import sys
import json

import pygame

from .window import *
from .arg_specs import *
from .config import *
from .player import *


class PyPR:
    def __init__(self, args: dict[str, Any] = {}):
        # 初始化配置
        self.config = Config(**args)

        # 初始化 pygame
        if not pygame.get_init():
            pygame.init()

        # 初始化窗口
        self.window = Window(self.config.width, self.config.height,
                             pygame.DOUBLEBUF | pygame.OPENGL)

        self.window.create_window()

        # 初始化渲染器
        self.renderer = Renderer(self.config)
        self.renderer.set_blend(True)

        # 初始化播放器
        self.player = Player(self.config)

        # 初始化变量
        self.running = True

    def import_chart_by_path(self, path: str):
        if not path:
            logger.error("未选择谱面文件")

            sys.exit()

        with open(path, "r", encoding="utf-8") as f:
            try:
                self.player.load_chart(json.load(f), self.config)
            except Exception as e:
                logger.error(f"谱面导入失败: {e}")

                sys.exit()

    def import_music(self, music: str | bytes):
        self.player.load_music(music)

    def import_illustration(self, illustration: str | bytes | BytesIO):
        self.player.load_illustration(illustration, self.renderer)

    def _handle_events(self, events: list[pygame.Event]):
        for event in events:
            match event.type:
                case pygame.QUIT:  # 退出
                    self.running = False

    def main_loop(self):
        self.player.start()

        while self.running:
            # 处理事件
            events = pygame.event.get()
            self.window.handle_events(events)
            self._handle_events(events)

            if not self.running:
                break

            # 渲染画面
            self.renderer.clear()

            self.player.update(self.renderer)

            pygame.display.flip()


if __name__ == "__main__":
    from tkinter.filedialog import askopenfilename
    from tkinter import Tk

    args = ArgParser.parse(sys.argv, aliases=ARG_ALIASES,
                           type_hints=ARG_TYPE_HINTS)

    app = PyPR(args=args)

    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    app.import_chart_by_path(askopenfilename(
        title="请选择谱面文件",
        filetypes=(
            ("JSON 文件", "*.json"),
            ("所有文件", "*.*"),
        )))

    app.import_music(askopenfilename(
        title="请选择音乐文件",
        filetypes=(
            ("音频文件", "*.mp3 *.ogg *.wav"),
            ("所有文件", "*.*"),
        )))

    app.import_illustration(askopenfilename(
        title="请选择曲绘文件",
        filetypes=(
            ("音频文件", "*.png *.jpg *.jpeg *.gif"),
            ("所有文件", "*.*"),
        )))

    root.destroy()

    app.main_loop()
