from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path

from app.config import AppConfig
from app.media import MediaFile


@dataclass(frozen=True)
class RenderPlan:
    source: MediaFile
    opponent: MediaFile
    background: MediaFile
    commentator: MediaFile
    output_path: Path
    main_on_left: bool
    background_offset: float
    commentator_offset: float
    me_label: str
    opponent_label: str
    me_emoji_path: Path
    opponent_emoji_path: Path


def build_ffmpeg_command(plan: RenderPlan, config: AppConfig) -> list[str]:
    layout = config.layout
    chroma = config.chroma_key
    encoding = config.encoding

    left_input = "[mainv]" if plan.main_on_left else "[oppv]"
    right_input = "[oppv]" if plan.main_on_left else "[mainv]"

    left_label = plan.me_label if plan.main_on_left else plan.opponent_label
    right_label = plan.opponent_label if plan.main_on_left else plan.me_label
    left_emoji_path = plan.me_emoji_path if plan.main_on_left else plan.opponent_emoji_path
    right_emoji_path = plan.opponent_emoji_path if plan.main_on_left else plan.me_emoji_path

    commentator_y = layout.bottom_y + layout.bottom_height - layout.commentator_height - layout.commentator_bottom_margin
    left_label_center_x = layout.left_x + (layout.slot_width / 2)
    right_label_center_x = layout.right_x + (layout.slot_width / 2)
    left_emoji_input_index = 4 if config.include_commentator else 3
    right_emoji_input_index = 5 if config.include_commentator else 4

    filter_parts = [
        f"color=c=black:s={layout.canvas_width}x{layout.canvas_height}:d={plan.source.duration}[base]",
        (
            f"[0:v]fps={layout.fps},"
            f"scale={layout.slot_width}:{layout.slot_height}:force_original_aspect_ratio=increase,"
            f"crop={layout.slot_width}:{layout.slot_height},setsar=1[mainv]"
        ),
        (
            f"[1:v]fps={layout.fps},"
            f"scale={layout.slot_width}:{layout.slot_height}:force_original_aspect_ratio=increase,"
            f"crop={layout.slot_width}:{layout.slot_height},setsar=1[oppv]"
        ),
        (
            f"[2:v]fps={layout.fps},"
            f"scale={layout.canvas_width}:{layout.bottom_height}:force_original_aspect_ratio=increase,"
            f"crop={layout.canvas_width}:{layout.bottom_height},setsar=1[bgv]"
        ),
        f"[base][bgv]overlay=0:{layout.bottom_y}[step1]",
        f"[step1]{left_input}overlay={layout.left_x}:{layout.top_margin}[step2]",
        f"[step2]{right_input}overlay={layout.right_x}:{layout.top_margin}[step3]",
    ]

    current_stream = "[step3]"
    if config.include_commentator:
        filter_parts.extend(
            [
                (
                    f"[3:v]fps={layout.fps},chromakey={chroma.color}:{chroma.similarity}:{chroma.blend},"
                    f"scale=-2:{layout.commentator_height},setsar=1[commentator]"
                ),
                f"[step3][commentator]overlay=(W-w)/2:{commentator_y}:format=auto[step4]",
            ]
        )
        current_stream = "[step4]"

    filter_parts.extend(
        [
            _drawtext_filter(current_stream, "[step5]", left_label, left_label_center_x, layout.label_y, config),
            _overlay_emoji_filter(
                "[step5]",
                "[step6]",
                left_label_center_x,
                layout.label_y,
                left_emoji_input_index,
                left_label,
                config,
            ),
            _drawtext_filter("[step6]", "[step7]", right_label, right_label_center_x, layout.label_y, config),
            _overlay_emoji_filter(
                "[step7]",
                "[vout]",
                right_label_center_x,
                layout.label_y,
                right_emoji_input_index,
                right_label,
                config,
            ),
        ]
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(plan.source.path),
        "-i",
        str(plan.opponent.path),
        "-ss",
        f"{plan.background_offset:.3f}",
        "-i",
        str(plan.background.path),
    ]
    if config.include_commentator:
        command.extend(
            [
                "-ss",
                f"{plan.commentator_offset:.3f}",
                "-i",
                str(plan.commentator.path),
            ]
        )
    command.extend(
        [
            "-i",
            str(left_emoji_path),
            "-i",
            str(right_emoji_path),
        ]
    )

    command.extend(
        [
        "-filter_complex",
        ";".join(filter_parts),
        "-map",
        "[vout]",
        "-map",
        "0:a?",
        "-t",
        f"{plan.source.duration:.3f}",
        "-c:v",
        encoding.video_codec,
        "-preset",
        encoding.preset,
        "-crf",
        str(encoding.crf),
        "-pix_fmt",
        encoding.pix_fmt,
        "-c:a",
        encoding.audio_codec,
        "-b:a",
        encoding.audio_bitrate,
        "-movflags",
        encoding.movflags,
        str(plan.output_path),
        ]
    )
    return command


def command_as_shell(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _drawtext_filter(
    source: str,
    target: str,
    text: str,
    center_x: float,
    y: int,
    config: AppConfig,
) -> str:
    style = config.style
    escaped_text = _escape_drawtext_text(text)
    font_path = style.font_file.replace("\\", "\\\\").replace(":", r"\:")
    return (
        f"{source}drawtext="
        f"fontfile='{font_path}':"
        f"text='{escaped_text}':"
        f"fontcolor={style.text_color}:"
        f"fontsize={config.layout.label_font_size}:"
        f"x={center_x}-text_w/2:y={y}:"
        f"borderw={style.text_border_width}:"
        f"bordercolor={style.text_border_color}:"
        f"shadowx={style.text_shadow_x}:"
        f"shadowy={style.text_shadow_y}:"
        f"box=1:"
        f"boxcolor={style.text_box_color}:"
        f"boxborderw={style.text_box_border_width}"
        f"{target}"
    )


def _overlay_emoji_filter(
    source: str,
    target: str,
    center_x: float,
    y: int,
    input_index: int,
    text: str,
    config: AppConfig,
) -> str:
    layout = config.layout
    estimated_text_width = _estimate_text_width(text, layout.label_font_size)
    emoji_x = int(center_x + (estimated_text_width / 2) + layout.label_gap)
    emoji_y = y + max((layout.label_font_size - layout.emoji_size) // 2, 0)
    return (
        f"[{input_index}:v]scale={layout.emoji_size}:{layout.emoji_size}:force_original_aspect_ratio=decrease[emoji{input_index}];"
        f"{source}[emoji{input_index}]overlay=x={emoji_x}:y={emoji_y}:format=auto{target}"
    )


def _estimate_text_width(text: str, font_size: int) -> int:
    return max(int(len(text) * font_size * 0.62), font_size)


def _escape_drawtext_text(text: str) -> str:
    return (
        text.replace("\\", r"\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace("%", r"\%")
        .replace(",", r"\,")
        .replace("[", r"\[")
        .replace("]", r"\]")
    )
