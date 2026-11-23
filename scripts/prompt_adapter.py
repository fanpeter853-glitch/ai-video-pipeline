#!/usr/bin/env python3
"""Node 5：模型提示词编译器（骨架）
用法：python3 prompt_adapter.py --storyboard ../example_2min/storyboard.json --out ../example_2min/prompts
为 Kling / 即梦 / MiniMax 各出一份提示词文件，字段：主体、光影、运动幅度、负面词。
"""
import argparse, json, os

NEGATIVE = "blurry, distorted hands, garbled text, extra fingers, low quality, watermark, cartoon, deformed face"

def adapt(shot, model):
    base = shot["visual_prompt"]
    motion = {"推": "slow push-in", "拉": "slow pull-out", "摇": "slow pan",
              "移": "slow dolly", "升降": "slow crane up"}.get(shot["camera_motion"], "subtle motion")
    return {
        "shot_id": shot["shot_id"],
        "model": model,
        "prompt": f"{base} {motion}, realistic, natural light, 1080x1920 vertical.",
        "prompt_cn": f"{shot.get('visual_prompt_cn','')}，{shot['camera_motion']}，写实，自然光，竖屏1080x1920。",
        "negative_prompt": NEGATIVE,
        "duration": shot["duration"],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    with open(args.storyboard, encoding="utf-8") as f:
        data = json.load(f)
    os.makedirs(args.out, exist_ok=True)
    for model, fname in [("kling", "kling.json"), ("seedream", "seedream.json"), ("minimax", "minimax.json")]:
        out = [adapt(s, model) for s in data["shots"]]
        with open(os.path.join(args.out, fname), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"写好 {fname}：{len(out)} 条")

if __name__ == "__main__":
    main()
