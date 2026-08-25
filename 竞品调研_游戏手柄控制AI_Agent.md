# 游戏手柄控制 AI Agent — 开源竞品调研

> 调研日期：2026-08-23
> 调研目的：寻找"利用游戏手柄麦克风 + 按键，作为 AI Agent（Codex / Hermes / Claude Code）操作路径"的开源程序，实现语音输入、操作批准/取消等功能，为自研程序提供参考。

---

## 一、需求概述

- **硬件输入**：游戏手柄（Xbox / PS5 / 通用 360 手柄）的按键 + 麦克风语音
- **目标软件**：Codex、Hermes、Claude Code 等 AI Agent / CLI 工具
- **核心功能**：
  - 语音输入（读入手柄麦克风 → 语音识别 → 文本输入到 Agent）
  - 操作批准（AI 请求确认时，手柄一键批准/取消）
  - 按键映射（手柄按键 → 快捷键/命令）
  - 会话管理（多个 Agent 会话切换）

---

## 二、竞品全景（按参考价值分档）

### A档：专为 AI Agent 设计（参考价值最高）

#### 1. Helm（PetePeter/gamepad-cli-hub）— 最全面的多 Agent 控制台

- **仓库**：https://github.com/PetePeter/gamepad-cli-hub
- **定位**：Electron 桌面应用，用游戏手柄控制多个 AI CLI 会话
- **支持的 Agent**：Claude Code、Copilot CLI、Codex CLI、Hermes（任何 CLI）
- **平台**：Windows（.exe）、macOS（.dmg 通用包）
- **技术栈**：Electron + node-pty + xterm.js
- **特色功能**：
  - 嵌入式终端（每个 CLI 独立标签页，无外部窗口）
  - D-pad / 左摇杆切换会话，自动聚焦终端
  - 右摇杆滚动终端缓冲
  - 左扳机 = 启动 Claude Code，右肩键 = 启动 Copilot CLI（默认）
  - A/B/X/Y 键可自定义绑定
  - **Telegram 远程控制**（手机监控 + /spawn /send 命令）
  - **OpenWhisper 语音输入**（voice-to-text）
  - 计划系统（planning/ready/coding/review/blocked/done 状态）
  - 定时任务、模式匹配器（PTY 输出匹配正则自动触发）
  - Helm MCP 服务器（供其他 AI 控制）
- **配置方式**：npm install && npm start，Settings 配置 CLI 工具路径和按键绑定
- **参考价值**：多会话管理 + 嵌入式终端 + 远程控制架构

#### 2. agentpad（pameziane-hub）— 正中"批准"需求！

