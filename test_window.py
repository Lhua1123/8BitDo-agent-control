"""带真实窗口的手柄事件测试：排除无窗口模式下 SDL 收不到输入事件的问题。"""

import pygame

pygame.init()
pygame.joystick.init()

# 创建真实窗口（SDL 在 Windows 上依赖窗口消息接收输入事件）
screen = pygame.display.set_mode((320, 200))
pygame.display.set_caption("手柄测试 - 按任意键，关闭窗口退出")

count = pygame.joystick.get_count()
if count == 0:
    print("未检测到手柄")
    pygame.quit()
    raise SystemExit(0)

js = pygame.joystick.Joystick(0)
js.init()
print(f"手柄: {js.get_name()} | 轴 {js.get_numaxes()} | 按钮 {js.get_numbuttons()} | Hat {js.get_numhats()}")

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.JOYBUTTONDOWN:
            print(f"[按钮 {e.button} 按下]")
        elif e.type == pygame.JOYBUTTONUP:
            print(f"[按钮 {e.button} 释放]")
        elif e.type == pygame.JOYAXISMOTION:
            print(f"[轴 {e.axis} = {e.value:+.2f}]")
        elif e.type == pygame.JOYHATMOTION:
            print(f"[Hat 方向 = {e.value}]")
    pygame.time.wait(10)

pygame.quit()
print("已退出")