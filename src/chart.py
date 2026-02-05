from __future__ import annotations

from typing import Any, Literal
from abc import ABC, abstractmethod
from enum import IntEnum
from collections import deque

from loguru import logger

from .renderer import Renderer
from .config import Config
from .utils import *
from .sound_manager import SoundManager


class Chart(ABC):
    @abstractmethod
    def to_chart_time(self, now_time: float) -> float:
        """
        将传入的时间转换为谱面时间 (一般为应用 offset)
        """
        pass

    @abstractmethod
    def update(self, now_time: float, sound_manager: SoundManager):
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


PHI_NOTE_HITSOUNDS = {
    PhiNoteTypes.TAP: "hitsound-tap",
    PhiNoteTypes.DRAG: "hitsound-drag",
    PhiNoteTypes.HOLD: "hitsound-tap",
    PhiNoteTypes.FLICK: "hitsound-flick"
}


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
        floor_position: float = 0  # 速度事件用

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

            if event["startTime"] <= time <= event["endTime"]:
                progress = ((time - event["startTime"]) /
                            (event["endTime"] - event["startTime"]))
                return linear_interpolation(event["start"], event["end"], progress)

            elif time < event["startTime"]:
                right = mid - 1

            else:
                left = mid + 1

        return 0

    @staticmethod
    def group_notes(notes: deque[dict[str, PhiNote]]) -> deque[deque[PhiNote]]:
        groups: dict[float, deque[dict[str, PhiNote]]] = {}

        for note in notes:
            if not note.speed in groups:
                groups[note.speed] = deque()

            groups[note.speed].append(note)

        # 将字典转换为二维队列
        grouped_notes = [value for value in groups.values()]

        return grouped_notes

    @staticmethod
    def init_notes(bpm: float, speed_events: deque, above_notes: list, below_notes: list) -> deque[deque[PhiNote]]:
        [i.update({"isAbove": 1}) for i in above_notes]
        [i.update({"isAbove": -1}) for i in below_notes]
        all_notes: list[dict[str, float | Any]] = above_notes + below_notes

        for note in all_notes:
            note["time"] = PhiDataConverter.tick_to_sec(bpm, note["time"])
            note["positionX"] = (
                PhiDataConverter.convert_note_x_pos(note["positionX"]))
            note["holdTime"] = PhiDataConverter.tick_to_sec(
                bpm, note["holdTime"])
            note["floorPosition"] = PhiDataProcessor.get_floor_position(
                note["time"], speed_events)

            note["visible"] = True

            if note["type"] == PhiNoteTypes.HOLD:
                note["holdSpeed"] = PhiDataConverter.convert_speed_event_value(
                    note["speed"])
                note["speed"] = 1

                note["endTime"] = note["time"] + note["holdTime"]
                note["length"] = (note["holdTime"] * note["holdSpeed"])

                note["visible"] = bool(note["length"])

        # 按 floorPosition 排序以处理部分特殊情况
        all_notes.sort(key=lambda note: note["floorPosition"])

        note_objs: list[PhiNote] = [PhiNote(note) for note in all_notes]

        # 按 speed 分组以处理部分特殊情况
        grouped_notes = PhiDataProcessor.group_notes(deque(note_objs))

        return grouped_notes

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


# 更新 Note 时返回码枚举
class NoteResultCode(IntEnum):
    OK = 0
    HIT = 1
    BREAK = 2


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

        self.note_groups = PhiDataProcessor.init_notes(
            self.bpm, self.speed_events, data["notesAbove"], data["notesBelow"]
        )
        # 计算此判定线的总 Note 数
        self.note_num = len([item for row in self.note_groups for item in row])

        logger.info(f"已加载 {self.index} 号判定线的 Note")
        logger.info(
            f"#notes({self.index}): {self.note_num} ({len(self.note_groups)} groups)")

        self.x_pos: float = 0
        self.y_pos: float = 0
        self.rotate: float = 0
        self.opacity: float = 0
        self.floor_position: float = 0

        self.last_processed_note_indices: list[int] = (
            [0] * len(self.note_groups))  # 最后处理的 Note 索引列表
        self.note_floor_position_threshold: int = 2 * config.height  # Note break 的 fp 阈值

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
        self.floor_position = PhiDataProcessor.update_events(
            self.speed_events, PhiEventTypes.SPEED, now_time)

    def update_notes(self, now_time: float, sound_manager: SoundManager):
        for group_index, notes in enumerate(self.note_groups):
            self.last_processed_note_indices[group_index] = -1

            note_index = -1

            for note in notes.copy():
                note_index += 1

                result = note.update(now_time, self, sound_manager)

                if result == NoteResultCode.HIT:
                    notes.remove(note)

                    note_index -= 1  # 由于 Notes 被删除一项，index 应减 1

                    continue

                if result == NoteResultCode.BREAK:
                    break

                self.last_processed_note_indices[group_index] = note_index

    def render_notes(self, renderer: Renderer):
        for group_index, notes in enumerate(self.note_groups):
            last_processed_note_index = self.last_processed_note_indices[group_index]

            for note_index, note in enumerate(notes.copy()):
                if note_index > last_processed_note_index:
                    break

                note.render(renderer)

    def render(self, renderer: Renderer):
        if self.opacity > 0:
            renderer.render_rect(x=self.x_pos, y=self.y_pos, w=self.width, h=self.height, r=self.rotate,
                                 color=(*self.rgb_color, self.opacity), anchor=(0.5, 0.5))


