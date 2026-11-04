#!/usr/bin/env python3
"""(Copied from the website-animations skill; adds --poster.)
Render an SVG-defined animation timeline to MP4 and/or GIF.

WHY THIS EXISTS
    Sandboxed environments usually cannot download a headless browser
    (Chromium CDNs are blocked), so you cannot screen-record a CSS
    animation. Instead: express the timeline in Python, emit one full
    SVG document per frame, rasterize with cairosvg, encode with ffmpeg.
    This is deterministic, dependency-light, and produces crisper output
    than screen capture anyway.

USAGE
    pip install cairosvg --break-system-packages
    python render_svg_animation.py path/to/scene.py \
        --mp4 out.mp4 --gif out.gif [--fps 30] [--gif-fps 20] [--gif-width 600]

SCENE CONTRACT — the scene file must define:
    DURATION : float   total seconds
    WIDTH    : int     output pixel width  (use even numbers for MP4)
    HEIGHT   : int     output pixel height (use even numbers for MP4)
    svg_at(t: float) -> str    full SVG document string for time t

See examples/d13-blueprint/scene.py for a complete worked example,
and references/video-export.md for encoding rationale.
"""
import argparse
import importlib.util
import pathlib
import shutil
import subprocess
import sys
import tempfile


def load_scene(path: str):
    p = pathlib.Path(path).resolve()
    spec = importlib.util.spec_from_file_location("scene", p)
    mod = importlib.util.module_from_spec(spec)
    # let scenes load sibling assets with relative paths
    sys.path.insert(0, str(p.parent))
    spec.loader.exec_module(mod)
    for attr in ("DURATION", "WIDTH", "HEIGHT", "svg_at"):
        if not hasattr(mod, attr):
            sys.exit(f"scene is missing required attribute: {attr}")
    return mod


def render_frames(scene, fps: int, outdir: pathlib.Path) -> int:
    import cairosvg  # deferred so --help works without the dep
    n = max(2, round(scene.DURATION * fps) + 1)
    for i in range(n):
        t = min(i / fps, scene.DURATION)
        svg = scene.svg_at(t)
        cairosvg.svg2png(
            bytestring=svg.encode("utf-8"),
            write_to=str(outdir / f"frame_{i:05d}.png"),
            output_width=scene.WIDTH,
            output_height=scene.HEIGHT,
        )
        if i % max(1, n // 10) == 0:
            print(f"  frame {i + 1}/{n}", flush=True)
    return n


def encode_mp4(frames_dir: pathlib.Path, fps: int, out: str):
    # yuv420p = plays everywhere (QuickTime, browsers, phones).
    # scale filter forces even dimensions, which yuv420p requires.
    subprocess.run(
        [
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%05d.png"),
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18", "-movflags", "+faststart",
            out,
        ],
        check=True,
        capture_output=True,
    )
    print(f"wrote {out}")


def encode_gif(frames_dir: pathlib.Path, fps: int, gif_fps: int, width: int, out: str):
    # Two-pass palette keeps flat brand colors clean (no dither speckle
    # on solid fills). Drop fps and width vs the MP4 to control size.
    filters = f"fps={gif_fps},scale={width}:-1:flags=lanczos"
    with tempfile.NamedTemporaryFile(suffix=".png") as pal:
        subprocess.run(
            [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", str(frames_dir / "frame_%05d.png"),
                "-vf", f"{filters},palettegen=stats_mode=diff",
                pal.name,
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", str(frames_dir / "frame_%05d.png"),
                "-i", pal.name,
                "-lavfi", f"{filters} [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=4",
                "-loop", "0",
                out,
            ],
            check=True,
            capture_output=True,
        )
    print(f"wrote {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scene", help="path to scene .py file")
    ap.add_argument("--mp4", help="output MP4 path")
    ap.add_argument("--gif", help="output GIF path")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--gif-fps", type=int, default=20)
    ap.add_argument("--gif-width", type=int, default=600)
    ap.add_argument("--keep-frames", help="also copy rendered frames to this directory")
    ap.add_argument("--poster", help="write a PNG of one frame (use with --poster-t)")
    ap.add_argument("--poster-t", type=float, default=None, help="poster time in s (default: DURATION*0.6)")
    args = ap.parse_args()

    if not args.mp4 and not args.gif and not args.poster:
        sys.exit("nothing to do: pass --mp4 and/or --gif")

    scene = load_scene(args.scene)
    if args.poster:
        import cairosvg
        pt = args.poster_t if args.poster_t is not None else scene.DURATION * 0.6
        cairosvg.svg2png(bytestring=scene.svg_at(pt).encode("utf-8"), write_to=args.poster,
                         output_width=scene.WIDTH, output_height=scene.HEIGHT)
        print(f"wrote {args.poster} (t={pt}s)")
        if not args.mp4 and not args.gif:
            return
    with tempfile.TemporaryDirectory() as tmp:
        frames = pathlib.Path(tmp)
        print(f"rendering {scene.DURATION}s @ {args.fps}fps ({scene.WIDTH}x{scene.HEIGHT})")
        render_frames(scene, args.fps, frames)
        if args.mp4:
            encode_mp4(frames, args.fps, args.mp4)
        if args.gif:
            encode_gif(frames, args.fps, args.gif_fps, args.gif_width, args.gif)
        if args.keep_frames:
            dst = pathlib.Path(args.keep_frames)
            dst.mkdir(parents=True, exist_ok=True)
            for f in sorted(frames.glob("frame_*.png")):
                shutil.copy(f, dst / f.name)


if __name__ == "__main__":
    main()
