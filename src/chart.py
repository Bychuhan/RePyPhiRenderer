from __future__ import annotations

from typing import Any, Literal
from abc import ABC, abstractmethod
from enum import IntEnum
from collections import deque

from loguru import logger

from .utils import linear_interpolation
from .renderer import Renderer
from .config import Config


class Chart(ABC):
    @abstractmethod
    def to_chart_time(self, now_time: float) -> float:
        """
        将传入的时间转换为谱面时间 (一般为应用 offset)
        """
        pass

    @abstractmethod
    def update(self, now_time: float):
        pass

    @abstractmethod
    def render(self, renderer: Renderer):
        pass


class PhiEventTypes(IntEnum):
    MOVE = 0
    ROTATE = 1
    OPACITY = 2  # Disappear
    SPEED = 3


class PhiNoteTypes(IntEnum):
    TAP = 1
    DRAG = 2
    HOLD = 3
    FLICK = 4


class PhiDataConverter:
    width: int
    height: int

    @staticmethod
    def init(width: int, height: int):  # 初始化宽高用于计算，一般在 Player.__init__ 进行初始化
        PhiDataConverter.width = width
        PhiDataConverter.height = height

    @staticmethod
    def convert_move_event_pos(x: float, y: float):
        return (x - 0.5) * PhiDataConverter.width, (y - 0.5) * PhiDataConverter.height

    @staticmethod
    def convert_speed_event_value(value: float):
        return 0.6 * PhiDataConverter.height * value

    @staticmethod
    def tick_to_sec(bpm: float, tick: int | float):
        return 1.875 / bpm * tick

    @staticmethod
    def convert_note_x_pos(x: float):
        return 0.05625 * x * PhiDataConverter.width


class PhiDataProcessor:
    @staticmethod
    def init_events(bpm: float, events: list, type: Literal[0, 1, 2, 3]) -> deque:
        floor_position = 0  # 速度事件用

        events.sort(key=lambda x: x["startTime"])

        for event in events:
            event["startTime"] = PhiDataConverter.tick_to_sec(
                bpm, event["startTime"])
            event["endTime"] = PhiDataConverter.tick_to_sec(
                bpm, event["endTime"])

            match type:
                case PhiEventTypes.MOVE:  # 移动事件位置转换
                    event["start"], event["start2"] = PhiDataConverter.convert_move_event_pos(
                        event["start"], event["start2"])
                    event["end"], event["end2"] = PhiDataConverter.convert_move_event_pos(
                        event["end"], event["end2"])

                case PhiEventTypes.SPEED:  # 速度事件
                    event["start"] = floor_position

                    event["value"] = PhiDataConverter.convert_speed_event_value(
                        event["value"])

                    event_floor_position = (event["value"] *
                                            (event["endTime"] - event["startTime"]))

                    end_floor_position = floor_position + event_floor_position

                    event["end"] = end_floor_position
                    floor_position = end_floor_position

        return deque(events)

    @staticmethod
    def get_floor_position(time: float, speed_events: deque):
        left, right = 0, len(speed_events) - 1

        while left <= right:
            mid = left + (right - left) // 2
            event = speed_events[mid]

            if event["startTime"] <= time < event["endTime"]:
                progress = ((time - event["startTime"]) /
                            (event["endTime"] - event["startTime"]))
                return linear_interpolation(event["startTime"], event["endTime"], progress)

            elif time < event["startTime"]:
                right = mid - 1

            else:
                left = mid + 1

        return 0

    @staticmethod
    def init_notes(bpm: float, speed_events: deque, above_notes: list, below_notes: list) -> list[list[PhiNote]]:
        [i.update({"above": 1}) for i in above_notes]
        [i.update({"above": -1}) for i in below_notes]
        all_notes = above_notes + below_notes

        for note in all_notes:
            note["time"] = PhiDataConverter.tick_to_sec(bpm, note["time"])
            note["positionX"] = (
                PhiDataConverter.convert_note_x_pos(note["positionX"]))
            note["holdTime"] = PhiDataConverter.tick_to_sec(bpm, note["time"])
            note["floorPosition"] = PhiDataProcessor.get_floor_position(
                note["time"], speed_events)

            note["visible"] = True

            if note["type"] == PhiNoteTypes.HOLD:
                note["holdSpeed"] = note["speed"]
                note["speed"] = 1

                note["endTime"] = note["time"] + note["holdTime"]
                note["length"] = (note["holdTime"] *
                                  PhiDataConverter.convert_speed_event_value(note["holdSpeed"]))

                note["visible"] = bool(note["length"])

    @staticmethod
    def update_events(events: deque, type: Literal[0, 1, 2, 3], now_time: float) -> float | tuple[float, float]:
        now_event = events[0]

        if now_time < now_event["endTime"]:
            event_time = (now_event["endTime"] - now_event["startTime"])
            progress = (
                ((now_time - now_event["startTime"]) / event_time) if event_time
                else 1
            )

            value = linear_interpolation(
                now_event["start"], now_event["end"], progress)

            if type == PhiEventTypes.MOVE:
                y_value = linear_interpolation(
                    now_event["start2"], now_event["end2"], progress)

                return value, y_value
            else:
                return value
        else:
            events.popleft()

            return PhiDataProcessor.update_events(events, type, now_time)


