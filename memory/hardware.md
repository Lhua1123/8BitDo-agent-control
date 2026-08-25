# 硬件：8BitDo 黑神话悟空联名手柄

## 型号本质
- 用户手柄：8BitDo 黑神话悟空联名版，model **81HD**
- 本质 = **Ultimate 2C（猎户座2青春版）** 换壳联名款
- 青春版不支持官方 Ultimate Software 改键（本项目工具即替代品）

## Windows 连接方式（重要限制）
| 方式 | 支持 | 说明 |
|---|---|---|
| USB 有线 | ✅ | 即插即用 |
| 2.4G 接收器 | ✅ | 即插即用，推荐 |
| 蓝牙 | ❌ | **仅限 Android，不能连 Windows** |

- Windows 下默认 **XInput 协议** = 标准 Xbox 手柄，pygame/SDL 零配置直读
- 模式切换（一般不用动）：关机状态按 `X+Home` 或 `B+Home` 切 XInput/DInput，模式会被保存

## pygame/SDL 识别信息（实测）
- XInput 模式设备名：`Controller (8BitDo Ultimate 2C Wireless (WUKONG))`
- **6 轴（SDL 2.28 XInput 后端实际布局）**：0/1=左摇杆，**2=LT**，**3/4=右摇杆**，**5=RT**
  - ⚠️ 注意：不是直觉的 3=RT！RT 在 axis 5（详见 architecture.md 坑 2）
- **11 按钮**：0=A, 1=B, 2=X, 3=Y, 4=LB, 5=RB, 6=BACK, 7=START, 8=GUIDE, 9=L3, 10=R3
- **1 hat**：十字键（⚠️ SDL 报的 Y 方向与物理相反，代码已对调，见 architecture.md 坑 3）
- 无背键（back paddle），无内置麦克风
- ⚠️ SDL 默认 HIDAPI 后端读不到此手柄（枚举成功但无事件），必须强制 XInput 后端（见 architecture.md 坑 1）

## ⚠️ 大坑：手柄会自动回连蓝牙导致 DInput 错乱模式（2026-08-23 排查实录）
症状：显示"已连接"但按键全无反应；SDL 枚举为 `8BitDo Ultimate 2C Wireless Controller`（15 按钮 DInput）；按某些键触发系统热键（如按 Y 触发窗口 QUIT）。

根因链：
1. 手柄曾与电脑蓝牙配对过 → 开机时**优先自动回连蓝牙**，即使 2.4G 接收器插着也绕过它
2. 蓝牙通道**没有 XInput 模式**（官方设计蓝牙仅给 Android）→ 只能以通用 HID DInput 15 键布局工作
3. XInput/DInput 是手柄自身的模式状态，**独立于连接通道**——走了接收器也可能仍是 DInput

诊断手段：
- `Get-PnpDevice -PresentOnly`：Parent 为 `BTH\MS_BTHLE` = 走蓝牙；USB 列表查 `VID_2DC8`（8BitDo 厂商ID）= 接收器节点（PID_301C）
- SDL 枚举按钮数：11=XInput ✅ / 15=DInput ❌
- 对照实验：拔掉接收器看手柄是否仍在线 → 在线即证明走的是蓝牙

解决步骤（实测有效）：
1. Windows 设置→蓝牙→删除 `8BitDo Ultimate 2C Wireless` 配对记录（掐断蓝牙通道）
2. 手柄开机状态按住 **View(选择键)+X 约 5 秒**切回 XInput（指示灯快闪=成功）；备选：关机状态按住 X+Home 开机
3. 重开手柄自动连接收器 → SDL 枚举应显示 WUKONG 名字 + 11 按钮
