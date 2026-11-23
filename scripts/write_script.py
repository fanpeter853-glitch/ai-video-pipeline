#!/usr/bin/env python3
"""Node 1 补齐：剧本起草器（2026-11-24 新增）
原来 Node 1 只有拆分镜，不会写剧本。本脚本把写剧本变成可执行的一步：
你给主题 + 每段节拍的一两句关键点，它按 A+B 路线和固定节拍拼成一版
400~500 字、带 [mm:ss-mm:ss] 时间轴的草稿，写完自动数字数，不够或超了会提示。
用法：
  python3 write_script.py --topic "先做最小的一步" \\
    --hook "晚上十一点，客户问我，瓷砖胶多少钱一袋，我盯着屏幕三分钟，没敢回" \\
    --pain "成本还没对齐，怕说错一个数就丢了客户，不是缺准备，是怕丢脸" \\
    --method "拆成最小的一步，先回一句话，明天给准确价格；第二天问工厂拿真实成本，第三天报价；三条规则：先问工厂要真实成本不自己编数，先给真实回应不装懂，能发的先发再改一版" \\
    --golden "创业不是等准备好，是先把最小的一步做出来" \\
    --cta "你现在最不敢做的那一步是什么，评论区告诉我" \\
    --out ../example_2min/script.md
诚实说明：
  - 这不是让脚本凭空替你创作：它只做结构拼接和字数校验，
    真实细节、你的口语、金句都来自你给的 --hook / --pain / --method，
    没给的内容它不会编数字、编经历，缺了就留 [待填] 让你补。
  - 写完后你读一遍，标出不像你说话的地方再改，改完跑 split_storyboard.py 拆分镜。
  - 想让 Muse 直接帮你写一版，聊天里说一声就行，写完同样存成这个格式。
"""
import argparse, re

BEATS = [
    ("00:00-00:05", "hook", "钩子：具体场景，3 秒留人"),
    ("00:05-00:30", "pain", "痛点：当时怎么卡的，真实感受"),
    ("00:30-01:15", "method", "方法：一个所有人能用的办法 + 你的真实过程"),
    ("01:15-01:45", "golden", "金句 + 迁移：别人卡住时也能用"),
    ("01:45-02:00", "cta", "互动：选择题或开放提问收口"),
]

GOLDEN_BRIDGE = "所以如果你现在也卡住了，别问自己准备好了没有，先问自己，今天能做的最小一步是什么。"

def clean(text):
    return re.sub(r"\s+", " ", (text or "").strip())

def main(args):
    parts = {
        "hook": clean(args.hook),
        "pain": clean(args.pain),
        "method": clean(args.method),
        "golden": clean(args.golden),
        "cta": clean(args.cta),
    }
    # 金句段：如果只给了金句本身，前面补一句迁移桥接
    golden_text = parts["golden"]
    if golden_text and GOLDEN_BRIDGE not in golden_text:
        golden_text = f"{golden_text}。{GOLDEN_BRIDGE}"
    lines = [
        f"# 剧本：{args.topic}（A+B 路线）",
        "",
        f"- 主题：{args.topic}",
        "- 受众：19-22岁想折腾但不敢开始的大学生",
        "- 目标时长：约120秒，语速约240字/分钟",
        "- 下面每行是一个节拍，格式 [开始-结束] 台词，供 split_storyboard.py 解析",
        "",
    ]
    body = {
        "hook": parts["hook"] or "[待填：写一个具体场景，3 秒留人]",
        "pain": parts["pain"] or "[待填：当时怎么卡的，真实感受]",
        "method": parts["method"] or "[待填：一个所有人能用的办法 + 你的真实过程]",
        "golden": golden_text or "[待填：金句 + 迁移]",
        "cta": parts["cta"] or "[待填：选择题或开放提问收口]",
    }
    for ts, key, _label in BEATS:
        lines.append(f"[{ts}] {body[key]}")
    text = "\n".join(lines) + "\n"
    chars = len(re.sub(r"[，。、；：！？,.!?、\s]", "", "\n".join(body.values())))
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"写好 {args.out}：{chars} 字（不含标点），目标 400~500 字")
    if chars < 400:
        print(f"提示：少了 {400 - chars} 字，约 {round((400 - chars) / 4, 1)} 秒，补一点方法或过程再跑。")
    elif chars > 500:
        print(f"提示：多了 {chars - 500} 字，约 {round((chars - 500) / 4, 1)} 秒，删一点再跑。")
    else:
        print(f"字数在目标内，约 {round(chars / 4, 1)} 秒，可直接跑 split_storyboard.py 拆分镜。")
    missing = [k for k, v in parts.items() if not v]
    if missing:
        print("未填的节拍（已留 [待填]）：", "、".join(missing))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True, help="主题，如 先做最小的一步")
    ap.add_argument("--hook", default="")
    ap.add_argument("--pain", default="")
    ap.add_argument("--method", default="")
    ap.add_argument("--golden", default="")
    ap.add_argument("--cta", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    main(args)
