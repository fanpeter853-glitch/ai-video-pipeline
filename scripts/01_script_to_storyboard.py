#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_script_to_storyboard.py
Parses a raw 2-minute video script into structured storyboard JSON (16-20 shots, 4-6s per shot).
"""

import json
import re
import argparse
import os

def parse_script_to_storyboard(script_text, default_shot_duration=5.0):
    lines = [line.strip() for line in script_text.splitlines() if line.strip() and not line.strip().startswith('#')]
    shots = []
    
    current_time = 0.0
    for idx, line in enumerate(lines, 1):
        # Clean line
        voiceover = re.sub(r'^[0-9]+[\.\、\:\s]*', '', line).strip()
        if not voiceover:
            continue
            
        # Estimate duration based on text length (approx 4 chars per second)
        char_count = len(voiceover)
        est_duration = max(3.5, min(6.5, round(char_count / 4.0, 1)))
        
        # Determine camera motion and scene type based on sequence position
        if idx == 1:
            scene_type = "特写 (Close-up)"
            camera_motion = "快速推进 (Quick Push-in)"
            pace = "紧凑抓住眼球 (Hook)"
        elif idx % 4 == 0:
            scene_type = "全景 (Wide Shot)"
            camera_motion = "缓慢拉远 (Slow Pull-out)"
            pace = "舒缓沉淀 (Breathing)"
        elif idx % 2 == 0:
            scene_type = "中近景 (Medium Close-up)"
            camera_motion = "平移跟拍 (Tracking Pan)"
            pace = "清晰讲述 (Explaining)"
        else:
            scene_type = "近景 (Close-up)"
            camera_motion = "微小推镜 (Subtle Push-in)"
            pace = "强化观点 (Emphasis)"

        shots.append({
            "shot_id": f"shot_{idx:02d}",
            "order": idx,
            "start_time": current_time,
            "duration": est_duration,
            "scene_type": scene_type,
            "camera_motion": camera_motion,
            "pace_tag": pace,
            "voiceover": voiceover,
            "visual_description": f"画面与台词强关联：{voiceover[:20]}... 真实电影级质感，胶片颗粒，自然景深",
            "prompt_en": f"Cinematic shot, highly detailed, photorealistic 8k, natural depth of field, {scene_type.split(' ')[-1][1:-1]}, {camera_motion.split(' ')[-1][1:-1]}"
        })
        current_time += est_duration

    return {
        "title": "2-Minute AI Video Storyboard",
        "total_shots": len(shots),
        "estimated_total_duration": round(current_time, 1),
        "shots": shots
    }

def main():
    parser = argparse.ArgumentParser(description="Convert script to storyboard JSON")
    parser.add_argument("--input", "-i", required=True, help="Path to raw script markdown/text file")
    parser.add_argument("--output", "-o", default="storyboard.json", help="Path to output storyboard JSON")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found.")
        return

    with open(args.input, "r", encoding="utf-8") as f:
        content = f.read()

    result = parse_script_to_storyboard(content)
    
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ Storyboard generated: {result['total_shots']} shots, total ~{result['estimated_total_duration']}s -> {args.output}")

if __name__ == "__main__":
    main()
