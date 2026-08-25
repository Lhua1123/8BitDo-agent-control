"""深度诊断：直接调 XInput API 读手柄状态（绕过 SDL），并打印 SDL 枚举设备的 GUID。"""

import ctypes
import os
import time
from ctypes import wintypes

# ---- 直接调 XInput API ----
class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", wintypes.WORD),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]

class XINPUT_STATE(ctypes.Structure):
    _fields_ = [("dwPacketNumber", wintypes.DWORD), ("Gamepad", XINPUT_GAMEPAD)]

BUTTON_NAMES = {
    0x0001: "DPAD_UP", 0x0002: "DPAD_DOWN", 0x0004: "DPAD_LEFT", 0x0008: "DPAD_RIGHT",
    0x0010: "START", 0x0020: "BACK", 0x0040: "L3", 0x0080: "R3",
    0x0100: "LB", 0x0200: "RB", 0x1000: "A", 0x2000: "B", 0x4000: "X", 0x8000: "Y",
}

def load_xinput():
    for dll in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
        try:
            return ctypes.WinDLL(dll)
        except OSError:
            continue
    return None

def main():
    # ---- 1. SDL 枚举信息 ----
    os.environ["SDL_JOYSTICK_HIDAPI"] = "0"
    os.environ["SDL_JOYSTICK_XINPUT"] = "1"
    import pygame
    pygame.init()
    pygame.joystick.init()
    print(f"SDL 枚举手柄数量: {pygame.joystick.get_count()}")
    for i in range(pygame.joystick.get_count()):
        js = pygame.joystick.Joystick(i)
        js.init()
        print(f"  [{i}] {js.get_name()} | GUID: {js.get_guid()} | 轴{js.get_numaxes()} 按钮{js.get_numbuttons()} hat{js.get_numhats()}")

    # ---- 2. 直接调 XInput API ----
    xinput = load_xinput()
    if xinput is None:
        print("无法加载 XInput DLL")
        return
    xinput.XInputGetState.argtypes = (wintypes.DWORD, ctypes.POINTER(XINPUT_STATE))
    xinput.XInputGetState.restype = wintypes.DWORD

    print("\nXInput 槽位扫描:")
    slots = []
    for i in range(4):
        st = XINPUT_STATE()
        r = xinput.XInputGetState(i, ctypes.byref(st))
        if r == 0:
            slots.append(i)
            print(f"  槽位 {i}: 设备存在 (ERROR_SUCCESS)")
        else:
            print(f"  槽位 {i}: 无设备 (错误码 {r})")

    if not slots:
        print("XInput 层没有检测到任何设备！")
        return

    print("\n开始轮询 XInput 状态（按手柄按键，Ctrl+C 退出）...")
    last_buttons = 0
    try:
        while True:
            for i in slots:
                st = XINPUT_STATE()
                r = xinput.XInputGetState(i, ctypes.byref(st))
                if r != 0:
                    continue
                b = st.Gamepad.wButtons
                if b != last_buttons:
                    pressed = [n for mask, n in BUTTON_NAMES.items() if b & mask]
                    released = [n for mask, n in BUTTON_NAMES.items() if last_buttons & mask and not (b & mask)]
                    if pressed:
                        print(f"[槽位{i}] 按下: {', '.join(pressed)}")
                    if released:
                        print(f"[槽位{i}] 释放: {', '.join(released)}")
                    last_buttons = b
                if st.Gamepad.bLeftTrigger > 30 or st.Gamepad.bRightTrigger > 30:
                    print(f"[槽位{i}] 扳机 LT={st.Gamepad.bLeftTrigger} RT={st.Gamepad.bRightTrigger}")
            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    print("\n已退出")

if __name__ == "__main__":
    main()