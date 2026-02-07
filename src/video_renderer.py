import re
import subprocess

import tqdm

from .config import Config


class VideoRenderer:
    def __init__(self, config: Config, music_length: float | None = None):
        self.config = config

        self.width: int = self.config.width
        self.height: int = self.config.height

        self.video_output_path = config.video_output_path
        self.video_output_path = re.sub(
            r'[:\*\?"<>\|、：？]', '_', self.video_output_path)  # 过滤非法字符

        self.encoder = self.config.encoder

        self.video_fps = self.config.video_fps
        self.video_bitrate = self.config.video_bitrate

        self.process: subprocess.Popen = None

        self.frame_time = 1 / self.video_fps

        self.music_length = 0
        self.total_frame = 0
        if not music_length is None:
            self.music_length = music_length
            self.total_frame = self.video_fps * self.music_length

        # TODO: 异常情况处理

    def set_music_length(self, music_length: float):
        self.music_length = music_length
        self.total_frame = int(self.video_fps * self.music_length)

    def get_progress_bar(self) -> tqdm.tqdm:
        return tqdm.tqdm(range(self.total_frame), desc="渲染视频", unit="帧")

    def create_popen(self):
        ffmpeg_command = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{self.width}x{self.height}",
            "-pix_fmt", "rgb24",
            "-r", str(self.video_fps),
            "-i", "-",
            # "-i", ".\\sound.wav",  TODO: 合成打击音效
            "-c:v", self.encoder,
            "-b:v", self.video_bitrate,
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",  # TODO: 自定义音频比特率
            "-strict", "experimental",
            "-vf", "vflip",
            self.video_output_path
        ]

        print(ffmpeg_command)

        self.process = subprocess.Popen(
            ffmpeg_command, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def write_frame(self, data: bytes):
        self.process.stdin.write(data)

    def close(self):
        self.process.stdin.close()
        self.process.wait()