- **仓库**：https://github.com/pameziane-hub/agentpad
- **定位**：**用手柄回答 AI 的权限提示**——AI 编码时等你确认，手柄一键批准/取消
- **支持的 Agent**：Claude Code、Codex CLI、Gemini CLI（任何终端程序）
- **平台**：macOS 13+（Xbox 手柄蓝牙，DS4/DualSense 也可）
- **技术栈**：Swift + Apple GameController 框架，合成鼠标/键盘事件
- **核心按键映射**（非常有参考价值）：
  | 按键 | 动作 |
  |---|---|
  | A | 左键点击（批准） |
  | B | Esc（取消） |
  | X | Tab |
  | Y | Shift+Tab（切换 Claude Code 权限模式） |
  | RT | Return（发送提示） |
  | LT | 点击=右击；**按住=快捷层** |
  | D-pad | 方向键（导航选项） |
  | RB | **语音听写** |
  | LB | Cmd+`（切换窗口） |
  | L3/R3 | Cmd+C / Cmd+V |
  | 菜单键 | 应用菜单 |
- **快捷层（按住 LT）**：Steam-Input 风格
  - LT+A = 切到上个应用、LT+B = 删除、LT+X = 撤销、LT+Y = Ctrl+C 中断
  - LT+D-pad↓ = 输入 `/`（打开 Claude Code 命令菜单）
- **安装**：一键脚本 `curl -fsSL ...install.sh | bash`，需授予辅助功能权限
- **参考价值**：**权限批准流程设计**（A 批准 / B 取消 / Y 切换模式）——正是"允许批准"功能

#### 3. ai-operator-controller（ryumindmitrii-cmd）— Windows 原生！

- **仓库**：https://github.com/ryumindmitrii-cmd/ai-operator-controller
- **定位**：本地优先的语音 + 游戏手柄控制 AI 工作区（Windows-first）
- **支持的 Agent**：Codex Desktop（目标 MVP）、ChatGPT 浏览器 / Cursor 后续
- **技术栈**：Python + faster-whisper（本地语音识别）
- **Topics**：accessibility / codex / dictation / faster-whisper / gamepad / voice-control / windows / xbox-controller
- **核心功能**：
  - **Push-to-talk 听写**：F9 听写并粘贴到当前窗口；F8 仅听写到剪贴板
  - 本地语音识别（faster-whisper，默认 large-v3 模型）
  - **Xbox 手柄控制**：
    - A = 聚焦输入框+听写+粘贴
    - X = 当前光标处听写+粘贴
    - Y = Ctrl+Alt+B 切换 Codex 侧边栏
    - B = 退格（按住重复）
    - LB/RB = 左/右鼠标点击
    - LT/RT = 空格/回车
    - 左摇杆 = 切换上/下一个聊天
    - D-pad = 移动文本光标
    - 右摇杆 = 滚动/移动鼠标
    - 菜单键 = Ctrl+J 切换底部面板
  - **语音文本清理**：替换词典、填充词过滤（去掉"嗯""啊"）、语音命令（"换行"/"发送"）
  - **听写质量门槛**：低置信度 / 长文本 / 文本改动过大时**阻止自动回车**，避免误发
  - 私有学习管线（收集热词/替换/标点候选，不存原始聊天到 git）
- **状态**：早期公开开发者预览
- **参考价值**：**Windows 实现 + faster-whisper 本地语音 + 防误发质量门槛**

#### 4. ClaudeGamepad（cch123，28⭐）+ ClaudeGamepad-Win（Go 重写版）

- **仓库**：
  - https://github.com/cch123/ClaudeGamepad（macOS 原版）
  - https://github.com/Shio0909/ClaudeGamepad-Win（Windows Go 重写版，带语音输入）
- **定位**：用游戏手柄"玩"Claude Code，躺在沙发上编程（vibe coding）
- **平台**：macOS 原生（Swift）；Windows 版为 Go 重写
- **支持控制器**：Xbox、PS5 DualSense、任意 MFi 兼容
- **语音输入**：Apple Speech Recognition 或本地 whisper.cpp，**可选 LLM 自动修正听写文本（Ollama / OpenAI 兼容）**
- **特色功能**：
  - 菜单栏应用（后台运行，无 Dock 图标）
  - 全部按键可通过 GUI 配置
  - **快速预设提示**：LT/RT + 面键发送预设 prompt
  - **命令连招**：按住 LT+RT 进入命令模式，格斗游戏风格输入序列
  - **预设菜单**：Start 键打开 D-pad 可导航的提示列表
  - **悬浮 HUD**：显示按键反馈、连招、听写文本
  - 组合键前缀冲突检测（设置界面警告）
- **参考价值**：**LLM 修正听写文本**、LT/RT 修饰键组合、悬浮 HUD 反馈

#### 5. VibePad（ignatovv，67⭐）— 设计最精致

- **仓库**：https://github.com/ignatovv/VibePad
- **定位**：macOS 菜单栏应用，手柄变成完整编码控制器（"躺在沙发上写代码"）
- **支持的 Agent**：Claude Code、Codex CLI 优化的映射
- **平台**：macOS 14+（Swift + AppKit + GameController + CGEvent）
- **核心设计**：
  - **双层映射**：默认层 + L1 按住修饰层 = 按键数翻倍
  - **智能粘贴**：剪贴板含图片 → Ctrl+V，纯文本 → Cmd+V
  - 左摇杆 = 方向键（滞回阈值 + 按住重复）
  - 右摇杆 = 连续平滑滚动
  - L1+摇杆 = 切换应用 & 鼠标控制
  - L3/R3 = 左右键点击
  - **触发模式**：按下触发 / 松开触发 / 两者都触发（如按住说话 hold-to-talk）
  - **HUD 覆盖层**：每个按键按下时显示动作标签
  - JSON 全配置（`~/.vibepad/config.json`）
  - 按动作类型：`keystroke` / `typeText` / `smartPaste` / `leftMouseClick` / `rightMouseClick`
- **布局灵感**：reWASD / Steam Input 风格；灵感来源 enjoy2
- **参考价值**：**双层映射架构**、智能粘贴、触发模式设计

#### 6. 其他 AI 相关

- **sina2077/Gamepad-AI-assistant**（无描述，待考察）
- **RisAbd/virtual-gamepad-python-tk**：Python+vgamepad 虚拟手柄+ChatGPT

---

### B档：通用手柄 → 键鼠映射（底层基础，可直接借鉴）

| 项目 | ⭐ | 平台 | 特点 |
|---|---|---|---|
| **AntiMicroX** | 3926 | Win/Linux | 图形化映射到键盘/鼠标/**宏/脚本**，最经典，跨 X.org/Wayland |
| **AntiMicro**（旧版） | 1834 | Win/Linux | AntiMicroX 前身，已停止维护 |
| **xbox-controller-mapper**（NSEvent） | 93 | 跨平台 | 支持 300+ 控制器，映射+宏+脚本 |
| **gyromouse**（Yamakaky） | 36 | 跨平台 | 陀螺仪鼠标 + 按键映射 |
| **JoyMapper**（compnski） | - | Python | 摇杆→键鼠绑定，代码轻量易读 |
| **joystick-to-keyboard**（Egemen28） | - | Python | 手柄输入转键盘输出 |
| **remapper**（rennerdo30） | - | Rust | 跨平台输入重映射（键盘/鼠标/手柄→虚拟设备） |
| **GamepadKey**（mikahama） | 1 | Linux Wayland | 手柄→键鼠 |
| **joypad-for-debian**（velvet-os） | 1 | Linux | 掌机手柄映射 |
| **InputConfig**（ryleighnewman） | - | macOS | 手柄→键鼠映射 |

---

### C档：Windows 手柄 + 语音（可直接复用思路）

#### Joy_Flow（richarddong124-boop）

- **仓库**：https://github.com/richarddong124-boop/Joy_Flow
- **定位**：**Windows 无障碍/生产力应用**，手柄变成鼠标导航 + 语音听写
- **平台**：Windows 10/11，Python 3.12，**PyInstaller 打包 exe**
- **特色功能**：
  - 手柄驱动光标移动和点击
  - **Hold-to-talk Whisper 语音听写**（openai-whisper，默认 small 模型，可换）
  - 可配置映射和行为
  - **中英文双语界面**、深浅主题
  - 屏幕覆盖层（显示控制器状态）
  - 系统托盘 + 单实例保护
  - 本地持久化配置
- **技术栈**：Python + whisper + PyInstaller（含 Torch 打包 hook）
- **参考价值**：**Windows 上 Python 全流程实现范例**（含打包方案）

#### 其他语音类

- **Clohman11/VoiceToController**：语音命令 → 手柄输入
- **themanyone/whisper_dictation**：Whisper 本地语音键盘/听写工具
- **danielrosehill/Awesome-Whisper-Apps**：Whisper 应用集合（有用工具列表）

---

### D档：可参考的底层库（自研时直接用）

| 库 | 用途 | 平台 |
|---|---|---|
| **vgamepad** | Python 虚拟手柄（模拟 Xbox360/DS4） | Windows |
| **pynput** | 全局键盘/鼠标事件监听与模拟 | 跨平台 |
| **faster-whisper** | 本地语音识别（CPU 可跑，CTranslate2 加速） | 跨平台 |
| **openai-whisper** | Whisper 原版（需 torch） | 跨平台 |
| **Interception** | Windows 输入驱动层注入 | Windows |
| **node-pty** | 嵌入式终端（PTY） | Windows/macOS/Linux |
| **GameController** | Apple 原生手柄框架 | macOS |
| **SDL2 / SDL_GameControllerDB** | 跨平台手柄输入 + 控制器数据库 | 跨平台 |

---

## 三、自研方案建议（基于竞品分析）

### 推荐参考组合

1. **交互设计** ← agentpad（批准/取消流程）+ VibePad（双层映射、hold-to-talk）
2. **Windows 实现** ← Joy_Flow（Python 全流程 + PyInstaller 打包）或 ai-operator-controller（faster-whisper 本地语音）
3. **多 Agent 支持** ← Helm（嵌入式终端管理多个 CLI）
4. **语音质量** ← ai-operator-controller 的置信度门槛（防误发）+ ClaudeGamepad 的 LLM 文本修正

### 最小可行架构（建议）

```
┌─────────────────────────────────────────┐
│  手柄输入层（pynput / SDL2 / vgamepad）  │
│  ↓ 按键/摇杆事件                         │
│  映射引擎（JSON 配置映射表 + 修饰层）     │
│  ↓ 键盘/鼠标模拟                          │
│  Agent 会话层（Hermes / Codex CLI）      │
│  ↑                                        │
│  语音管线（faster-whisper 本地 STT）      │
│  → 文本清理 → 质量门槛 → 注入输入框/终端  │
└─────────────────────────────────────────┘
```

### 核心模块

1. **手柄事件采集**：读取按键/摇杆/扳机（含阈值、滞回、按住重复）
2. **映射引擎**：JSON 映射配置、默认层+修饰层、组合键、触发模式（按下/松开/双向）
3. **键鼠注入**：pynput / Interception 合成键盘鼠标事件
4. **语音管线**：手柄麦克风 → push-to-talk 录音 → faster-whisper → 文本清理（填充词/替换词典）→ 质量门槛 → 粘贴发送
5. **Agent 批准流程**：A=批准 / B=取消 / Y=切换权限模式 / RT=发送
6. **HUD 反馈**：悬浮层显示按键动作和语音转写结果

### 注意事项（踩坑点）

- Windows 上模拟键鼠需要**辅助功能/无障碍权限**
- 手柄麦克风通常走 3.5mm 耳机接口或手柄内置（如 PS5 DualSense 内置麦克风），需确认输入设备捕获方式
- 语音识别置信度低时禁止自动回车（防误发）
- hold-to-talk 用"松开触发"而不是"按下触发"，避免长文本被截断

---

## 四、信息源清单

| 项目 | GitHub 链接 |
|---|---|
| Helm | https://github.com/PetePeter/gamepad-cli-hub |
| agentpad | https://github.com/pameziane-hub/agentpad |
| ai-operator-controller | https://github.com/ryumindmitrii-cmd/ai-operator-controller |
| ClaudeGamepad | https://github.com/cch123/ClaudeGamepad |
| ClaudeGamepad-Win | https://github.com/Shio0909/ClaudeGamepad-Win |
| VibePad | https://github.com/ignatovv/VibePad |
| Joy_Flow | https://github.com/richarddong124-boop/Joy_Flow |
| AntiMicroX | https://github.com/AntiMicroX/antimicrox |
| xbox-controller-mapper | https://github.com/NSEvent/xbox-controller-mapper |
| gyromouse | https://github.com/Yamakaky/gyromouse |
| JoyMapper | https://github.com/compnski/JoyMapper |
| remapper | https://github.com/rennerdo30/remapper |
| AntiMicro（旧版，已停维护） | https://github.com/AntiMicro/antimicro |
| joystick-to-keyboard | https://github.com/Egemen28/joystick-to-keyboard |
| GamepadKey（Linux Wayland） | https://github.com/mikahama/GamepadKey |
| joypad-for-debian | https://github.com/velvet-os/joypad-for-debian |
| InputConfig（macOS） | https://github.com/ryleighnewman/InputConfig |
| Gamepad-AI-assistant（待考察） | https://github.com/sina2077/Gamepad-AI-assistant |
| VoiceToController（语音→手柄输入） | https://github.com/Clohman11/VoiceToController |
| whisper_dictation（本地语音听写） | https://github.com/themanyone/whisper_dictation |
| Awesome-Whisper-Apps（Whisper 应用合集） | https://github.com/danielrosehill/Awesome-Whisper-Apps |

---
*本文档由小草丛 2026-08-23 调研整理*