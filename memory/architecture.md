# 架构：gamepad-agent

## 数据流
```
pygame 手柄事件 → mapper 查绑定（修饰层优先，回落默认层）→ injector SendInput 注入当前焦点窗口
```

## 文件职责
| 文件 | 职责 |
|---|---|
| `test_gamepad.py` | 独立测试脚本：打印手柄信息与实时事件 |
| `injector.py` | ctypes 调 user32.SendInput，零第三方依赖；支持单键/组合键/UNICODE 文本(含中文)/步骤序列 |
| `mapper.py` | 加载 config.json；Binding 数据类；双层查找；profile 循环切换 |
| `main.py` | 入口主循环：按钮/hat/摇杆(死区+滞回)/扳机(阈值+滞回)、连发、Start 切配置档 |
| `config.json` | 全部映射与全局参数 |

## config.json 绑定格式
```json
"RT": {"action": "sequence", "steps": [
  {"type": "text", "value": "y"},
  {"type": "wait", "ms": 50},
  {"type": "key", "keys": ["ENTER"]}
]}
```
- `action`: `"key"`（keys=组合键列表）或 `"sequence"`（steps 序列）
- `trigger`: press（默认）/ release / both
- `repeat: true` 按住连发（方向类），首次延迟 repeat_delay_ms，之后每 repeat_rate_ms
- 绑定名加前缀 `LT+A`/`LB+Y` 等构成修饰层；查找先精确匹配带前缀的，再回落默认层
- 键名不区分大小写：ENTER/ESC/TAB/LWIN/F1-F12/A-Z/0-9 等（见 injector.py VK_CODES）

## 默认按键表
A=Enter批准 | B=Esc取消 | X=Tab | Y=Shift+Tab | D-pad/左摇杆=方向键(连发) | RB=Win+H语音 | LB=Ctrl+C | RT=y+回车快速确认 | LT+A/B/X/Y=Ctrl+V/退格连发/Ctrl+Z/Ctrl+C | Start=切配置档

## 关键实现细节
- INPUT 结构体 union 以 MOUSEINPUT 尺寸对齐（64 位关键点）；press_vk 用 MapVirtualKeyW 补扫描码
- 中文文本用 KEYEVENTF_UNICODE 注入（wScan=ord(ch)）
- SDL_VIDEODRIVER=dummy 避免 pygame 弹窗；主循环 clock.tick(100) 低 CPU
- 摇杆死区进入阈值 deadzone，退出阈值 deadzone-hysteresis（滞回防抖）

## 验证结论（2026-08-23 实测）
- ✅ 手柄识别：Controller (8BitDo Ultimate 2C Wireless (WUKONG))，轴/按钮映射与代码一致
- ✅ 注入链路：记事本注入 "hello 你好"+Ctrl+A+Ctrl+C，剪贴板码点验证完全正确
- ⚠️ 管理员权限窗口收不到注入：目标程序提权时脚本也需管理员运行
- ⚠️ 控制台中文乱码：管道重定向下 GBK 显示问题，不影响功能；终端直跑正常或先 chcp 65001
- ⚠️ LSP 可能报 "Import pygame could not be resolved"：LSP 用了别的 Python 环境，实际 pip 已装 pygame 2.6.1，运行不受影响

## 排查实录（2026-08-23，全部已修复并实测通过）

### 坑 1：SDL 默认 HIDAPI 后端读不到此手柄
- 症状：SDL 枚举到设备（名字 `Controller (8BitDo ... (WUKONG))`）但收不到任何事件；joy.cpl 和直接调 XInput API 都正常
- 根因：SDL 2.28 默认用 HIDAPI 后端读手柄，打开 HID 设备句柄失败 → 枚举成功但无数据流
- 修复：pygame.init() 前强制 XInput 后端：
  ```python
  os.environ["SDL_JOYSTICK_HIDAPI"] = "0"
  os.environ["SDL_JOYSTICK_XINPUT"] = "1"
  os.environ["SDL_JOYSTICK_RAWINPUT"] = "0"
  os.environ["SDL_JOYSTICK_DINPUT"] = "0"
  ```
- 验证手段：直接 ctypes 调 XInputGetState 轮询按钮（test_deep.py），确认 XInput API 层正常

### 坑 2：SDL 2.28 XInput 后端轴布局与直觉不同
- 实际布局：**0/1=左摇杆、2=LT、3/4=右摇杆、5=RT**（不是 3=RT！）
- 症状：把 axis 3 当 RT 时，往右拨右摇杆反而触发 RT 功能
- 修复：main.py 里 `axis 5 → on_trigger("RT")`，axis 3/4（右摇杆）不处理

### 坑 3：SDL XInput 后端 hat 的 Y 方向反
- 症状：按物理"上"时 SDL 报 hat y=+1（标准约定 y=-1 才是上）
- 修复：main.py hat_to_dirs 里对调 UP/DOWN

### 坑 4：combo 注入需要保持延迟
- 症状：Alt+Tab 切换器一闪而过、只能切换相邻两个窗口
- 根因：combo 按下后立即松开（微秒级），Windows 来不及显示切换器
- 修复：combo(keys, hold_ms=30)，按下后保持 30ms 再松开

### 坑 5：LT 的 Alt 逻辑与修饰层冲突
- 需求：LT+Y = Alt+Tab 切换器（按住 LT 打开、按 Y 循环、松开确认）
- 冲突：若 LT 按住就自动按住 Alt，LT+B 的退格会变成 Alt+Backspace 行为异常（删整段）
- 修复：LT 按住时**不**自动按 Alt；改为**按 Y 时**才按住 Alt（打开切换器），松开 LT 时松开 Alt（确认）。LT 只做修饰层，LT+B 恢复正常

### 坑 6：按钮连发逻辑的边界 bug
- 症状：按住 LT+B 连发停不下来，删光所有内容
- 根因：松开 B 时若 LT 已松开，find_binding 回落默认层（无 repeat 标记），repeat_deadlines 没被清除
- 修复：松开时**无条件** pop repeat_deadlines（不依赖修饰层状态）
- 最终行为：点按 LT+B 逐个删除、长按连续删除（400ms 延迟后每 80ms 一次）

### 坑 7：.bat 启动脚本闪退（LF 换行 + 编码）
- 症状：双击启动手柄映射.bat，窗口一闪而过程序没启动
- 根因两个：
  1. Write 工具生成的文件是 **LF 换行**，cmd 解析 LF-only 的批处理会把一行拆成多条碎片命令直接崩溃
  2. UTF-8 编码含中文 + `chcp 65001` 中途切代码页会导致 cmd 解析指针错乱
- 修复：.bat 必须 **CRLF 换行 + GBK(ANSI) 编码 + 不用 chcp**：
  ```powershell
  $gbk = [System.Text.Encoding]::GetEncoding("GBK")
  $content = [IO.File]::ReadAllText($path, $gbk).Replace("`r`n","`n").Replace("`n","`r`n")
  [IO.File]::WriteAllText($path, $content, $gbk)
  ```
- 一键启动脚本：gamepad-agent\启动手柄映射.bat（双击即用）
