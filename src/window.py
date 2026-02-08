import pygame

from .renderer import *


class Window:
    def __init__(self, width: int, height: int, window_flags: int = 0, caption: str = "RePyPhiRenderer"):
        if not pygame.get_init():
            pygame.init()

        self.width, self.height = width, height
        self.window_flags = window_flags
        self.caption = caption

    def create_window(self):
        pygame.display.set_mode((self.width, self.height), self.window_flags)
        pygame.display.set_caption(self.caption)

    def destroy_window(self):
        pygame.quit()

    def handle_events(self, events: list[pygame.Event]):
        for event in events:
            match event.type:
                case pygame.QUIT:  # 退出
                    self.destroy_window()
