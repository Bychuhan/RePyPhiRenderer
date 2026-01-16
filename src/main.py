import pygame
from core import *
from const import *
from config import *
import sys


class PyPR:
    def __init__(self, args: dict[str, Any] = {}):
        # 初始化配置
        self.config = Config(**args)

        # 初始化 pygame
        if not pygame.get_init():
            pygame.init()

        # 初始化窗口
        _window_width = self.config.width
        _window_height = self.config.height
        self.window = Window(_window_width, _window_height,
                             pygame.DOUBLEBUF | pygame.OPENGL)

        self.window.create_window()

        # 初始化渲染器
        self.renderer = Renderer()
        self.renderer.set_blend(True)

        # 初始化变量
        self.running = True

    def _handle_events(self, events: list[pygame.Event]):
        for event in events:
            match event.type:
                case pygame.QUIT:  # 退出
                    self.running = False

    def main_loop(self):
        while self.running:
            # 处理事件
            events = pygame.event.get()
            self.window.handle_events(events)
            self._handle_events(events)


if __name__ == "__main__":
    args = ArgParser.parse(sys.argv, aliases=ARG_ALIASES,
                           type_hints=ARG_TYPE_HINTS)

    app = PyPR(args=args)

    app.main_loop()
