#!/usr/bin/env python3
"""Node 3 替换版：Muse 自带视觉锚点（代替 Liblib / Bing DALL·E 3 / 即梦手动生关键帧）
用法：
  python3 anchor_muse.py --storyboard ../example_2min/storyboard.json --out ../example_2min/assets/anchor_prompts.json
说明：
  - Node 3 本来是手动步：先定一张人物参考图，再生静态关键帧图。
    本脚本把这一步变成可执行的提示词清单：每镜一条写实 B-roll 提示词，
    统一锚点写死在 ANCHOR 里，Muse 按提示词逐镜生成视频（每段约 10 秒，
    一次最多 6 段，竖屏 9:16），不用再去外部工具。
  - 生成规则（已在 60 秒主号视频上验证过）：
    人物用 Peter 本人照片作参考，灰色休闲卫衣（不要西装），宿舍书桌，
    写实风，B-roll 不对镜说话，无台词，无屏幕字幕，屏幕和笔记本上的字虚化，
    不留乱码和假数据；画面只当 B-roll，发布时勾选 AI 生成。
  - 输出的 anchor_prompts.json 每条含 shot_id、duration_s（取自配音实测时长，
    没有实测时用分镜标称时长）、visual_prompt_cn、visual_prompt_en。
  - 视频生成本身由 Muse 的媒体工具执行，不在本脚本里调 API；
    拿到视频后按 shot_XX.mp4 放到 example_2min/assets/videos/，再跑 Node 6。
"""
import argparse, json

ANCHOR = (
    "人物锚点：以 Peter 本人照片为准，19岁大二男生，灰色休闲卫衣，"
    "宿舍书桌，写实电影感，自然光。画面为 B-roll，不对镜说话，无台词，"
    "无屏幕字幕，屏幕和笔记本上的字虚化，不留乱码和假数据。"
)

def main(args):
    with open(args.storyboard, encoding="utf-8") as f:
        data = json.load(f)
    prompts = []
    for shot in data["shots"]:
        text = shot.get("voiceover_text") or shot.get("voiceover", "")
        prompts.append({
            "shot_id": shot["shot_id"],
            "duration_s": shot["duration"],
            "voiceover_text": text,
            "visual_prompt_cn": (
                f"{ANCHOR} 本镜台词：{text}。"
                "竖屏 9:16，约 10 秒一段，画面与台词相符，真实自然。"
            ),
            "visual_prompt_en": (
                "Photorealistic vertical 9:16 B-roll, casual grey hoodie, dorm desk, "
                "natural light, no dialogue, no on-screen text, screens blurred. "
                f"Scene matches: {text}"
            ),
        })
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"anchor": ANCHOR, "prompts": prompts}, f, ensure_ascii=False, indent=2)
    print(f"写好 {args.out}：{len(prompts)} 条锚点提示词")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    main(args)
