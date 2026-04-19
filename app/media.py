from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.config import AppConfig


@dataclass(frozen=True)
class MediaFile:
    path: Path
    duration: float


def ensure_runtime_dependencies() -> None:
    for executable in ("ffmpeg", "ffprobe"):
        try:
            subprocess.run(
                [executable, "-version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(f"'{executable}' is not installed or is not available in PATH.") from exc


def ensure_directories(config: AppConfig) -> None:
    for directory in (
        config.paths.source_dir,
        config.paths.challengers_dir,
        config.paths.backgrounds_dir,
        config.paths.commentators_dir,
        config.paths.emojis_dir,
        config.paths.output_dir,
        config.paths.temp_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def get_video_duration(path: Path) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout)
    duration_raw = payload.get("format", {}).get("duration")
    if duration_raw is None:
        raise RuntimeError(f"Could not read duration for file: {path}")
    return float(duration_raw)


def list_video_files(directory: Path, extensions: tuple[str, ...]) -> list[Path]:
    files = [path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in extensions]
    return sorted(files)


def load_media_files(paths: list[Path]) -> list[MediaFile]:
    return [MediaFile(path=path, duration=get_video_duration(path)) for path in paths]


def find_single_source(config: AppConfig) -> MediaFile:
    source_files = list_video_files(config.paths.source_dir, config.supported_video_extensions)
    if len(source_files) != 1:
        raise RuntimeError(
            f"'source' must contain exactly one video file. Found {len(source_files)} file(s) in {config.paths.source_dir}."
        )
    return MediaFile(path=source_files[0], duration=get_video_duration(source_files[0]))


def find_pool(directory: Path, config: AppConfig, label: str) -> list[MediaFile]:
    files = list_video_files(directory, config.supported_video_extensions)
    if not files:
        raise RuntimeError(f"No video files found for {label} in {directory}.")
    return load_media_files(files)


def list_image_files(directory: Path) -> list[Path]:
    supported_extensions = {".png", ".webp", ".jpg", ".jpeg"}
    files = [path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in supported_extensions]
    return sorted(files)


def find_emoji_images(config: AppConfig) -> list[Path]:
    files = list_image_files(config.paths.emojis_dir)
    if not files:
        raise RuntimeError(
            f"No emoji image files found in {config.paths.emojis_dir}. Add PNG/WebP/JPG emoji assets there."
        )
    return files
