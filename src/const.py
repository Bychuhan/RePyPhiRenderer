import json
from typing import Type, Callable

# --- 画面 ---
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600

# --- 参数解析 ---

# 短参数映射 (参数别名)
ARG_ALIASES: dict[str, str] = {
    "w": "width",
    "h": "height"
}

# 参数类型提示
ARG_TYPE_HINTS: dict[str, Type] = {
    "width": int,
    "height": int
}

# 参数类型转换器
ARG_TYPE_CONVERTERS: dict[Type, Callable] = {
    int: int,
    float: float,
    str: str,
    bool: lambda x: str(x).lower() in ("true", "1"),
    list: json.loads,
    dict: json.loads
}
