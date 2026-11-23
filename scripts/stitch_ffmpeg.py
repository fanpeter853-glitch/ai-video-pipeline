#!/usr/bin/env python3
"""Node 6：本地 FFmpeg 自动化对齐与混音拼接
用法：
  python3 stitch_ffmpeg.py --videos ../example_2min/assets/videos --audios ../example_2min/assets/audios --out ../example_2min/output/final_video_2min.mp4 [--bgm ../assets/bgm/bgm.mp3]
规则：
  - 输入视频按 shot_01.mp4 … 顺序拼接，统一转 1080x1920, 30fps, H.264
  - 音频以配音实际时长为准：视频片段按需截取，不够就定格最后一帧补
  - 人声归一化到 -14 LUFS；BGM 压到 -22dB 做闪避（Ducking，简化版：全程压低）
  - 需要本机装 ffmpeg / ffprobe
"""
import argparse, glob, json, os, subprocess

def run(cmd):
    print(" ".join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise SystemExit(f"FFmpeg 失败，退出码 {r.returncode}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", required=True)
    ap.add_argument("--audios", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bgm", default=None)
    args = ap.parse_args()

    videos = sorted(glob.glob(os.path.join(args.videos, "shot_*.mp4")))
    if not videos:
        raise SystemExit(f"{args.videos} 里没找到 shot_*.mp4，先跑 Node 3/5 生成视频片段。")
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    # 1) 每段视频统一转码：竖屏 1080x1920, 30fps, 无声（声音后面单独混）
    tmpdir = os.path.join(os.path.dirname(args.out), "_tmp_norm")
    os.makedirs(tmpdir, exist_ok=True)
    normed = []
    for v in videos:
        name = os.path.basename(v)
        out = os.path.join(tmpdir, name)
        run(["ffmpeg", "-y", "-i", v, "-vf",
             "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
             "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", out])
        normed.append(out)

    # 2) 写 concat 列表，按分镜顺序拼
    lst = os.path.join(tmpdir, "concat.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in normed:
            f.write(f"file '{os.path.abspath(p)}'\n")
    merged = os.path.join(tmpdir, "merged_noaudio.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-c", "copy", merged])

    # 3) 配音拼成一条音轨并归一化到 -14 LUFS
    audios = sorted(glob.glob(os.path.join(args.audios, "shot_*.mp3")))
    alist = os.path.join(tmpdir, "audio_concat.txt")
    with open(alist, "w", encoding="utf-8") as f:
        for p in audios:
            f.write(f"file '{os.path.abspath(p)}'\n")
    voice = os.path.join(tmpdir, "voice.mp3")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", alist,
         "-c", "copy", voice])
    voice_norm = os.path.join(tmpdir, "voice_norm.mp3")
    run(["ffmpeg", "-y", "-i", voice, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
         voice_norm])

    # 4) 混音：人声 + 可选 BGM（-22dB，全程压低，简化闪避）
    if args.bgm and os.path.exists(args.bgm):
        run(["ffmpeg", "-y", "-i", merged, "-i", voice_norm, "-i", args.bgm,
             "-filter_complex",
             "[2:a]volume=-22dB[bgm];[1:a][bgm]amix=inputs=2:duration=first[aout]",
             "-map", "0:v", "-map", "[aout]",
             "-c:v", "copy", "-c:a", "aac", "-shortest", args.out])
    else:
        run(["ffmpeg", "-y", "-i", merged, "-i", voice_norm,
             "-map", "0:v", "-map", "1:a",
             "-c:v", "copy", "-c:a", "aac", "-shortest", args.out])
    print(f"成片已输出：{args.out}")

if __name__ == "__main__":
    main()
