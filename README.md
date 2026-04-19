# Dance Challenge Generator

A Python pipeline for building vertical viral comparison videos:

- two videos are placed side by side at the top;
- the main video from `source/` is placed on either the left or the right;
- a separate background clip from `resources/background_videos/` is used in the bottom section;
- a green-screen commentator is overlaid on top of the bottom background;
- audio is taken only from the main video;
- two versions are created for each `opponent`: `main_left` and `main_right`.

## Structure

```text
source/
source_challangers/
resources/
  background_videos/
  commentators/
  emojis/
output/
temp/
app/
```

## Quick Start

1. Make sure `ffmpeg` and `ffprobe` are installed.
2. Put exactly one video file into `source/`.
3. Put challenger videos into `source_challangers/`.
4. Put vertical background videos into `resources/background_videos/`.
5. Put green-screen commentator videos into `resources/commentators/`.
6. Put emoji image files (`.png`, `.webp`, `.jpg`) into `resources/emojis/`.
7. Adjust settings in [app/config.py](/Users/gleb/PycharmProjects/DanceChallangeGenerator/app/config.py:1) if needed.
8. Run:

```bash
python3 main.py
```

## Useful Commands

Preview commands without rendering:

```bash
python3 main.py --dry-run
```

Disable the commentator:

```bash
python3 main.py --no-commentator
```

Use a fixed seed for reproducible randomization:

```bash
python3 main.py --seed 42
```

## What You Can Configure in config.py

- final video resolution;
- size and position of the top video slots;
- bottom background area;
- commentator size and position;
- text font and styling;
- emoji image size and spacing;
- chroma key settings for green screen removal;
- encoding parameters.

## Notes

- `source/` must contain exactly one file.
- The output duration always matches the duration of the main video.
- Random start offsets are used for both the background and the commentator.
- Labels are automatically centered above each top video.
- If the background or commentator clip is shorter than the main video, rendering starts from the beginning of that clip.
