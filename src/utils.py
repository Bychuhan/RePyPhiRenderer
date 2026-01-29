import math


def linear_interpolation(start: float, end: float, progress: float) -> float:
    return start + ((end - start) * progress)


def rotate_translate(x: float, y: float, rotate: float, dx: float, dy: float) -> tuple[float, float]:
    _temp_x = x
    _temp_y = y

    if dx:
        _temp_r = math.radians(rotate)
        _temp_x += math.cos(_temp_r) * dx
        _temp_y += math.sin(_temp_r) * dx

    if dy:
        _temp_r = math.radians(rotate + 90)
        _temp_x += math.cos(_temp_r) * dy
        _temp_y += math.sin(_temp_r) * dy

    return _temp_x, _temp_y
