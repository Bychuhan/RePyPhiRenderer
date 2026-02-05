from .dxsound import *


class SoundManager:
    def __init__(self):
        self.sounds: dict[str, directSound] = {}

    def create_sound(self, name: str, data: bytes | str, replace: bool = True) -> None:
        if name in self.sounds:
            logger.warning(f"音效 {name} 已存在")

            if not replace:
                return

        self.sounds[name] = directSound(data)

    def play_sound(self, name: str):
        if not name in self.sounds:
            logger.warning(f"音效 {name} 不存在")

            return

        sound = self.sounds[name]

        sound.play()

    def destroy_sound(self, name: str):
        if not name in self.sounds:
            logger.warning(f"销毁的音效 {name} 不存在")

            return

        self.sounds.pop(name)

    def __contains__(self, name: str):
        return name in self.sounds
