"""Windows 游戏手柄 → 键盘映射工具入口：读取手柄事件，按 config.json 注入键盘事件。"""

import os
import sys
import time

import pygame

from injector import VK_CODES, click_mouse, combo, execute_steps, move_mouse, press_vk
from mapper import Mapper

# 无头模式，避免 pygame 弹出窗口
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

# 强制 SDL 使用 XInput 后端读取手柄。
# 原因：此手柄（8BitDo Ultimate 2C）在 SDL 默认的 HIDAPI 后端下枚举成功但读不到数据
# （打开 HID 设备句柄失败），强制 XInput 后端后按钮/轴/十字键全部正常。
os.environ["SDL_JOYSTICK_HIDAPI"] = "0"
os.environ["SDL_JOYSTICK_XINPUT"] = "1"
os.environ["SDL_JOYSTICK_RAWINPUT"] = "0"
os.environ["SDL_JOYSTICK_DINPUT"] = "0"

# Xbox 标准布局按钮索引 → 事件名
# 注意：SDL 2.28 XInput 后端实际布局为 8=L3、9=R3、10=GUIDE（不是 8=GUIDE、9=L3、10=R3）
BUTTON_NAMES = {
    0: "A", 1: "B", 2: "X", 3: "Y",
    4: "LB", 5: "RB",
    6: "BACK", 7: "START",
    8: "L3", 9: "R3", 10: "GUIDE",
}
MODIFIERS = {"LT", "LB", "RT", "RB", "L3"}  # 可作修饰层的按键


def hat_to_dirs(hat):
    """hat 值 ((-1..1), (-1..1)) 转方向名集合，斜方向拆成两个。

    注意：此手柄（8BitDo Ultimate 2C）在 XInput 模式下 SDL 报告的 hat Y 方向
    与物理方向相反（按物理"上"时 SDL 报 y=+1），因此这里对调 UP/DOWN。
    """
    x, y = hat
    dirs = set()
    if y == -1:
        dirs.add("DOWN")
    if y == 1:
        dirs.add("UP")
    if x == -1:
        dirs.add("LEFT")
    if x == 1:
        dirs.add("RIGHT")
    return dirs


