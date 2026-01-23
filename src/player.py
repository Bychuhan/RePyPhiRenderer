from typing import Any

from loguru import logger

from config import *
from chart import *
from timer import *


class Player:
    def __init__(self, config: Config):
        self.config = config

        self.width = config.width
        self.height = config.height

        self.chart: Chart = None

        self.timer = Timer()
        self.timer.reset()

        PhiDataConverter.init(config.width, config.height)

    def load_chart(self, chart: dict | Any, config: Config):
        self.chart = ChartParser.parse(chart, config)

        if self.chart is None:
            logger.error("谱面解析失败")
            return

    def start(self):
        self.timer.start()

    def update(self, renderer: Renderer):
        now_time = self.timer.get_time()
        chart_time = self.chart.to_chart_time(now_time)

        self.chart.update(chart_time)
        self.chart.render(renderer)
