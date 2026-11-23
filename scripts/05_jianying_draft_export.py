#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_jianying_draft_export.py
Exports video segments and subtitle metadata to a standard project manifest for Jianying / CapCut draft importing.
"""

import json
import argparse
import os

def export_jianying_manifest(storyboard_path, final_video_path, output_dir):
    with open(storyboard_path, "r", encoding="utf-8") as f:
        sb = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    
    subtitles = []
    current_ms = 0
    for shot in sb.get("shots", []):
        duration_ms = int(shot.get("duration", 5.0) * 1000)
        subtitles.append({
            "index": shot.get("order"),
            "start_time_ms": current_ms,
            "end_time_ms": current_ms + duration_ms,
            "text": shot.get("voiceover", ""),
            "shot_id": shot.get("shot_id")
        })
        current_ms += duration_ms

    draft_manifest = {
        "project_name": "AI_Video_Pipeline_2min",
        "canvas_ratio": "9:16",
        "resolution": {"width": 1080, "height": 1920},
        "fps": 30,
        "media_file": os.path.abspath(final_video_path) if final_video_path else "",
        "total_duration_ms": current_ms,
        "subtitles_timeline": subtitles,
        "usage_guide": "Import final_video.mp4 into Jianying / CapCut, then click [Text] -> [Auto Subtitles / Match Script] to apply highlighted yellow keyframe captions."
    }

    out_file = os.path.join(output_dir, "jianying_draft_info.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(draft_manifest, f, ensure_ascii=False, indent=2)

    print(f"✅ Jianying draft manifest exported: {out_file}")

def main():
    parser = argparse.ArgumentParser(description="Export Jianying / CapCut project draft metadata")
    parser.add_argument("--storyboard", "-s", required=True, help="Path to storyboard JSON")
    parser.add_argument("--video", "-v", default="", help="Path to final stitched video")
    parser.add_argument("--output-dir", "-o", default="workspace/jianying_draft", help="Directory to save draft info")
    args = parser.parse_args()

    export_jianying_manifest(args.storyboard, args.video, args.output_dir)

if __name__ == "__main__":
    main()
