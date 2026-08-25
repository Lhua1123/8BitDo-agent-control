"""手柄连接测试脚本：打印手柄信息与实时输入事件，用于确认连接和按键编号。"""

import os
import sys

# 强制 SDL 使用 XInput 后端（HIDAPI 后端在此手柄上读不到数据，见 main.py 注释）
os.environ["SDL_JOYSTICK_HIDAPI"] = "0"
os.environ["SDL_JOYSTICK_XINPUT"] = "1"
os.environ["SDL_JOYSTICK_RAWINPUT"] = "0"
os.environ["SDL_JOYSTICK_DINPUT"] = "0"

import pygame


def main():
    pygame.init()
    pygame.joystick.init()

    count = pygame.joystick.get_count()
    if count == 0:
        print("未检测到手柄，请确认 2.4G 接收器已插入或 USB 线已连接")
        pygame.quit()
        sys.exit(0)

    # 打印所有手柄的基本信息
    for i in range(count):
        js = pygame.joystick.Joystick(i)
        js.init()
        print(f"手柄 {i}: {js.get_name()} | 轴数 {js.get_numaxes()} | "
              f"按钮数 {js.get_numbuttons()} | Hat 数 {js.get_numhats()}")

    print("\n开始监听输入事件，按 Ctrl+C 或关闭窗口退出...\n")

    last_axis = {}  # {(手柄号, 轴号): 上次打印值}，过滤微小抖动避免刷屏
    try:
        while True:
            pygame.event.pump()  # 维持事件队列
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    sys.exit(0)
                elif e.type == pygame.JOYBUTTONDOWN:
                    print(f"[手柄 {e.joy}] 按钮 {e.button} 按下")
                elif e.type == pygame.JOYBUTTONUP:
                    print(f"[手柄 {e.joy}] 按钮 {e.button} 释放")
                elif e.type == pygame.JOYAXISMOTION:
                    key = (e.joy, e.axis)
                    if abs(e.value - last_axis.get(key, 0.0)) >= 0.05:
                        last_axis[key] = e.value
                        print(f"[手柄 {e.joy}] 轴 {e.axis} = {e.value:+.2f}")
                elif e.type == pygame.JOYHATMOTION:
                    print(f"[手柄 {e.joy}] Hat {e.hat} 方向 = {e.value}")
            pygame.time.wait(10)
    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()
    print("\n已退出")


if __name__ == "__main__":
    main()
