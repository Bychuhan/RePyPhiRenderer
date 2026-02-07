import sys
import json

from .window import *
from .arg_specs import *
from .arg_parser import *
from .config import *
from .player import *
from .video_renderer import *


class PyPR:
    def __init__(self, args: dict[str, Any] = {}):
        # 初始化配置
        self.config = Config(**args)
        self.res_config = ResConfig.from_json(
            ArgParser.parse_from_toml(
                os.path.join(self.config.resources_dir, "config.toml"),
                True
            ))

        if not self.config.render:
            import pygame

            # 初始化 pygame
            if not pygame.get_init():
                pygame.init()

            # 初始化窗口
            self.window = Window(self.config.width, self.config.height,
                                 pygame.DOUBLEBUF | pygame.OPENGL)

            self.window.create_window()

        # 初始化渲染器
        self.renderer = Renderer(self.config, standalone=self.config.render)
        self.renderer.set_blend(True)

        # 初始化播放器
        self.player = Player(self.config, self.res_config, self.renderer)

        self.video_renderer: VideoRenderer = None

        if self.config.render:
            self.video_renderer = VideoRenderer(self.config)

        # 初始化变量
        self.running = True

    def import_chart_by_path(self, path: str):
        if not path:
            logger.error("未选择谱面文件")

            sys.exit()

        with open(path, "r", encoding="utf-8") as f:
            try:
                self.player.load_chart(json.load(f))
            except Exception as e:
                import traceback

                logger.error(f"谱面导入失败: {e}")

                logger.error(traceback.format_exc())

                sys.exit()

    def import_music(self, music: str | bytes):
        self.player.load_music(music)

        if self.config.render:
            self.video_renderer.set_music_length(self.player.music_length)

    def import_illustration(self, illustration: str | bytes | BytesIO):
        self.player.load_illustration(illustration)

    def _handle_events(self, events: list[pygame.Event]):
        for event in events:
            match event.type:
                case pygame.QUIT:  # 退出
                    self.running = False

    def render_video(self):
        if not self.config.render:
            logger.warning("未启用渲染视频模式")

            return

        self.renderer.create_frame_buffer()
        self.renderer.frame_buffer.use()

        self.video_renderer.create_popen()

        bar = self.video_renderer.get_progress_bar()
        time = 0

        pbo = bytearray(self.config.width * self.config.height * 3)

        for _ in bar:
            self.renderer.clear()

            self.player.update(time=time)

            self.renderer.frame_buffer.read_into(pbo)
            self.video_renderer.write_frame(pbo)

            time += self.video_renderer.frame_time

        self.video_renderer.close()

    def main_loop(self):
        if self.config.render:
            self.render_video()

            return

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

            self.player.update()

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
