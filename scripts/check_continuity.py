#!/usr/bin/env python3
"""首尾帧连续性检查：抽每段视频的首帧和尾帧，拼成对照图，人工看接缝。

用法：
  python3 scripts/check_continuity.py --videos example_2min/assets/videos --out example_2min/output/continuity_check.jpg

说明：
  - 每段取第 0.5 秒一帧（首帧）和倒数 0.5 秒一帧（尾帧），上下并排：
    上一行是 shot_NN 的尾帧，下一行是 shot_NN+1 的首帧，两帧应该像同一镜头。
  - 检查点：人物位置、姿势、衣服、桌面物品、光线、机位有没有跳变；
    有跳变的段，重新生成那一段（以它上一段的尾帧为首帧参考图），不要整条重做。
  - 需要 FFmpeg（ffmpeg / ffprobe 已装）。只做检查，不改视频。
"""
import argparse, glob, os, subprocess, sys

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr.strip() or r.stdout.strip())
        sys.exit(r.returncode)

def main(args):
    files = sorted(glob.glob(os.path.join(args.videos, "shot_*.mp4")))
    if len(files) < 2:
        print(f"只找到 {len(files)} 段视频，至少要 2 段才能检查接缝。")
        sys.exit(1)
    tmp = os.path.join(os.path.dirname(args.out), ".continuity_frames")
    os.makedirs(tmp, exist_ok=True)
    pairs = []
    for i, f in enumerate(files):
        base = os.path.splitext(os.path.basename(f))[0]
        first = os.path.join(tmp, f"{base}_first.jpg")
        last = os.path.join(tmp, f"{base}_last.jpg")
        run(["ffmpeg", "-y", "-v", "error", "-ss", "0.5", "-i", f, "-frames:v", "1", first])
        run(["ffmpeg", "-y", "-v", "error", "-sseof", "-0.5", "-i", f, "-frames:v", "1", last])
        pairs.append((base, first, last))
        print(f"{base}：首帧 {first}，尾帧 {last}")
    # 拼对照图：每对接缝两行（上一段尾帧 / 下一段首帧）
    rows = []
    for (prev_base, _, prev_last), (next_base, next_first, _) in zip(pairs, pairs[1:]):
        rows.append((f"{prev_base} 尾帧 -> {next_base} 首帧", prev_last, next_first))
    inputs = []
    for _, a, b in rows:
        inputs += ["-i", a, "-i", b]
    n = len(rows)
    filt = "".join(
        f"[{2*i}:v]scale=360:-1[v{2*i}];[{2*i+1}:v]scale=360:-1[v{2*i+1}];"
        f"[v{2*i}][v{2*i+1}]vstack=inputs=2[r{i}];" for i in range(n)
    ) + "".join(f"[r{i}]" for i in range(n)) + f"vstack=inputs={n},scale=720:-1[out]"
    run(["ffmpeg", "-y", "-v", "error", *inputs,
         "-filter_complex", filt, "-map", "[out]", args.out])
    print(f"\n接缝对照图：{args.out}")
    print("人工检查：每对上下两帧，人物位置、姿势、衣服、桌面、光线、机位是否一致；")
    print("不一致的接缝，记下段号，用上一段尾帧当参考图重生成下一段。")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", required=True)
    ap.add_argument("--out", required=True)
    main(ap.parse_args())
