"""绕过事件队列，直接轮询 SDL joystick 状态（get_button），并禁用所有非 XInput 后端。"""

import os

# 必须在 pygame.init() 之前设置：只留 XInput 后端
os.environ["SDL_JOYSTICK_HIDAPI"] = "0"
os.environ["SDL_JOYSTICK_XINPUT"] = "1"
os.environ["SDL_JOYSTICK_RAWINPUT"] = "0"
os.environ["SDL_JOYSTICK_DINPUT"] = "0"

import time

import pygame

pygame.init()
pygame.joystick.init()

count = pygame.joystick.get_count()
if count == 0:
    print("未检测到手柄")
    pygame.quit()
    raise SystemExit(0)

js = pygame.joystick.Joystick(0)
js.init()
print(f"手柄: {js.get_name()} | 按钮 {js.get_numbuttons()} | 轴 {js.get_numaxes()} | hat {js.get_numhats()}")
print("开始直接轮询 get_button()（绕过事件队列），按手柄按键，Ctrl+C 退出...")

last = [False] * js.get_numbuttons()
last_axis = [0.0] * js.get_numaxes()
last_hat = (0, 0)
try:
    while True:
        pygame.event.pump()  # 触发 SDL_JoystickUpdate
        for i in range(js.get_numbuttons()):
            cur = js.get_button(i)
            if cur != last[i]:
                print(f"[按钮 {i} {'按下' if cur else '释放'}]")
                last[i] = cur
        for a in range(js.get_numaxes()):
            v = js.get_axis(a)
            if abs(v - last_axis[a]) > 0.05:
                print(f"[轴 {a} = {v:+.2f}]")
                last_axis[a] = v
        h = js.get_hat(0)
        if h != last_hat:
            print(f"[Hat = {h}]")
            last_hat = h
        time.sleep(0.02)
except KeyboardInterrupt:
    pass
pygame.quit()
print("已退出")