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
  - 首帧锁定法 v2（2026-11-24，主号 6 段实测，Peter 确认采用）：
    每段只拿上一段的尾帧图当首帧参考，不用 snapshot 链式续生成——
    snapshot 会把旧视频的上下文带进来，反而让机位和构图漂移。
    每段提示词必须写：首帧和给的图一模一样，先定住 1 秒再动；
    机位锁死为右侧中近景三脚架固定机位，镜头不动、角度构图不变，
    动作放慢放小。尾帧用 scripts/extract_frames.py 从已生成的视频里抽
    （ffmpeg -sseof -0.5），不要凭记忆描述上一段结尾。
    实测：v2 的 1-2、3-4、4-5、5-6 接缝基本是同一帧接着拍；
    仍有天花板：生成模型每次都会重新理解首帧图，保证不了像素级完美，
    2-3 接缝头低了一点，第 4 段内部自己从夜晚近景漂到了白天宽景。
    剪辑里再加 0.5 秒定帧 / 交叉淡化（scripts/stitch_xfade.py）才能兜底。
"""
import argparse, json

ANCHOR = (
    "人物锚点：以 Peter 选定的真人参考图为准（media-generation-real-person-half-frame-glasses-0-e7bf054a，"
    "细金属半框眼镜，灰色休闲卫衣，宿舍书桌），19岁大二男生，戴半框眼镜，灰色休闲卫衣，"
    "宿舍书桌，写实电影感，自然光。画面为 B-roll，不对镜说话，无台词，"
    "无屏幕字幕，屏幕和笔记本上的字虚化，不留乱码和假数据。"
)

# 首帧锁定法 v2（2026-11-24，主号 6 段实测，Peter 确认采用）：
# 首帧必须和给的图一模一样，先定住 1 秒再动；机位锁死为右侧中近景
# 三脚架固定机位，镜头不动、角度构图不变，动作放慢放小。
FRAME_LOCK_CN = (
    "首帧锁定：本镜首帧必须和给的首帧图一模一样，构图、人物、桌面、光线"
    "都不许变，先定住 1 秒再动。机位锁死为右侧中近景三脚架固定机位，"
    "镜头不动、角度构图不变，动作放慢放小。"
)
FRAME_LOCK_EN = (
    "First-frame lock: the first frame of this video must be exactly the given image, "
    "pixel for pixel, do not change the framing, person, desk or lighting in the first frame. "
    "Hold this exact frame still for the first second. Locked-off tripod, fixed medium "
    "close-up from his right side, camera never moves, angle and framing never change. "
    "Move very slowly and very little."
)
# 每条视频只锁定一个场景，除非剧本明确写了换时间/换地点，否则全片不换场景、
# 不换机位、不换光线。每段的首尾帧必须配合好，拼起来要像一个连续镜头。
# 生成方法：上一段的最后一帧，就是下一段的首帧参考图；每段动作幅度要小，
# 慢动作、镜头几乎不动，结尾姿势和下一段开头姿势一致。
SCENE_LOCK = (
    "场景锁定：整条视频只在一个场景里，宿舍书桌，同一机位、同一角度、同一光线，"
    "不换场景、不跳时间、不换衣服。动作要小、要慢，镜头几乎不动。"
)
CONTINUITY = (
    "连续性：本镜以上一镜的最后一帧为首帧，人物位置、姿势、衣服、桌面物品、"
    "光线和上一镜结尾完全一致，像同一个镜头接着拍下去，不要重新开场。"
)

def main(args):
    with open(args.storyboard, encoding="utf-8") as f:
        data = json.load(f)
    prompts = []
    for i, shot in enumerate(data["shots"]):
        text = shot.get("voiceover_text") or shot.get("voiceover", "")
        continuity = CONTINUITY if i > 0 else "开场镜：确立场景、人物位置和机位，后面所有镜都以这一镜为准，不再变。"
        prev = f"上一镜：shot_{i:02d}。" if i > 0 else ""
        if i == 0:
            first_frame_source = "真人参考图 media-generation-real-person-half-frame-glasses-0-e7bf054a（Peter 选定）"
            first_frame_cn = "首帧锁定：本镜首帧按真人参考图开场，确立机位和场景。"
            first_frame_en = "First frame establishes the scene from the reference photo."
        else:
            first_frame_source = (
                f"上一镜 shot_{i:02d} 的尾帧 clip{i:02d}_last.jpg，"
                "用 scripts/extract_frames.py 从已生成的视频里抽（ffmpeg -sseof -0.5）"
            )
            first_frame_cn = FRAME_LOCK_CN
            first_frame_en = FRAME_LOCK_EN
        prompts.append({
            "shot_id": shot["shot_id"],
            "duration_s": shot["duration"],
            "scene": "宿舍书桌（单场景锁定）",
            "prev_shot": f"shot_{i:02d}" if i > 0 else None,
            "first_frame_source": first_frame_source,
            "generation_method": "首帧锁定法 v2：只传上一段尾帧图当首帧参考，不用 snapshot 链式续生成",
            "continuity": continuity,
            "voiceover_text": text,
            "visual_prompt_cn": (
                f"{ANCHOR} {SCENE_LOCK} {first_frame_cn} {continuity} {prev}"
                f"本镜台词：{text}。"
                "竖屏 9:16，约 10 秒一段，画面与台词相符，真实自然。"
            ),
            "visual_prompt_en": (
                "Photorealistic vertical 9:16 B-roll, half-rim glasses, casual grey hoodie, dorm desk, "
                "natural light, no dialogue, no on-screen text, screens blurred. "
                "Single locked scene, same camera angle and lighting throughout. "
                f"{first_frame_en} "
                "Continue exactly from the previous clip's last frame, same position and pose, "
                "small slow motion, no scene jump. "
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
