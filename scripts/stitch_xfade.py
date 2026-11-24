#!/usr/bin/env python3
"""把 6 段 continuity  clips 用 0.5 秒交叉淡化拼成一条，检验接缝卡顿是否缓解。
- 每段先做模糊背景填充到 1080x1920（不裁画面，保留 944x960 全幅）
- 段与段之间 xfade 0.5s，总长 60 - 5*0.5 = 57.5s
- 全部静音（去掉 AI 原声，避免声音跳变也卡）
用法：
  python3 scripts/stitch_xfade.py
"""
import glob, os, subprocess, sys

SRC = os.path.expanduser("~/workspace/goals/personal-media-ip-university-growth-and-business/files/videos-ab-continuity")
OUT = os.path.join(SRC, "stitched_xfade_1080x1920.mp4")
XF = 0.5
DUR = 10.0

files = sorted(glob.glob(os.path.join(SRC, "media-generation-ab-continuity-clip-*.mp4")))
assert len(files) == 6, f"找到 {len(files)} 段，应为 6 段"
cmd = ["ffmpeg", "-y", "-v", "error"]
for f in files:
    cmd += ["-i", f]
# 每段：模糊背景 + 前景居中，输出 1080x1920，静音
filt = []
for i in range(6):
    filt.append(
        f"[{i}:v]split=2[bg{i}][fg{i}];"
        f"[bg{i}]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=40[bg{i}s];"
        f"[fg{i}]scale=1080:-1[fg{i}s];"
        f"[bg{i}s][fg{i}s]overlay=(W-w)/2:(H-h)/2,format=yuv420p,settb=AVTB[v{i}]"
    )
# xfade 链
prev = "v0"
off = DUR - XF
for i in range(1, 6):
    filt.append(f"[{prev}][v{i}]xfade=transition=fade:duration={XF}:offset={off}[x{i}]")
    prev = f"x{i}"
    off += DUR - XF
filt.append(f"[{prev}]format=yuv420p[out]")
cmd += ["-filter_complex", ";".join(filt), "-map", "[out]", "-an",
        "-c:v", "libx264", "-r", "30", OUT]
print(" ".join(cmd[:6]), "...")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stderr[-3000:])
    sys.exit(r.returncode)
print("写好", OUT)
