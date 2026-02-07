# 合成音频主要代码来自 K0nGbawa

from io import BytesIO
import os

import librosa
import tqdm
import soundfile as sf
import numpy as np
from loguru import logger

from .chart import PhiNoteTypes, PhiChart, Chart
from .config import Config


PHI_NOTE_HITSOUNDS = {
    PhiNoteTypes.TAP: "tap",
    PhiNoteTypes.DRAG: "drag",
    PhiNoteTypes.HOLD: "tap",
    PhiNoteTypes.FLICK: "flick"
}


class HitSoundMixer:
    @staticmethod
    def to_stereo(audio: np.array, target_channels: int = 2):
        """确保音频为立体声格式 (channels, samples)"""
        if audio.ndim == 1:
            return np.tile(audio, (target_channels, 1))
        elif audio.ndim == 2 and audio.shape[0] == 1:
            return np.tile(audio, (target_channels, 1))
        elif audio.ndim == 2 and audio.shape[0] == 2:
            return audio
        else:
            return audio[:2, :]

    @staticmethod
    def mix(music: str | bytes, chart: PhiChart | Chart, config: Config, target_sr=48000) -> tuple[np.ndarray, float | int]:
        logger.info("正在加载音乐，该过程耗时可能较长...")

        mus = BytesIO(music) if isinstance(music, bytes) else music
        audio, sr = librosa.load(mus, sr=target_sr, mono=False)

        logger.info("加载完成")

        if len(audio.shape) == 1:
            audio = HitSoundMixer.to_stereo(audio)

        hitsounds = {
            "tap": librosa.load(
                os.path.join(config.resources_dir, "sounds/tap.ogg"),
                sr=target_sr, mono=False
            )[0],
            "drag": librosa.load(
                os.path.join(config.resources_dir, "sounds/drag.ogg"),
                sr=target_sr, mono=False
            )[0],
            "flick": librosa.load(
                os.path.join(config.resources_dir, "sounds/flick.ogg"),
                sr=target_sr, mono=False
            )[0]
        }

        # 确保打击音效为立体声格式
        for key in hitsounds:
            sound = hitsounds[key]
            if len(sound.shape) == 1:
                hitsounds[key] = HitSoundMixer.to_stereo(sound)

        hitsound_audio = np.zeros_like(audio, dtype=np.float32)

        note_count = chart.note_count

        with tqdm.tqdm(total=note_count, unit="Notes", desc="合成音频...") as bar:
            for line in chart.lines:
                for speed in line.note_groups:
                    for note in speed:
                        start_sample = int((note.time + chart.offset) * sr)
                        end_sample = min(
                            audio.shape[-1], start_sample +
                            hitsounds[PHI_NOTE_HITSOUNDS[note.type]].shape[-1])

                        if (0 <= start_sample < hitsound_audio.shape[-1] and
                                start_sample < end_sample):
                            hitsound_audio[:, start_sample:end_sample] += (
                                hitsounds[PHI_NOTE_HITSOUNDS[note.type]][:, 0:end_sample-start_sample])

                            bar.update()

        hitsound_audio = hitsound_audio.clip(-0.5, 0.5)

        audio = audio * 0.5 + hitsound_audio * 0.4

        return audio.astype(np.float32).T, sr

    @staticmethod
    def mix_as_file(music: str | bytes, chart: PhiChart | Chart, config: Config, target_sr=48000, output: str = "outout.wav"):
        audio, sr = HitSoundMixer.mix(
            music, chart, config, target_sr=target_sr)

        sf.write(output, np.array(audio), sr, subtype="FLOAT")
