import time


class Timer:  # 仅实现基本计时功能  TODO: 暂停 设置当前时间
    def __init__(self):
        self._now_time = 0
        self._start_time = 0

    def reset(self):
        self._now_time = 0
        self._start_time = 0

    def start(self):
        self._start_time = time.time()

    def update(self):
        self._now_time = time.time() - self._start_time

    def get_time(self):
        self.update()
        return self._now_time
