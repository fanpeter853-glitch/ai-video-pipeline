#!/usr/bin/env python3
"""抽一段视频的首帧和尾帧：首帧锁定法 v2 的链式工具。

用法：
  # 给下一段当首帧参考图：抽上一段的尾帧
  python3 scripts/extract_frames.py --video assets/videos/shot_01.mp4 --out-dir assets/videos --prefix clip01
  # 只抽尾帧
  python3 scripts/extract_frames.py --video assets/videos/shot_01.mp4 --out-dir assets/videos --prefix clip01 --last-only

说明：
  - 首帧取 0.2 秒处（避开编码第一帧的黑场/闪烁），尾帧取倒数 0.5 秒处。
  - 输出 <prefix>_first.jpg 和 <prefix>_last.jpg；下一段生成时只传
    <prefix>_last.jpg 当首帧参考图，不要再传 snapshot 链。
  - 需要 FFmpeg（ffmpeg 已装）。只抽帧，不改视频。
"""
import argparse, os, subprocess, sys

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr.strip() or r.stdout.strip())
        sys.exit(r.returncode)

def main(args):
    if not os.path.exists(args.video):
        print(f"找不到视频：{args.video}")
        sys.exit(1)
    os.makedirs(args.out_dir, exist_ok=True)
    if not args.last_only:
        first = os.path.join(args.out_dir, f"{args.prefix}_first.jpg")
        run(["ffmpeg", "-y", "-v", "error", "-ss", "0.2",
             "-i", args.video, "-frames:v", "1", first])
        print(f"首帧：{first}")
    last = os.path.join(args.out_dir, f"{args.prefix}_last.jpg")
    run(["ffmpeg", "-y", "-v", "error", "-sseof", "-0.5",
         "-i", args.video, "-frames:v", "1", last])
    print(f"尾帧：{last}（下一段的首帧参考图）")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--last-only", action="store_true")
    main(ap.parse_args())
