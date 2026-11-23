#!/usr/bin/env python3
"""Node 4：免费广播级 TTS 配音生成（edge-tts）
用法：
  pip install edge-tts
  python3 tts_edge.py --storyboard ../example_2min/storyboard.json --out ../example_2min/assets/audios
  python3 tts_edge.py --storyboard ../example_2min/storyboard.json --out ../example_2min/assets/audios --voice zh-CN-XiaoxiaoNeural
规则：
  - 每个分镜输出 audio/shot_XX.mp3，纯净人声，不带 BGM
  - 生成后用 ffprobe 读每个音频的实际毫秒时长，写 durations.json
  - Node 6 拼接时以这个实际时长为准，反向校准视频时间线
注意：edge-tts 走微软免费端点，0 成本但不是本地模型，
  批量跑太快可能被限速，失败就等一会儿重跑那一段，别全量重跑。
"""
import argparse, asyncio, json, os, subprocess

try:
    import edge_tts
except ImportError:
    raise SystemExit("先装：pip install edge-tts")

async def synth_one(text, voice, out_path):
    comm = edge_tts.Communicate(text, voice)
    await comm.save(out_path)

def probe_duration_ms(path):
    """ffprobe 读毫秒时长，失败返回 None"""
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True)
    try:
        return int(float(r.stdout.strip()) * 1000)
    except Exception:
        return None

async def main_async(args):
    with open(args.storyboard, encoding="utf-8") as f:
        data = json.load(f)
    os.makedirs(args.out, exist_ok=True)
    durations = {}
    for shot in data["shots"]:
        out = os.path.join(args.out, f"{shot['shot_id']}.mp3")
        if os.path.exists(out) and not args.force:
            print(f"跳过已存在：{out}")
        else:
            await synth_one(shot["voiceover_text"], args.voice, out)
            print(f"已生成：{out}")
        ms = probe_duration_ms(out)
        durations[shot["shot_id"]] = ms
        print(f"  {shot['shot_id']} 实际时长：{ms} ms（分镜标称 {shot['duration']}s）")
    with open(os.path.join(args.out, "durations.json"), "w", encoding="utf-8") as f:
        json.dump(durations, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice", default="zh-CN-YunxiNeural",
                    help="zh-CN-YunxiNeural（男声）或 zh-CN-XiaoxiaoNeural（女声）")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    asyncio.run(main_async(args))