class GamepadApp:
    """持有运行状态，把手柄事件翻译成键盘注入。"""

    def __init__(self, stick, mapper):
        self.stick = stick
        self.mapper = mapper
        self.active_modifiers = set()   # 当前激活的修饰层 LT/LB/RT/RB
        self.hat_dirs = set()           # 十字键当前方向
        self.stick_dirs = set()         # 左摇杆当前虚拟方向
        self.move_state = [0, 0]        # 左摇杆 x/y 轴状态：-1 / 0 / 1
        self.lt_on = False              # 扳机按下状态（带滞回）
        self.rt_on = False
        self.repeat_deadlines = {}      # 方向名 -> 下次连发时间戳
        self.mouse_stick = [0.0, 0.0]   # 右摇杆 x/y 轴值（axis 3/4），用于鼠标移动

    # ---- 绑定执行 ----

    def dispatch(self, name, pressed):
        """查绑定并执行，返回命中的 Binding（未命中返回 None）。"""
        b = self.mapper.find_binding(name, self.active_modifiers)
        if b is None:
            return None
        if b.trigger == "press" and not pressed:
            return b
        if b.trigger == "release" and pressed:
            return b
        if b.action == "key":
            combo(b.keys)
        elif b.action == "sequence":
            execute_steps(b.steps)
        elif b.action == "mouse":
            click_mouse(b.button)
        return b

    def handle_button(self, name, pressed):
        """按钮按下/释放统一入口：维护修饰层、处理 Start 切换配置档、支持按住连发。"""
        if name in MODIFIERS:
            if pressed:
                self.active_modifiers.add(name)
            else:
                self.active_modifiers.discard(name)
        # LT 松开时松开 Alt（确认 Alt+Tab 切换）；LT 按住期间按 Y 时按住 Alt（打开切换器）。
        # 注意：LT 按住时不再自动按住 Alt，否则 LT+B 的退格会变成 Alt+Backspace 行为异常。
        if name == "LT" and not pressed:
            press_vk(VK_CODES["LALT"], up=True)
        if name == "Y" and pressed and "LT" in self.active_modifiers:
            press_vk(VK_CODES["LALT"])
        # Start 键特殊处理：当前配置档没有显式绑定 START 时用于切换配置档
        if name == "START" and pressed and self.mapper.find_binding("START", ()) is None:
            new_name = self.mapper.switch_profile()
            print(f"已切换到配置档：{new_name}" if new_name else "只有一个配置档，无法切换")
            return
        b = self.dispatch(name, pressed)
        # 按住连发：按下且 binding 标记 repeat 时启动连发；松开时无条件停止
        # （防止修饰层状态变化导致 find_binding 回落默认层、连发计时没被清除而停不下来）
        if b is not None and b.repeat and pressed:
            self.repeat_deadlines[name] = time.monotonic() + self.mapper.repeat_delay_ms / 1000
        elif not pressed:
            self.repeat_deadlines.pop(name, None)

    # ---- 方向类（十字键 + 左摇杆共用）----

    def update_dir_source(self, store, new_dirs):
        """更新一个方向来源，对增减的方向分别触发按下/释放，并维护连发计时。"""
        old = self.hat_dirs | self.stick_dirs
        store.clear()
        store |= new_dirs
        new = self.hat_dirs | self.stick_dirs
        for d in new - old:  # 新按下的方向
            b = self.dispatch(d, True)
            if b is not None and b.repeat:
                self.repeat_deadlines[d] = time.monotonic() + self.mapper.repeat_delay_ms / 1000
        for d in old - new:  # 释放的方向
            self.repeat_deadlines.pop(d, None)
            self.dispatch(d, False)

    def fire_repeats(self):
        """对按住的方向按 repeat_rate_ms 周期重发。"""
        now = time.monotonic()
        due = [d for d, t in self.repeat_deadlines.items() if now >= t]
        for d in due:
            self.dispatch(d, True)
            self.repeat_deadlines[d] = now + self.mapper.repeat_rate_ms / 1000

    # ---- 摇杆与扳机 ----

    def on_move_axis(self, axis, value):
        """左摇杆轴 0/1：死区进入、死区-滞回退出，转虚拟方向事件。"""
        st = self.move_state[axis]
        dz = self.mapper.deadzone
        low = dz - self.mapper.hysteresis
        if st == 0:
            if value > dz:
                st = 1
            elif value < -dz:
                st = -1
        elif st == 1 and value < low:
            st = 0
        elif st == -1 and value > -low:
            st = 0
        self.move_state[axis] = st

        x, y = self.move_state
        dirs = set()
        if y < 0:
            dirs.add("UP")
        if y > 0:
            dirs.add("DOWN")
        if x < 0:
            dirs.add("LEFT")
        if x > 0:
            dirs.add("RIGHT")
        self.update_dir_source(self.stick_dirs, dirs)

    def on_trigger(self, name, value):
        """扳机轴 LT(axis2)/RT(axis3)：超过阈值视为按下，低于阈值-滞回视为释放。"""
        on = self.lt_on if name == "LT" else self.rt_on
        th = self.mapper.trigger_threshold
        hys = self.mapper.hysteresis
        if not on and value > th:
            on = True
            self.handle_button(name, True)   # handle_button 内部会加入修饰层集合
        elif on and value < th - hys:
            on = False
            self.handle_button(name, False)
        if name == "LT":
            self.lt_on = on
        else:
            self.rt_on = on

    # ---- 右摇杆 → 鼠标 ----

    def on_mouse_axis(self, axis, value):
        """右摇杆轴 3/4：记录当前偏移，供每帧移动鼠标。"""
        self.mouse_stick[axis - 3] = value

    def move_mouse_by_stick(self):
        """根据右摇杆偏移移动鼠标：死区 + 线性速度映射（每帧调用）。"""
        x, y = self.mouse_stick
        dz = self.mapper.mouse_deadzone
        speed = self.mapper.mouse_speed
        dx = dy = 0
        if abs(x) > dz:
            dx = int((x - dz * (1 if x > 0 else -1)) * speed)
        if abs(y) > dz:
            dy = int((y - dz * (1 if y > 0 else -1)) * speed)
        if dx or dy:
            move_mouse(dx, dy)

    # ---- 主循环 ----

    def run(self):
        clock = pygame.time.Clock()
        my_id = self.stick.get_id()
        try:
            while True:
                for e in pygame.event.get():
                    if getattr(e, "joy", my_id) != my_id:  # 只处理本手柄的事件
                        continue
                    if e.type == pygame.JOYBUTTONDOWN:
                        self.handle_button(BUTTON_NAMES.get(e.button, f"BUTTON{e.button}"), True)
                    elif e.type == pygame.JOYBUTTONUP:
                        self.handle_button(BUTTON_NAMES.get(e.button, f"BUTTON{e.button}"), False)
                    elif e.type == pygame.JOYAXISMOTION:
                        if e.axis in (0, 1):
                            self.on_move_axis(e.axis, e.value)
                        elif e.axis == 2:
                            self.on_trigger("LT", e.value)
                        elif e.axis in (3, 4):
                            # 右摇杆 → 鼠标移动（axis 3=X、4=Y）
                            self.on_mouse_axis(e.axis, e.value)
                        elif e.axis == 5:
                            # 注意：SDL 2.28 XInput 后端轴布局为 0/1=左摇杆、2=LT、
                            # 3/4=右摇杆、5=RT（不是 3=RT！）
                            self.on_trigger("RT", e.value)
                    elif e.type == pygame.JOYHATMOTION:
                        self.update_dir_source(self.hat_dirs, hat_to_dirs(e.value))
                self.fire_repeats()
                self.move_mouse_by_stick()
                clock.tick(100)  # 约 10ms 一帧，CPU 占用低
        except KeyboardInterrupt:
            pass


def main():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    mapper = Mapper(config_path)

    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("错误：未检测到手柄，请确认 2.4G 接收器已插入或 USB 线已连接")
        sys.exit(1)

    stick = pygame.joystick.Joystick(0)
    stick.init()
    print(f"已连接手柄：{stick.get_name()}")
    print(f"当前配置档：{mapper.profile_name}")
    print("提示：按 Ctrl+C 退出")

    app = GamepadApp(stick, mapper)
    try:
        app.run()
    finally:
        pygame.quit()
    print("已退出，再见")


if __name__ == "__main__":
    main()
