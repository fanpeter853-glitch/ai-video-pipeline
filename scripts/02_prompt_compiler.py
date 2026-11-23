#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_prompt_compiler.py
Compiles storyboard JSON into model-specific prompts for free video platforms:
- jimeng (豆包即梦)
- kling (快手可灵)
- minimax (海螺AI)
"""

import json
import argparse
import os

MODEL_TEMPLATES = {
    "jimeng": {
        "prefix": "电影级质感，胶片颗粒，真实自然光影，9:16竖屏高清，",
        "suffix": "，动作平稳流畅，无变形，大师级调色，4k超高清",
        "negative": "文字，水印，畸变，模糊，卡顿，多余肢体，画面闪烁"
    },
    "kling": {
        "prefix": "Photorealistic cinematic footage, Masterpiece, 8K resolution, 9:16 vertical aspect ratio, ",
        "suffix": ", smooth continuous motion, hyper-realistic physics, warm natural lighting",
        "negative": "low quality, blurry, text, logo, watermark, deformed limbs, glitches"
    },
    "minimax": {
        "prefix": "电影级镜头，真实纪录片风格，微距细节清晰，9:16画幅，",
        "suffix": "，运镜稳定平滑，高动态范围，真实物理交互",
        "negative": "文字乱码，闪烁，穿模，低画质，变形"
    }
}

def compile_prompts(storyboard_data, model_name="jimeng"):
    tmpl = MODEL_TEMPLATES.get(model_name.lower(), MODEL_TEMPLATES["jimeng"])
    compiled = []

    for shot in storyboard_data.get("shots", []):
        shot_id = shot.get("shot_id")
        desc = shot.get("visual_description", "")
        motion = shot.get("camera_motion", "")
        
        prompt = f"{tmpl['prefix']}{desc}，运镜方式：{motion}{tmpl['suffix']}"
        
        compiled.append({
            "shot_id": shot_id,
            "order": shot.get("order"),
            "duration": shot.get("duration"),
            "model_target": model_name,
            "prompt": prompt,
            "negative_prompt": tmpl["negative"],
            "suggested_ratio": "9:16"
        })

    return {
        "model": model_name,
        "total_prompts": len(compiled),
        "prompts": compiled
    }

def main():
    parser = argparse.ArgumentParser(description="Compile storyboard into model-specific video prompts")
    parser.add_argument("--input", "-i", required=True, help="Path to storyboard JSON")
    parser.add_argument("--model", "-m", default="jimeng", choices=["jimeng", "kling", "minimax"], help="Target AI model")
    parser.add_argument("--output", "-o", default=None, help="Output JSON path")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: {args.input} not found.")
        return

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    compiled = compile_prompts(data, args.model)
    
    out_path = args.output or f"compiled_prompts_{args.model}.json"
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(compiled, f, ensure_ascii=False, indent=2)

    print(f"✅ Compiled {compiled['total_prompts']} prompts for [{args.model}] -> {out_path}")

if __name__ == "__main__":
    main()
