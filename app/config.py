from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class LayoutConfig:
    canvas_width: int = 1080
    canvas_height: int = 1920
    fps: int = 30

    top_margin: int = 110
    top_gap: int = 20
    slot_width: int = 510
    slot_height: int = 860

    bottom_y: int = 1010
    bottom_height: int = 820

    commentator_height: int = 560
    commentator_bottom_margin: int = 28

    left_x: int = 20
    right_x: int = 550

    label_y: int = 36
    label_font_size: int = 54
    label_gap: int = 14
    emoji_size: int = 52


@dataclass(frozen=True)
class StyleConfig:
    font_file: str = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
    text_color: str = "white"
    text_border_color: str = "black"
    text_border_width: int = 4
    text_shadow_x: int = 3
    text_shadow_y: int = 3
    text_box_color: str = "black@0.18"
    text_box_border_width: int = 18
@dataclass(frozen=True)
class ChromaKeyConfig:
    color: str = "03ff00"
    similarity: float = 0.18
    blend: float = 0.08


@dataclass(frozen=True)
class EncodingConfig:
    video_codec: str = 'h264_videotoolbox'
    audio_codec: str = "aac"
    crf: int = 20
    preset: str = "medium"
    audio_bitrate: str = "192k"
    pix_fmt: str = "yuv420p"
    movflags: str = "+faststart"


@dataclass(frozen=True)
class PathConfig:
    source_dir: Path = PROJECT_ROOT / "source"
    challengers_dir: Path = PROJECT_ROOT / "source_challangers"
    backgrounds_dir: Path = PROJECT_ROOT / "resources" / "background_videos"
    commentators_dir: Path = PROJECT_ROOT / "resources" / "commentators"
    emojis_dir: Path = PROJECT_ROOT / "resources" / "emojis"
    output_dir: Path = PROJECT_ROOT / "output"
    temp_dir: Path = PROJECT_ROOT / "temp"


@dataclass(frozen=True)
class AppConfig:
    paths: PathConfig = field(default_factory=PathConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    style: StyleConfig = field(default_factory=StyleConfig)
    chroma_key: ChromaKeyConfig = field(default_factory=ChromaKeyConfig)
    encoding: EncodingConfig = field(default_factory=EncodingConfig)
    random_seed: int | None = None
    include_commentator: bool = True
    supported_video_extensions: tuple[str, ...] = (".mp4", ".mov", ".mkv", ".avi", ".webm")


CONFIG = AppConfig()