class PhiNote:
    def __init__(self, data: dict):
        self.type = data["type"]
        self.time = data["time"]
        self.x_pos = data["positionX"]
        self.floor_position = data["floorPosition"]
        self.speed = data["speed"]
        self.is_above = data["isAbove"]

        self.is_visible = data["visible"]
        self.is_hit = False  # 是否被打击 (now_time >= start_time)

        self.hold_time = 0
        self.hold_speed = 1
        self.end_time = self.time
        self.length = 0

        if self.type == PhiNoteTypes.HOLD:
            self.hold_time = data["holdTime"]
            self.hold_speed = data["holdSpeed"]
            self.end_time = data["endTime"]
            self.length = data["length"]

        self.now_x: float = 0
        self.now_y: float = 0
        self.now_end_x: float = 0
        self.now_end_y: float = 0
        self.now_rotate: float = 0
        self.now_floor_position: float = self.floor_position
        self.now_end_floor_position: float = self.floor_position
        self.now_length = self.length

        self.hitsound_name = PHI_NOTE_HITSOUNDS[self.type]

    def update(self, now_time: float, parent_line: PhiLine, sound_manager: SoundManager) -> Literal[0, 1, 2]:
        if now_time >= self.time:
            if not self.is_hit:

                sound_manager.play_sound(self.hitsound_name)

                self.is_hit = True

            if self.type == PhiNoteTypes.HOLD and now_time <= self.end_time:  # 长条长按期间判断
                now_hold_time = now_time - self.time

                self.now_length = self.length - now_hold_time * self.hold_speed

                self.now_floor_position = 0  # 强制将当前 fp 设为 0 以确保长条在判定线上
                self.now_end_floor_position = self.now_length
            else:
                self.now_x, self.now_y = rotate_translate(
                    parent_line.x_pos, parent_line.y_pos, parent_line.rotate, self.x_pos, 0)

                return NoteResultCode.HIT
        else:
            self.now_floor_position = ((self.floor_position - parent_line.floor_position)
                                       * self.speed)
            self.now_end_floor_position = self.now_floor_position + self.now_length

        if self.now_floor_position > parent_line.note_floor_position_threshold:
            return NoteResultCode.BREAK

        real_floor_position = self.now_floor_position * self.is_above
        real_end_floor_position = self.now_end_floor_position * self.is_above

        self.now_x, self.now_y = rotate_translate(
            parent_line.x_pos, parent_line.y_pos, parent_line.rotate, self.x_pos, real_floor_position)

        if self.type == PhiNoteTypes.HOLD:
            self.now_end_x, self.now_end_y = rotate_translate(
                parent_line.x_pos, parent_line.y_pos, parent_line.rotate, self.x_pos, real_end_floor_position)

        self.now_rotate = parent_line.rotate

        return NoteResultCode.OK

    def render(self, renderer: Renderer):
        if self.now_floor_position < -0.0001:  # 遮罩逻辑，-0.0001 防止误差
            return

        # 长条初始长度为 0 时不渲染 ( 初始长度不为 0 但当前长度为 0 仍然会正常渲染长条尾 )
        if self.type == PhiNoteTypes.HOLD and self.length == 0:
            return

        # TODO: Note 纹理
        if self.type == PhiNoteTypes.HOLD:  # 长条渲染
            # 长条头
            if not self.is_hit:
                renderer.render_rect(self.now_x, self.now_y,
                                     50, 10, self.now_rotate, anchor=(0.5, 1))

            # 长条身
            renderer.render_rect(self.now_x, self.now_y, 50,
                                 self.now_length * self.is_above, self.now_rotate, anchor=(0.5, 0))

            # 长条尾
            renderer.render_rect(self.now_end_x, self.now_end_y,
                                 50, 10, self.now_rotate, anchor=(0.5, 0))

        else:  # 其他 Note 渲染
            renderer.render_rect(
                self.now_x, self.now_y, 50, 20, self.now_rotate
            )


class PhiChart(Chart):
    def __init__(self, format_version: Literal[3], offset: float, lines: list[PhiLine]):
        self.format_version = format_version
        self.offset = offset
        self.lines = lines

    def to_chart_time(self, now_time: float) -> float:
        return now_time - self.offset

    def update(self, now_time: float, sound_manager: SoundManager):
        for line in self.lines:
            line.update(now_time)

        for line in self.lines:
            line.update_notes(now_time, sound_manager)

    def render(self, renderer: Renderer):
        for line in self.lines:
            line.render(renderer)

        for line in self.lines:
            line.render_notes(renderer)


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

                logger.info(f"#lines: {len(line_objs)}")
                logger.info(
                    f"#notes: {sum([line.note_num for line in line_objs])}")

                result_chart = PhiChart(format_version, offset, line_objs)

                return result_chart
            else:
                logger.error("不支持的谱面格式")

                return None
        else:
            logger.error("不支持的谱面格式")

            return None
