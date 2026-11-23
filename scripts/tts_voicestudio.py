#!/usr/bin/env python3
"""Node 4 正式版：VoiceStudio 本地配音（2026-11-24 接入，Peter 确认）
VoiceStudio = 开源本地版 ElevenLabs（debpalash/VoiceStudio，AGPL-3.0），
免费、无账号、无 API key、无订阅，全部在自己电脑上跑。
它取代 edge-tts（虚拟机连不上微软端点）和 Muse 自带配音（音色不是 Peter 的），
成为 Node 4 的首选：用 Peter 自己的克隆声音配音。

前置步骤（在你自己的电脑上做一次，不是虚拟机）：
  1. 装 VoiceStudio：去 https://github.com/debpalash/VoiceStudio/releases/latest
     下最新 release（Windows MSI / macOS DMG / Linux AppImage），第一次启动
     会建 Python 环境并下载默认模型；或 Docker：
       docker run -d -p 127.0.0.1:3900:3900 -v omnivoice-data:/app/omnivoice_data \\
         --name voicestudio palashdeb/omnivoice-studio:stable
  2. 打开 VoiceStudio → Voice cloning，录一段 5~15 秒干净的你自己的声音
     （安静环境、正常说话速度），建一个声音档案，记下它的 profile id 或名字，
     比如 "Peter"。只克隆你自己的声音，不要克隆别人的声音。
  3. 中文优先选 CosyVoice 3 引擎（Model Manager 里装）；默认引擎 OmniVoice 也能用，
     中文效果看引擎，选错引擎中文会差。
  4. 启动 VoiceStudio 后确认本地服务在跑：curl http://localhost:3900/.well-known/voicestudio-speech

用法（接口与 tts_edge.py / tts_muse.py 一致）：
  python3 tts_voicestudio.py --storyboard ../example_2min/storyboard.json \\
    --out ../example_2min/assets/audios --voice Peter --model cosyvoice3
  python3 tts_voicestudio.py --storyboard ../example_2min/storyboard.json \\
    --out ../example_2min/assets/audios --voice Peter --probe-only
规则：
  - 每个分镜输出 audio/shot_XX.mp3，纯净人声，不带 BGM
  - 生成后用 ffprobe 读每个音频的实际毫秒时长，写 durations.json
  - Node 6 拼接时以这个实际时长为准，反向校准视频时间线
API（VoiceStudio 本地 OpenAI 兼容接口，见 docs/agentic-voice.md）：
  - base_url http://localhost:3900/v1
  - POST /v1/audio/speech，model = 引擎 id（如 cosyvoice3）或 tts-1，
    voice = 声音档案 id 或名字，response_format = mp3
  - GET /v1/audio/voices 列出本地声音档案和引擎
注意：
  - 本脚本不在虚拟机里跑通：虚拟机没装 VoiceStudio，localhost:3900 不存在，
    跑了会报连接失败并提示先装先启动，这是预期的。
  - 如果服务没启动，不要自动改去云端配音；先启动 VoiceStudio 再重跑失败的那一段。
"""
import argparse, json, os, subprocess, sys

try:
    import requests
except ImportError:
    raise SystemExit("先装：pip install requests")

def probe_duration_ms(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True)
    try:
        return int(float(r.stdout.strip()) * 1000)
    except Exception:
        return None

def synth_one(text, voice, model, base_url, api_key, out_path):
    url = base_url.rstrip("/") + "/v1/audio/speech"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "voice": voice, "input": text,
              "response_format": "mp3"},
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"VoiceStudio 返回 {resp.status_code}：{resp.text[:300]}")
    with open(out_path, "wb") as f:
        f.write(resp.content)

def main(args):
    with open(args.storyboard, encoding="utf-8") as f:
        data = json.load(f)
    os.makedirs(args.out, exist_ok=True)
    # 先确认服务在跑，失败就直接说明原因，不静默换别的配音
    try:
        r = requests.get(args.base_url.rstrip("/") + "/.well-known/voicestudio-speech",
                         timeout=5)
        r.raise_for_status()
    except Exception as e:
        print("VoiceStudio 本地服务没连上：", e)
        print("先在你自己的电脑上启动 VoiceStudio，确认 http://localhost:3900 能打开，")
        print("再重跑本脚本。不要用云端配音代替。")
        sys.exit(1)
    durations = {}
    for shot in data["shots"]:
        out = os.path.join(args.out, f"{shot['shot_id']}.mp3")
        if os.path.exists(out) and not args.force and not args.probe_only:
            print(f"跳过已存在：{out}")
        elif not args.probe_only:
            try:
                synth_one(shot["voiceover_text"], args.voice, args.model,
                          args.base_url, args.api_key, out)
            except Exception as e:
                print(f"失败 {shot['shot_id']}：{e}（只重跑这一段，别全量重跑）")
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
    ap.add_argument("--voice", default="Peter",
                    help="VoiceStudio 里你自己的声音档案 id 或名字")
    ap.add_argument("--model", default="cosyvoice3",
                    help="引擎 id，中文优先 cosyvoice3；默认引擎用 tts-1")
    ap.add_argument("--base-url", default="http://localhost:3900",
                    help="VoiceStudio 本地服务地址")
    ap.add_argument("--api-key", default="local",
                    help="本地服务 key，默认 local")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--probe-only", action="store_true",
                    help="只测已有音频的时长并写 durations.json")
    args = ap.parse_args()
    main(args)
