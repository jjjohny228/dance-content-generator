# Dance Challenge Generator

A Python pipeline for building vertical viral comparison videos:

- two videos are placed side by side at the top;
- the main video from `source/` is placed on either the left or the right;
- a separate background clip from `resources/background_videos/` is used in the bottom section;
- a green-screen commentator is overlaid on top of the bottom background;
- in classic mode audio is taken only from the main video;
- two versions are created for each `opponent`: `main_left` and `main_right`.
- an additional `what-is-better` mode can show two videos sequentially in the same top layout.

## Structure

```text
source/
source_challangers/
source_what_is_better/
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

For the new sequential mode, put all candidate videos into `source_what_is_better/` and run:

```bash
python3 main.py --mode what-is-better
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

Use the sequential "What is better?" mode:

```bash
python3 main.py --mode what-is-better
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
- `source_what_is_better/` must contain at least two files for the sequential mode.
- In classic mode, the output duration always matches the duration of the main video.
- In `what-is-better` mode, the output duration is `video1 + video2`: first the left video plays while the right shows the first frame, then the left freezes on its last frame and the right video starts.
- In `what-is-better` mode, audio is also played sequentially: first from the first clip, then from the second clip. If one clip has no audio, silence is inserted for that segment.
- Random start offsets are used for both the background and the commentator.
- Labels are automatically centered above each top video.
- In `what-is-better` mode, a single centered caption `Что лучше?` is used instead of per-video labels.
- In `what-is-better` mode, videos are paired in a ring, so each source clip appears in two final renders.
- If the background or commentator clip is shorter than the main video, rendering starts from the beginning of that clip.
