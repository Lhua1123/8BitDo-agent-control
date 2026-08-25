# 游戏手柄 → 键盘映射工具（Windows）

把 8BitDo 黑神话悟空联名手柄（Ultimate 2C 底子，model 81HD）的按键合成为键盘事件，
发送给当前焦点窗口。主要用于操作 AI Agent CLI（opencode / claude code / codex）的
批准、取消、上下导航，以及一键唤起微信输入法语音输入。

## 功能特性

- 手柄按键 → 单键 / 组合键 / 文本序列注入（支持中文文本）
- LT/LB/RT/RB 修饰层：同一按键在不同修饰层下映射不同输出（如 LT+A → Ctrl+V）
- 十字键与左摇杆均可映射方向键，支持按住连发（死区 + 滞回防抖）
- 多配置档管理，Start 键循环切换
- 基于 Windows SendInput，兼容绝大多数接收键盘输入的程序

## 环境要求与安装

- Windows 10/11，Python 3.12
- 安装依赖（仅 pygame 一个第三方库）：

```
pip install pygame
```

## 手柄连接方法

- **2.4G 接收器**插 USB 口，或 **USB 线直连**，即插即用，系统识别为标准 Xbox（XInput）手柄。
- ⚠️ 警告：此手柄的**蓝牙模式仅支持 Android 设备，不能连接 Windows**，请勿尝试蓝牙配对。

## 运行

```
# 一键启动（推荐）：双击即可
启动手柄映射.bat

# 或手动运行：
# 第一步：测试手柄连接与按键编号
python test_gamepad.py

# 第二步：启动映射（保持目标窗口在前台焦点）
python main.py
```

## 默认按键表（default 配置档）

| 手柄按键        | 键盘输出         | 说明                       |
| --------------- | ---------------- | -------------------------- |
| A               | Enter            | 批准 / 确认                |
| B               | Esc              | 取消                       |
| X               | Tab              |                            |
| Y               | Shift+Tab        | 反向导航                   |
| 十字键 / 左摇杆 | 上/下/左/右方向键| 按住连发                   |
| RB              | V → 4（序列）    | 微信输入法语音条           |
| LB              | Ctrl+C           |                            |
| RT              | 输入 `y` 后回车  | 序列动作，快速确认         |
| LT+A            | Ctrl+V           | 按住 LT 再按 A             |
| LT+B            | Backspace        | 点按逐个删除、长按连发     |
| LT+X            | Ctrl+Z           |                            |
| LT+Y            | Tab              | Alt+Tab 切换器内循环       |
| Start           | 切换配置档       | 只有一个配置档时会提示     |

## Alt+Tab 切换器（LT）

1. **按住 LT**：进入修饰层（此时**不**按 Alt，LT+A/B/X 正常使用）
2. **按住 LT 期间按 Y**：打开任务切换器并循环（等同按住 Alt + 按 Tab）
3. **松开 LT**：确认切换（等同松开 Alt）

> 设计说明：LT 只在按 Y 时才临时按住 Alt，因此 LT+A/B/X 的修饰层功能不受影响
> （LT+B 退格不会变成 Alt+Backspace）。

## 自定义映射（config.json）

每个绑定支持以下字段：

- `action`：`"key"`（组合键）或 `"sequence"`（步骤序列）
- `keys`：组合键名列表，如 `["LCTRL", "C"]`；键名不区分大小写，
  支持 ENTER / ESC / ESCAPE / TAB / BACKSPACE / DELETE / UP / DOWN / LEFT / RIGHT /
  HOME / END / PAGEUP / PAGEDOWN / LWIN / SPACE / F1-F12 / A-Z / 0-9 等
- `steps`：序列步骤列表，三种类型：
  - `{"type": "text", "value": "任意文本"}` 注入文本（支持中文）
  - `{"type": "wait", "ms": 50}` 等待毫秒
  - `{"type": "key", "keys": ["ENTER"]}` 发送组合键
- `trigger`：触发时机，`"press"`（默认）/ `"release"` / `"both"`
- `repeat`：`true` 时按住连发（方向键和按钮都支持，如 LT+B 长按连续删除），
  首次延迟 `repeat_delay_ms`，之后每 `repeat_rate_ms` 重发一次
- **修饰层前缀**：绑定名写成 `LT+A`、`LB+Y`、`RT+B`、`RB+X` 形式时，
  只有按住对应修饰键才生效；查找顺序为先匹配修饰层、再回落默认层同名绑定。
  全局参数：`deadzone`（摇杆死区）、`hysteresis`（滞回量）、`trigger_threshold`（扳机阈值）。

## 微信输入法语音输入使用方法

1. 把光标焦点放在目标窗口的输入框；
2. 按 **RB**，工具自动发送 `V` 再发送 `4`（微信输入法 V 模式 → 语音输入）；
3. 直接说话，识别文字自动输入到焦点窗口；
4. 再次按 RB 或点关闭可结束语音输入。

> 若你的微信输入法语音快捷键不是 V+4，改 `config.json` 里 RB 的 `steps` 即可。

## 常见问题

- **未检测到手柄**：确认 2.4G 接收器已插入或 USB 线已连接；蓝牙模式无法在 Windows 使用。
- **手柄显示已连接但按键没反应**：多半是手柄走了蓝牙通道（DInput 15 键模式）。删除 Windows
  蓝牙配对记录，手柄开机状态按 **View+X 长按 5 秒**切回 XInput 模式（详见 memory/hardware.md）。
- **管理员权限窗口收不到注入**：目标程序以管理员运行时，脚本也需以管理员身份运行。
- **按键没反应**：焦点必须在目标窗口上，注入事件只发给当前前台焦点窗口。
- **想验证注入功能是否正常**：直接运行 `python injector.py`，它会向焦点窗口注入
  `hello 你好` 并复制到剪贴板，粘贴即可检查。
- **技术说明（SDL 后端）**：main.py 强制 SDL 使用 XInput 后端读取手柄
  （`SDL_JOYSTICK_HIDAPI=0` 等 4 个环境变量），因为此手柄在 SDL 默认的 HIDAPI 后端下
  枚举成功但读不到数据。若以后换手柄遇到类似问题，可先跑 `python test_poll.py` 验证。
