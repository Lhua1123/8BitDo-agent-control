"""键盘事件注入模块：纯 ctypes 调用 user32.SendInput，零第三方依赖。"""

import ctypes
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

# ---- 常量 ----
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
MAPVK_VK_TO_VSC = 0  # MapVirtualKeyW：虚拟键码 -> 扫描码

# 鼠标事件标志
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

# 指针大小的无符号整型（64 位下为 8 字节）
ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    # 比 KEYBDINPUT 大，union 的尺寸和对齐以它为准（64 位对齐关键点）
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]


user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
user32.SendInput.restype = wintypes.UINT
user32.MapVirtualKeyW.argtypes = (wintypes.UINT, wintypes.UINT)
user32.MapVirtualKeyW.restype = wintypes.UINT

# ---- VK 虚拟键码表 ----
VK_CODES = {
    "BACKSPACE": 0x08,
    "TAB": 0x09,
    "ENTER": 0x0D, "RETURN": 0x0D,
    "SHIFT": 0x10, "LSHIFT": 0xA0, "RSHIFT": 0xA1,
    "CTRL": 0x11, "CONTROL": 0x11, "LCTRL": 0xA2, "LCONTROL": 0xA2, "RCTRL": 0xA3, "RCONTROL": 0xA3,
    "ALT": 0x12, "LALT": 0xA4, "RALT": 0xA5,
    "ESCAPE": 0x1B, "ESC": 0x1B,
    "SPACE": 0x20,
    "LEFT": 0x25, "UP": 0x26, "RIGHT": 0x27, "DOWN": 0x28,
    "PAGEUP": 0x21, "PAGEDOWN": 0x22,
    "END": 0x23, "HOME": 0x24,
    "DELETE": 0x2E, "DEL": 0x2E,
    "LWIN": 0x5B, "RWIN": 0x5C,
}
for _i in range(1, 13):  # F1-F12
    VK_CODES[f"F{_i}"] = 0x70 + (_i - 1)
for _ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":  # 字母 VK == 大写 ASCII 码
    VK_CODES[_ch] = ord(_ch)
for _d in "0123456789":  # 数字 VK == ASCII 码
    VK_CODES[_d] = ord(_d)


def resolve_key(name):
    """键名 -> VK 码，不区分大小写，支持 ENTER/ESC/ESCAPE/TAB/Y/H 等写法。"""
    key = str(name).strip().upper()
    if key not in VK_CODES:
        raise ValueError(f"未知键名: {name}")
    return VK_CODES[key]


def _send_input(items):
    """批量发送 INPUT 数组，失败抛 RuntimeError 并带 GetLastError。"""
    arr = (INPUT * len(items))(*items)
    sent = user32.SendInput(len(arr), arr, ctypes.sizeof(INPUT))
    if sent != len(arr):
        raise RuntimeError(
            f"SendInput 失败：成功 {sent}/{len(arr)}，GetLastError={ctypes.get_last_error()}"
        )


def _mouse_event(flags, dx=0, dy=0, data=0):
    """发送单个鼠标事件（相对移动或按键）。"""
    item = INPUT()
    item.type = INPUT_MOUSE
    item.mi = MOUSEINPUT(dx=dx, dy=dy, mouseData=data, dwFlags=flags, time=0, dwExtraInfo=0)
    _send_input((item,))


def move_mouse(dx, dy):
    """相对移动鼠标 dx/dy 像素（可为负）。"""
    _mouse_event(MOUSEEVENTF_MOVE, dx=dx, dy=dy)


def mouse_down(button="left"):
    """按下鼠标键（left/right/middle），用于拖拽等按住场景。"""
    flags = {
        "left": MOUSEEVENTF_LEFTDOWN,
        "right": MOUSEEVENTF_RIGHTDOWN,
        "middle": MOUSEEVENTF_MIDDLEDOWN,
    }[button]
    _mouse_event(flags)


def mouse_up(button="left"):
    """松开鼠标键。"""
    flags = {
        "left": MOUSEEVENTF_LEFTUP,
        "right": MOUSEEVENTF_RIGHTUP,
        "middle": MOUSEEVENTF_MIDDLEUP,
    }[button]
    _mouse_event(flags)


def click_mouse(button="left", delay_ms=15):
    """点击鼠标键（按下-延迟-松开）。"""
    mouse_down(button)
    time.sleep(delay_ms / 1000)
    mouse_up(button)


def press_vk(vk, up=False):
    """发送单个虚拟键的按下/抬起事件；用 MapVirtualKey 补全扫描码提高兼容性。"""
    item = INPUT()
    item.type = INPUT_KEYBOARD
    item.ki = KEYBDINPUT(
        wVk=vk,
        wScan=user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC),
        dwFlags=KEYEVENTF_KEYUP if up else 0,
        time=0,
        dwExtraInfo=0,
    )
    _send_input((item,))


def tap_key(vk, delay_ms=15):
    """按下-延迟-抬起一个键。"""
    press_vk(vk)
    time.sleep(delay_ms / 1000)
    press_vk(vk, up=True)


def combo(keys, hold_ms=30):
    """组合键：顺序全部按下，保持 hold_ms 后逆序全部抬起，如 ["LWIN", "H"]。

    hold_ms 默认 30：让 Windows 有足够时间识别组合键（尤其 Alt+Tab 切换器
    需要 Tab 按下保持一段时间才会显示并循环，否则切换器一闪而过）。
    """
    vks = [resolve_key(k) for k in keys]
    for vk in vks:
        press_vk(vk)
    time.sleep(hold_ms / 1000)
    for vk in reversed(vks):
        press_vk(vk, up=True)


def type_text(text):
    """KEYEVENTF_UNICODE 注入任意文本（含中文），每字符 down+up；'\\n' 转回车。"""
    for ch in text:
        if ch == "\n":
            tap_key(VK_CODES["ENTER"])
            continue
        down = INPUT()
        down.type = INPUT_KEYBOARD
        down.ki = KEYBDINPUT(wVk=0, wScan=ord(ch), dwFlags=KEYEVENTF_UNICODE,
                             time=0, dwExtraInfo=0)
        up = INPUT()
        up.type = INPUT_KEYBOARD
        up.ki = KEYBDINPUT(wVk=0, wScan=ord(ch),
                           dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
                           time=0, dwExtraInfo=0)
        _send_input((down, up))


def execute_steps(steps):
    """执行序列步骤：
    {"type": "text", "value": "..."} 注入文本；
    {"type": "wait", "ms": 50} 等待；
    {"type": "key", "keys": ["ENTER"]} 组合键。
    """
    for step in steps:
        kind = step.get("type")
        if kind == "text":
            type_text(step["value"])
        elif kind == "wait":
            time.sleep(step.get("ms", 0) / 1000)
        elif kind == "key":
            combo(step["keys"])
        else:
            raise ValueError(f"未知步骤类型: {kind}")


if __name__ == "__main__":
    # 自测：向当前焦点窗口注入文本和组合键，供自动化验证剪贴板内容
    print("3 秒后向当前焦点窗口注入测试内容，请把光标放到任意可输入位置...")
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    type_text("hello 你好")
    time.sleep(0.3)
    combo(["LCTRL", "A"])  # 全选
    time.sleep(0.3)
    combo(["LCTRL", "C"])  # 复制到剪贴板
    print("完成：已注入 'hello 你好' 并复制到剪贴板，粘贴即可验证。")
