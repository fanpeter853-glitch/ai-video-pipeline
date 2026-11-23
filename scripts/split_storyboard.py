#!/usr/bin/env python3
"""Node 1 + Node 2：剧本 -> 结构化分镜 storyboard.json
用法：
  python3 split_storyboard.py --script ../example_2min/script.md --out ../example_2min/storyboard.json
规则：
  - 输入是按节拍分段的剧本（每段一行，格式：[00:00-00:05] 台词）
  - 输出 16-20 个分镜，每个 4-6 秒，字段与 pipeline_dag.json 一致
  - 本脚本是骨架：节拍切分靠人工标段，运镜/景别用模板轮换，正式用时按内容微调
"""
import argparse, json, re

# 景别 / 运镜模板轮换，避免全片一个机位
SCENE_TYPES = ["特写", "近景", "中景", "近景", "中景", "特写"]
CAMERA_MOTIONS = ["推", "静止", "摇", "移", "推", "升降"]

def parse_script(path):
    """读剧本，返回 [(start, end, text)]，时间格式 mm:ss"""
    beats = []
    pat = re.compile(r"\[(\d{2}:\d{2})-(\d{2}:\d{2})\]\s*(.+)")
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = pat.match(line)
            if m:
                beats.append((m.group(1), m.group(2), m.group(3)))
    return beats

def to_sec(t):
    m, s = map(int, t.split(":"))
    return m * 60 + s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--shots", type=int, default=18)
    args = ap.parse_args()

    beats = parse_script(args.script)
    if not beats:
        raise SystemExit("剧本里没找到 [mm:ss-mm:ss] 台词行，先按模板分段。")

    # 把全部台词按字数均分到目标分镜数，每镜 4-6 秒
    # 注意：按标点断句累积，绝不在词中间切断（旧版按字符硬切会出“幕三分钟”这种断词）
    full = "".join(t for _, _, t in beats)
    total_sec = to_sec(beats[-1][1]) - to_sec(beats[0][0])
    per_shot_chars = max(1, len(full) // args.shots)
    # 先按句号/逗号断成小句，保留标点
    clauses = re.findall(r"[^，。]+[，。]?", full)

    shot_texts = []
    cur = ""
    for clause in clauses:
        if cur and len(cur) + len(clause) > per_shot_chars:
            shot_texts.append(cur)
            cur = clause
        else:
            cur += clause
    if cur:
        shot_texts.append(cur)
    # 超出目标数时，合并最短的相邻两段，而不是把多余的都堆到最后一段
    while len(shot_texts) > args.shots:
        i = min(range(len(shot_texts) - 1), key=lambda k: len(shot_texts[k]) + len(shot_texts[k + 1]))
        shot_texts[i] += shot_texts[i + 1]
        shot_texts.pop(i + 1)

    shots = []
    for i, text in enumerate(shot_texts):
        if not text:
            continue
        dur = max(4, min(6, round(total_sec / args.shots)))
        shots.append({
            "shot_id": f"shot_{i+1:02d}",
            "duration": dur,
            "scene_type": SCENE_TYPES[i % len(SCENE_TYPES)],
            "camera_motion": CAMERA_MOTIONS[i % len(CAMERA_MOTIONS)],
            "visual_prompt": f"Realistic dorm desk scene, 19-year-old Chinese university student in casual grey hoodie, natural light, vertical 9:16. / 写实宿舍书桌，19岁大二男生灰色卫衣，自然光，竖屏。",
            "visual_prompt_cn": "写实宿舍书桌，19岁大二男生，灰色卫衣，自然光，竖屏9:16",
            "voiceover_text": text,
        })

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"shots": shots, "total_shots": len(shots)}, f, ensure_ascii=False, indent=2)
    print(f"写好 {args.out}：{len(shots)} 个分镜，共 {len(full)} 字")

if __name__ == "__main__":
    main()
