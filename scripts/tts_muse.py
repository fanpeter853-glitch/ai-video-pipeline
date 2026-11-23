#!/usr/bin/env python3
"""Node 4 替换版：Muse 自带配音（edge-tts 在虚拟机里连不上微软端点时的替代）
用法：
  python3 tts_muse.py --storyboard ../example_2min/storyboard.json --out ../example_2min/assets/audios
  python3 tts_muse.py --storyboard ../example_2min/storyboard.json --out ../example_2min/assets/audios --force
规则（与 tts_edge.py 接口一致）：
  - 每个分镜输出 audio/shot_XX.mp3，纯净人声，不带 BGM
  - 生成后用 ffprobe 读每个音频的实际毫秒时长，写 durations.json
  - Node 6 拼接时以这个实际时长为准，反向校准视频时间线
注意：
  - 音色是 Muse 默认配音，不是 edge-tts 的 zh-CN-YunxiNeural 男声。
    要 Yunxi 音色，在自己电脑上跑 tts_edge.py（网络能连 speech.platform.bing.com 时）。
  - Peter 自己配音是更优先的选项：按分段录音单逐段录，文件命名同样为
    shot_XX.mp3 放到同一个 out 目录，durations.json 由本脚本的 --probe-only 生成。
"""
import argparse, json, os, subprocess

def probe_duration_ms(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True)
    try:
        return int(float(r.stdout.strip()) * 1000)
    except Exception:
        return None

def main(args):
    with open(args.storyboard, encoding="utf-8") as f:
        data = json.load(f)
    os.makedirs(args.out, exist_ok=True)
    durations = {}
    for shot in data["shots"]:
        out = os.path.join(args.out, f"{shot['shot_id']}.mp3")
        if os.path.exists(out) and not args.force and not args.probe_only:
            print(f"跳过已存在：{out}")
        elif not args.probe_only:
            r = subprocess.run(
                ["/opt/hatch/bin/tts", "speak", "--language", "zh",
                 "--text", shot["voiceover_text"], "--output", out],
                capture_output=True, text=True)
            if not os.path.exists(out) or os.path.getsize(out) < 1000:
                print(f"失败 {shot['shot_id']}: {r.stdout[-200:]} {r.stderr[-200:]}")
                continue
            print(f"已生成：{out}")
        ms = probe_duration_ms(out)
        durations[shot["shot_id"]] = ms
        print(f"  {shot['shot_id']} 实际时长：{ms} ms（分镜标称 {shot['duration']}s）")
    with open(os.path.join(args.out, "durations.json"), "w", encoding="utf-8") as f:
        json.dump(durations, f, ensure_ascii=False, indent=2)
    total = sum(v for v in durations.values() if v)
    print(f"总时长：{total} ms = {total/1000:.1f} s")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--probe-only", action="store_true",
                    help="只测已有音频的时长并写 durations.json，用于 Peter 自己配音后")
    args = ap.parse_args()
    main(args)