class PhiLine:
    def __init__(self, data: dict[str, Any], config: Config, index: int = 0):
        self.index = index  # 调试与 log 用

        self.bpm = data["bpm"]

        self.move_events = PhiDataProcessor.init_events(
            self.bpm, data["judgeLineMoveEvents"], PhiEventTypes.MOVE)
        self.rotate_events = PhiDataProcessor.init_events(
            self.bpm, data["judgeLineRotateEvents"], PhiEventTypes.ROTATE)
        self.opacity_events = PhiDataProcessor.init_events(
            self.bpm, data["judgeLineDisappearEvents"], PhiEventTypes.OPACITY)
        self.speed_events = PhiDataProcessor.init_events(
            self.bpm, data["speedEvents"], PhiEventTypes.SPEED)

        self.notes = PhiDataProcessor.init_notes(
            self.bpm, self.speed_events, data["notesAbove"], data["notesBelow"]
        )

        self.x_pos: float = 0
        self.y_pos: float = 0
        self.rotate: float = 0
        self.opacity: float = 0

        self.width = 5.76 * config.height
        self.height = 0.0075 * config.height
        # TODO: 从资源配置文件读取判定线颜色
        self.rgb_color = (0.996078431372549, 1, 0.662745098039216)

        logger.info(f"已加载 {self.index} 号判定线")

    def update(self, now_time: float):
        self.x_pos, self.y_pos = PhiDataProcessor.update_events(
            self.move_events, PhiEventTypes.MOVE, now_time)
        self.rotate = PhiDataProcessor.update_events(
            self.rotate_events, PhiEventTypes.ROTATE, now_time)
        self.opacity = PhiDataProcessor.update_events(
            self.opacity_events, PhiEventTypes.OPACITY, now_time)

    def render(self, renderer: Renderer):
        if self.opacity > 0:
            renderer.render_rect(x=self.x_pos, y=self.y_pos, w=self.width, h=self.height, r=self.rotate,
                                 color=(*self.rgb_color, self.opacity), anchor=(0.5, 0.5))


class PhiNote:
    def __init__(self, data: dict):
        self.time = data["time"]
        self.x_pos = data["positionX"]
        self.floor_position = data["floorPosition"]

        self.is_visible = data["visible"]

        self.hold_time = 0
        self.hold_speed = 1
        self.end_time = self.time
        self.length = 0

        if self.type == PhiNoteTypes.HOLD:
            self.hold_time = data["holdTime"]
            self.hold_speed = data["holdSpeed"]
            self.end_time = data["endTime"]
            self.length = data["length"]


class PhiChart(Chart):
    def __init__(self, format_version: Literal[3], offset: float, lines: list[PhiLine]):
        self.format_version = format_version
        self.offset = offset
        self.lines = lines

    def to_chart_time(self, now_time: float) -> float:
        return now_time - self.offset

    def update(self, now_time: float):
        for line in self.lines:
            line.update(now_time)

    def render(self, renderer: Renderer):
        for line in self.lines:
            line.render(renderer)


class ChartParser:
    @staticmethod
    def parse(chart: dict | Any, config: Config) -> Chart | None:
        if isinstance(chart, dict):
            if "formatVersion" in chart:  # 官谱格式
                logger.info("检测到官谱格式")

                format_version = chart["formatVersion"]

                if not format_version in (3, ):  # 检查 formatVersion 是否支持
                    logger.error(f"不支持的 formatVersion : {format_version}")
                logger.info(f"formatVersion: {format_version}")

                offset = chart["offset"]

                logger.info(f"offset: {offset}")

                logger.info("加载判定线...")

                lines = chart["judgeLineList"]

                line_objs = [PhiLine(line, config, index=index)
                             for index, line in enumerate(lines)]

                logger.info(f"#lines: {len(lines)}")

                result_chart = PhiChart(format_version, offset, line_objs)

                return result_chart
            else:
                logger.error("不支持的谱面格式")

                return None
        else:
            logger.error("不支持的谱面格式")

            return None
