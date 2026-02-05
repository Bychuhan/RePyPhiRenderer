from typing import Any
from io import BytesIO
import math
import os

from loguru import logger
from PIL import Image, ImageFilter

from .config import *
from .chart import *
from .timer import *
from .dxsmixer import *
from .texture import TextureCreateTypes
from .sound_manager import *


class Player:
    def __init__(self, config: Config):
        self.config = config

        self.width = config.width
        self.height = config.height

        self.chart: Chart = None
        self.loaded_chart = False

        self.music: musicCls = musicCls()
        self.loaded_music = False

        self.loaded_illustration = False

        self.sound_manager = SoundManager()

        self.timer = Timer()
        self.timer.reset()

        PhiDataConverter.init(config.width, config.height)

        self._load_note_sounds()
        logger.info("已加载 Note 音效")

    def load_chart(self, chart: dict | Any, config: Config):
        self.chart = ChartParser.parse(chart, config)

        if self.chart is None:
            logger.error("谱面解析失败")
            return

        self.loaded_chart = True

        logger.info("谱面加载成功")

    def load_music(self, music: str | bytes):
        if not music:
            logger.warning("未选择音乐文件")

            return

        try:
            self.music.load(music)
            self.loaded_music = True
        except Exception as e:
            import traceback

            logger.warning(f"音乐加载失败: {e}")

            logger.warning(traceback.format_exc())

            return

        logger.info("音乐加载成功")

    def load_illustration(self, illustration: str | bytes | BytesIO, renderer: Renderer):
        if not illustration:
            logger.warning("未选择曲绘文件")

            return

        try:
            with Image.open(
                BytesIO(illustration) if isinstance(illustration, bytes) else
                illustration
            ) as image:
                image = image.convert("RGBA")
                image = image.filter(
                    ImageFilter.GaussianBlur(self.config.illustration_blurriness))

                scale = max(
                    self.config.width / image.width,
                    self.config.height / image.height
                )
                image = image.resize((
                    math.ceil(image.width * scale),
                    math.ceil(image.height * scale)
                ))

                renderer.texture_manager.create_texture(
                    renderer.ctx, "illustration", image, TextureCreateTypes.IMAGE)
        except Exception as e:
            import traceback

            logger.warning(f"曲绘加载失败: {e}")

            logger.warning(traceback.format_exc())

            return

        self.loaded_illustration = True
        logger.info("曲绘加载成功")

    def render_illustration(self, renderer: Renderer):
        renderer.render_texture("illustration", x=0, y=0, sx=1, sy=1,
                                r=0, color=(1, 1, 1, 1), anchor=(0.5, 0.5))

        # 渲染背景压暗
        # 第一层-固定0.5不透明度
        renderer.render_rect(x=0, y=0, w=self.config.width, h=self.config.height, r=0,
                             color=(0, 0, 0, 0.5), anchor=(0.5, 0.5))
        # 第二层-不透明度跟随配置
        renderer.render_rect(x=0, y=0, w=self.config.width, h=self.config.height, r=0,
                             color=(0, 0, 0, self.config.illustration_brightness), anchor=(0.5, 0.5))

    def _load_note_sounds(self):
        self.sound_manager.create_sound(
            "hitsound-tap", os.path.join(self.config.resources_dir, "sounds/tap.ogg"))
        self.sound_manager.create_sound(
            "hitsound-flick", os.path.join(self.config.resources_dir, "sounds/flick.ogg"))
        self.sound_manager.create_sound(
            "hitsound-drag", os.path.join(self.config.resources_dir, "sounds/drag.ogg"))

    def start(self):
        if not self.loaded_chart:
            logger.warning("未导入谱面文件，无法开始播放")

            return

        if self.loaded_music:
            self.music.play()

        self.timer.start()

    def update(self, renderer: Renderer):
        if not self.loaded_chart:
            logger.warning("未导入谱面文件")

            return

        now_time = self.timer.get_time()
        chart_time = self.chart.to_chart_time(now_time)

        if self.loaded_illustration:
            self.render_illustration(renderer)

        self.chart.update(chart_time, self.sound_manager)
        self.chart.render(renderer)
