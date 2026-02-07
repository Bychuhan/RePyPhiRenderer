from dataclasses import dataclass


@dataclass
class Config:
    width: int = 800
    height: int = 600

    resources_dir: str = "resources/"

    illustration_blurriness: float = 80.0
    illustration_brightness: float = 0.1

    render: bool = False
    video_output_path: str = "output.mp4"
    encoder: str = "libx264"
    video_fps: int = 60
    video_bitrate: str = "15000k"


@dataclass_json
@dataclass
class ResColors:
    line_color: list[float]


@dataclass_json
@dataclass
class ResConfig:
    colors: ResColors
