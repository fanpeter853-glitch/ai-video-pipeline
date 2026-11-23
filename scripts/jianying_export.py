#!/usr/bin/env python3
"""Node 7：剪映工程草稿导出（骨架）
用法：python3 jianying_export.py --video ../example_2min/output/final_video_2min.mp4 --storyboard ../example_2min/storyboard.json --out ../example_2min/draft_content.json
说明：剪映 draft_content.json 的完整结构随剪映版本变化，
  本骨架只输出“素材 + 时间轴 + 字幕文本”的最小可用结构，
  导入前先在剪映里建一个空工程备份，再替换草稿文件验证。
  字幕本身由剪映智能字幕识别生成，这里只提供对轴用的台词文本。
"""
import argparse, json

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    with open(args.storyboard, encoding="utf-8") as f:
        data = json.load(f)
    t = 0.0
    tracks = []
    for s in data["shots"]:
        tracks.append({
            "shot_id": s["shot_id"],
            "start_sec": round(t, 2),
            "duration_sec": s["duration"],
            "text": s["voiceover_text"],
        })
        t += s["duration"]
    draft = {
        "note": "Jianying draft skeleton — verify against your CapCut/Jianying version before use.",
        "video": args.video,
        "canvas": {"width": 1080, "height": 1920, "fps": 30},
        "tracks": tracks,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)
    print(f"写好 {args.out}：{len(tracks)} 条字幕对轴记录")

if __name__ == "__main__":
    main()
