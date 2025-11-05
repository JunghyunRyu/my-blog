"""간단한 TTS + 슬라이드 영상 생성기.

edge-tts (우선) 또는 gTTS로 나레이션을 생성하고, moviepy로 정적 배경 + 텍스트 슬라이드를 합성.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import tempfile


def _synthesize_tts_edge(text: str, *, voice: str = "ko-KR-SunHiNeural", out_path: Path | None = None) -> Path:
    try:
        import asyncio
        import edge_tts  # type: ignore
    except Exception as e:  # pragma: no cover - 선택적 의존성
        raise RuntimeError("edge-tts 설치 필요") from e

    out_path = out_path or Path(tempfile.mkstemp(suffix=".mp3")[1])

    async def _run():
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(str(out_path))

    asyncio.run(_run())
    return out_path


def _synthesize_tts_gtts(text: str, *, lang: str = "ko", out_path: Path | None = None) -> Path:
    try:
        from gtts import gTTS  # type: ignore
    except Exception as e:  # pragma: no cover - 선택적 의존성
        raise RuntimeError("gTTS 설치 필요") from e

    out_path = out_path or Path(tempfile.mkstemp(suffix=".mp3")[1])
    tts = gTTS(text=text, lang=lang)
    tts.save(str(out_path))
    return out_path


def generate_narration_video(
    *,
    paragraphs: Sequence[str],
    output_path: Path | str,
    width: int = 1280,
    height: int = 720,
    bg_color: tuple[int, int, int] = (248, 249, 250),
    text_color: str = "#1a1a1a",
    prefer_edge_tts: bool = True,
) -> Path:
    """간단한 슬라이드 + 나레이션 영상을 생성한다.

    paragraphs: 슬라이드마다 표시할 텍스트 목록
    output_path: 생성될 mp4 경로
    """
    try:
        from moviepy.editor import (  # type: ignore
            ColorClip,
            TextClip,
            CompositeVideoClip,
            concatenate_videoclips,
            AudioFileClip,
        )
    except Exception as e:
        raise RuntimeError("moviepy 설치 필요") from e

    # TTS 텍스트는 모든 단락을 연결해 한 번에 생성 (간단화)
    narration_text = "\n\n".join(paragraphs)

    # TTS 생성
    audio_path = None
    try:
        if prefer_edge_tts:
            audio_path = _synthesize_tts_edge(narration_text)
        else:
            raise RuntimeError("edge-tts 비활성화")
    except Exception:
        audio_path = _synthesize_tts_gtts(narration_text)

    audio_clip = AudioFileClip(str(audio_path))

    # 슬라이드 클립 생성
    per_slide_duration = max(4.0, audio_clip.duration / max(1, len(paragraphs)))
    slides = []
    for text in paragraphs:
        bg = ColorClip(size=(width, height), color=bg_color).set_duration(per_slide_duration)
        txt = TextClip(text, fontsize=42, color=text_color, method="caption", size=(int(width*0.9), int(height*0.8)))
        txt = txt.set_position("center").set_duration(per_slide_duration)
        slide = CompositeVideoClip([bg, txt])
        slides.append(slide)

    video = concatenate_videoclips(slides).set_audio(audio_clip)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    video.write_videofile(str(output_path), fps=24, codec="libx264", audio_codec="aac")

    # 정리
    try:
        audio_clip.close()
    except Exception:
        pass

    return output_path


