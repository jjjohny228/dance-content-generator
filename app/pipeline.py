from __future__ import annotations

import argparse
import random
import subprocess
import time
from pathlib import Path

from app.config import CONFIG, AppConfig
from app.ffmpeg_builder import RenderPlan, build_ffmpeg_command, command_as_shell
from app.media import (
    MediaFile,
    ensure_directories,
    ensure_runtime_dependencies,
    find_emoji_images,
    find_pool,
    find_single_source,
)


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    config = CONFIG

    if args.seed is not None or args.no_commentator:
        config = AppConfig(
            paths=config.paths,
            layout=config.layout,
            style=config.style,
            chroma_key=config.chroma_key,
            encoding=config.encoding,
            random_seed=args.seed,
            include_commentator=not args.no_commentator,
            supported_video_extensions=config.supported_video_extensions,
        )

    run_pipeline(config=config, dry_run=args.dry_run)
    return 0


def run_pipeline(config: AppConfig, dry_run: bool = False) -> None:
    ensure_runtime_dependencies()
    ensure_directories(config)
    _validate_font_file(config.style.font_file)

    rng = random.Random(config.random_seed)
    source = find_single_source(config)
    challengers = find_pool(config.paths.challengers_dir, config, "challengers")
    backgrounds = find_pool(config.paths.backgrounds_dir, config, "background videos")
    emojis = find_emoji_images(config)
    commentators = []
    if config.include_commentator:
        commentators = find_pool(config.paths.commentators_dir, config, "commentators")

    render_plans = build_render_plans(
        source=source,
        challengers=challengers,
        backgrounds=backgrounds,
        emojis=emojis,
        commentators=commentators,
        config=config,
        rng=rng,
    )

    if not render_plans:
        raise RuntimeError("Nothing to render. No valid render plans were created.")

    for index, plan in enumerate(render_plans, start=1):
        command = build_ffmpeg_command(plan, config)
        print(f"[{index}/{len(render_plans)}] Rendering {plan.output_path.name}")
        print(command_as_shell(command))
        if dry_run:
            continue
        subprocess.run(command, check=True)


def build_render_plans(
    source: MediaFile,
    challengers: list[MediaFile],
    backgrounds: list[MediaFile],
    emojis: list[Path],
    commentators: list[MediaFile],
    config: AppConfig,
    rng: random.Random,
) -> list[RenderPlan]:
    plans: list[RenderPlan] = []
    base_timestamp = int(time.time())
    sequence = 0
    for challenger in challengers:
        for main_on_left in (True, False):
            background = rng.choice(backgrounds)
            commentator = rng.choice(commentators) if config.include_commentator else source
            output_name = f"{base_timestamp + sequence}.mp4"
            sequence += 1
            plans.append(
                RenderPlan(
                    source=source,
                    opponent=challenger,
                    background=background,
                    commentator=commentator,
                    output_path=config.paths.output_dir / output_name,
                    main_on_left=main_on_left,
                    background_offset=_pick_offset(background.duration, source.duration, rng),
                    commentator_offset=_pick_offset(commentator.duration, source.duration, rng)
                    if config.include_commentator
                    else 0.0,
                    me_label="Me",
                    opponent_label="Opponent",
                    me_emoji_path=rng.choice(emojis),
                    opponent_emoji_path=rng.choice(emojis),
                )
            )
    return plans


def _pick_offset(duration: float, target_duration: float, rng: random.Random) -> float:
    max_offset = max(duration - target_duration, 0.0)
    if max_offset <= 0:
        return 0.0
    return rng.uniform(0.0, max_offset)
def _validate_font_file(font_file: str) -> None:
    if not Path(font_file).exists():
        raise RuntimeError(
            f"Font file not found: {font_file}. Update 'font_file' in config.py to a valid .ttf/.ttc path."
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate vertical dance challenge comparison videos.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print ffmpeg commands without rendering output files.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional seed for reproducible random selections.",
    )
    parser.add_argument(
        "--no-commentator",
        action="store_true",
        help="Disable commentator overlay and render only background in the bottom area.",
    )
    return parser
