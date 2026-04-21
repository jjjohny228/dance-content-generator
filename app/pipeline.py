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
            render_mode=args.mode,
            supported_video_extensions=config.supported_video_extensions,
        )
    elif args.mode != config.render_mode:
        config = AppConfig(
            paths=config.paths,
            layout=config.layout,
            style=config.style,
            chroma_key=config.chroma_key,
            encoding=config.encoding,
            random_seed=config.random_seed,
            include_commentator=config.include_commentator,
            render_mode=args.mode,
            supported_video_extensions=config.supported_video_extensions,
        )

    run_pipeline(config=config, dry_run=args.dry_run)
    return 0


def run_pipeline(config: AppConfig, dry_run: bool = False) -> None:
    ensure_runtime_dependencies()
    ensure_directories(config)
    _validate_font_file(config.style.font_file)

    rng = random.Random(config.random_seed)
    backgrounds = find_pool(config.paths.backgrounds_dir, config, "background videos")
    commentators = []
    if config.include_commentator:
        commentators = find_pool(config.paths.commentators_dir, config, "commentators")
    if config.render_mode == "classic":
        emojis = find_emoji_images(config)
        source = find_single_source(config)
        challengers = find_pool(config.paths.challengers_dir, config, "challengers")
        render_plans = build_render_plans(
            source=source,
            challengers=challengers,
            backgrounds=backgrounds,
            emojis=emojis,
            commentators=commentators,
            config=config,
            rng=rng,
        )
    elif config.render_mode == "what-is-better":
        render_plans = build_what_is_better_render_plans(
            candidates=find_pool(config.paths.what_is_better_dir, config, "what-is-better videos"),
            backgrounds=backgrounds,
            commentators=commentators,
            config=config,
            rng=rng,
        )
    else:
        raise RuntimeError(f"Unsupported render mode: {config.render_mode}")

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


def build_what_is_better_render_plans(
    candidates: list[MediaFile],
    backgrounds: list[MediaFile],
    commentators: list[MediaFile],
    config: AppConfig,
    rng: random.Random,
) -> list[RenderPlan]:
    if len(candidates) < 2:
        raise RuntimeError(
            f"'source_what_is_better' must contain at least two videos. Found {len(candidates)} file(s) in "
            f"{config.paths.what_is_better_dir}."
        )

    plans: list[RenderPlan] = []
    base_timestamp = int(time.time())

    for index, first_video in enumerate(candidates):
        second_video = candidates[(index + 1) % len(candidates)]
        total_duration = first_video.duration + second_video.duration
        background = rng.choice(backgrounds)
        commentator = rng.choice(commentators) if config.include_commentator else first_video
        plans.append(
            RenderPlan(
                source=first_video,
                opponent=second_video,
                background=background,
                commentator=commentator,
                output_path=config.paths.output_dir / f"{base_timestamp + index}.mp4",
                main_on_left=True,
                background_offset=_pick_offset(background.duration, total_duration, rng),
                commentator_offset=_pick_offset(commentator.duration, total_duration, rng)
                if config.include_commentator
                else 0.0,
                me_label="",
                opponent_label="",
                me_emoji_path=Path(),
                opponent_emoji_path=Path(),
                mode="what-is-better",
                title_text="Что лучше?",
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
    parser.add_argument(
        "--mode",
        choices=("classic", "what-is-better"),
        default=CONFIG.render_mode,
        help="Render mode: classic side-by-side or sequential 'what-is-better'.",
    )
    return parser
