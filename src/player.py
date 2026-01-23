from typing import Any
from io import BytesIO

from loguru import logger

from config import *
from chart import *
from timer import *
from dxsmixer import *


class Player:
    def __init__(self, config: Config):
        self.config = config

        self.width = config.width
        self.height = config.height

        self.chart: Chart = None
        self.loaded_chart = False

        self.music: musicCls = musicCls()
        self.loaded_music = False

        self.timer = Timer()
        self.timer.reset()

        PhiDataConverter.init(config.width, config.height)

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
            logger.warning(f"音乐加载失败: {e}")

            return

        logger.info("音乐加载成功")

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

        self.chart.update(chart_time)
        self.chart.render(renderer)
