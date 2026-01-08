import pygame
from core import *
from const import *

class PyPR:
    def __init__(self, **args):
        # 初始化 pygame
        if not pygame.get_init():
            pygame.init()

        # 初始化窗口
        _window_width = args.get("window_width", DEFAULT_WINDOW_WIDTH)
        _window_height = args.get("window_width", DEFAULT_WINDOW_HEIGHT)
        self.window = Window(_window_width, _window_height, pygame.DOUBLEBUF | pygame.OPENGL)

        self.window.create_window()

        # 初始化渲染器
        self.renderer = Renderer()
        self.renderer.set_blend(True)

        # 初始化变量
        self.running = True

    def _handle_events(self, events: list[pygame.Event]):
        for event in events:
            match event.type:
                case pygame.QUIT: # 退出
                    self.running = False

    def main_loop(self):
        while self.running:
            # 处理事件
            events = pygame.event.get()
            self.window.handle_events(events)
            self._handle_events(events)

if __name__ == "__main__":
    app = PyPR()

    app.main_loop()