# AI Video Pipeline — 2分钟长视频全免费端到端工作流

目标：100% 全免费，2 分钟左右（100-150 秒）长视频，拆成 15-22 个 4-6 秒分镜，先配音再对画面，最后本地 FFmpeg 拼接。

## 目录

- `pipeline_dag.json` — 7 个节点的拓扑与数据传递配置（DAG）
- `scripts/split_storyboard.py` — Node 1+2：剧本 → storyboard.json
- `scripts/tts_edge.py` — Node 4：edge-tts 配音，输出 shot_XX.mp3 + durations.json
- `scripts/prompt_adapter.py` — Node 5：Kling / 即梦 / MiniMax 提示词编译
- `scripts/stitch_ffmpeg.py` — Node 6：FFmpeg 统一转码 + 拼接 + 混音
- `scripts/jianying_export.py` — Node 7：剪映草稿骨架 draft_content.json
- `example_2min/` — 完整 2 分钟示例：剧本 + storyboard.json

## 跑一遍（示例）

```bash
cd ~/workspace/ai-video-pipeline
pip install edge-tts
python3 scripts/split_storyboard.py --script example_2min/script.md --out example_2min/storyboard.json --shots 20
python3 scripts/tts_edge.py --storyboard example_2min/storyboard.json --out example_2min/assets/audios
# Node 3/5：按 storyboard.json + prompts 生成关键帧和视频片段，放到 example_2min/assets/videos/shot_XX.mp4
python3 scripts/prompt_adapter.py --storyboard example_2min/storyboard.json --out example_2min/prompts
python3 scripts/stitch_ffmpeg.py --videos example_2min/assets/videos --audios example_2min/assets/audios --out example_2min/output/final_video_2min.mp4
python3 scripts/jianying_export.py --video example_2min/output/final_video_2min.mp4 --storyboard example_2min/storyboard.json --out example_2min/draft_content.json
```

## 硬性约束（别绕过）

1. 2 分钟视频严禁单次整片生成，必须拆 15-22 个 4-6 秒分镜。
2. 先锁定人物/产品参考图，再走图生视频 I2V / 带参考 R2V，保证主体一致。
3. 先生成 TTS 配音，按音频实际毫秒时长反向校准视频时间线。
4. 全免费：开源 + 本地 + 每日免费额度，禁止付费 API。Kling / 即梦 / MiniMax 的免费额度以官网为准，会变。
5. AI 画面只当 B-roll / 氛围镜头，不当实拍；发布时勾选 AI 生成；屏幕、笔记本上的文字要虚化，别留乱码和假数据。

## GitHub 说明（2026-11-23 核查，已推送）

仓库：`fanpeter853-glitch/ai-video-pipeline`（Public，main 分支）
https://github.com/fanpeter853-glitch/ai-video-pipeline

主示例是 Peter 的真实版：`example_2min/`（“先做最小的一步”，462 字、20 镜、瓷砖胶客户问价）。
通用备选示例保留在仓库里：`example_2min/sample_script_2min.md` 和 `sample_storyboard.json`
（“磨刀不误砍柴工”主题，18 镜），不要和主示例混用。

字段统一：分镜台词同时写 `voiceover_text` 和 `voiceover` 两个字段，
本地脚本用 `voiceover_text`，仓库另一套编号脚本用 `voiceover`，两者内容一致。

## 连续性硬性要求（2026-11-24，Peter 明确要求）

每条视频只锁定一个场景，除非剧本明确写了换时间/换地点，否则全片不换场景、
不换机位、不换光线、不换衣服。每段的首尾帧必须配合好，拼起来要像一个连续镜头。

- 生成方法：上一段的最后一帧，就是下一段的首帧参考图；每段动作幅度要小，
  慢动作、镜头几乎不动，结尾姿势和下一段开头姿势一致。
- `scripts/anchor_muse.py` 已改：每条提示词带 `scene`（单场景锁定）、`prev_shot`、
  `continuity` 字段，第 2 镜起都写明“以上一镜最后一帧为首帧”。
- 检查方法：`python3 scripts/check_continuity.py --videos example_2min/assets/videos --out example_2min/output/continuity_check.jpg`
  抽每段首帧和尾帧拼成接缝对照图，人工看人物位置、姿势、衣服、桌面、光线、机位
  有没有跳变；有跳变的段只重生成那一段，用上一段尾帧当参考图。
- 实测提醒（2026-11-24 验 2 分钟示例 1-12 镜）：这 12 镜是在加这条要求之前生成的，
  接缝并不顺滑——机位在特写/正面/全景之间跳，光线夜晚和白天混用，个别镜还出现
  了办公室场景和路人，半框眼镜也时有时无。光改提示词不够，下次生成必须按
  “尾帧当首帧参考图”逐段链式生成，生成完先跑 check_continuity 再拼。

## 首帧锁定法 v2（2026-11-24，主号 6 段实测，Peter 确认采用）

问题：只靠“上一段尾帧当参考图”不够，6 段拼起来接缝还是卡——静帧对上
了，动起来每段会重新起动作，3-4 夜晚到白天跳变、4-5 机位从近景切侧面最明显。

改法（已写进 `scripts/anchor_muse.py`，每条提示词都带）：
1. 每段只传上一段的尾帧图当首帧参考，**不用 snapshot 链式续生成**——snapshot
   会把旧视频上下文带进来，反而让机位构图漂移。
2. 首帧必须和给的图一模一样，先定住 1 秒再动；机位锁死为右侧中近景三脚架
   固定机位，镜头不动、角度构图不变，动作放慢放小。
3. 尾帧用 `scripts/extract_frames.py` 从已生成的视频里抽
   （`ffmpeg -sseof -0.5`），不要凭记忆描述上一段结尾。
4. 验接缝用 `scripts/check_continuity.py`（抽首尾帧拼对照图）；
   拼合用 `scripts/stitch_xfade.py`（0.5 秒交叉淡化 + 模糊背景填充到
   1080×1920 + 全部静音），总长 60 秒变 57.5 秒。

实测（主号“先做最小的一步”v2，2026-11-24）：1-2、3-4、4-5、5-6 接缝基本是
同一帧接着拍；2-3 头低了一点，第 4 段内部自己从夜晚近景漂到了白天宽景。
天花板要说清楚：生成模型每次都会重新理解首帧图，保证不了像素级完美，
剪辑里定帧 / 交叉淡化才能兜底。另注意：v2 的 6 段出来都是 944×960
近正方形，不是 720×1280 竖屏，拼竖屏得用模糊背景填充或裁。

## Node 1 补齐：写剧本（2026-11-24 新增）

原来 Node 1 只有拆分镜，不会写剧本。已加 `scripts/write_script.py`：

```bash
python3 scripts/write_script.py --topic "先做最小的一步" \
  --hook "晚上十一点，客户问我，瓷砖胶多少钱一袋，我盯着屏幕三分钟，没敢回" \
  --pain "成本还没对齐，怕说错一个数就丢了客户，不是缺准备，是怕丢脸" \
  --method "拆成最小的一步，先回一句话，明天给准确价格；第二天问工厂拿真实成本，第三天报价" \
  --golden "创业不是等准备好，是先把最小的一步做出来" \
  --cta "你现在最不敢做的那一步是什么，评论区告诉我" \
  --out example_2min/script.md
```

它按 A+B 路线和固定节拍拼成 400~500 字、带时间轴的草稿，自动数字数，
不够或超了会提示。注意：它只做结构拼接和字数校验，不编数字和经历，
没给的内容留 `[待填]`；写完读一遍改口语，再跑 Node 2 拆分镜。
想让 Muse 直接帮你写一版，在聊天里说一声就行。

## Node 4 正式版：VoiceStudio 本地克隆配音（2026-11-24 接入，Peter 确认）

VoiceStudio 是开源本地版 ElevenLabs（`debpalash/VoiceStudio`，AGPL-3.0），
免费、无账号、无订阅，全部在自己电脑上跑，是 Node 4 的首选。

先在你自己的电脑上做一次：

1. 装 VoiceStudio：去 [最新 release](https://github.com/debpalash/VoiceStudio/releases/latest)
   下 Windows MSI / macOS DMG / Linux AppImage；或 Docker
   `docker run -d -p 127.0.0.1:3900:3900 -v omnivoice-data:/app/omnivoice_data --name voicestudio palashdeb/omnivoice-studio:stable`
2. 打开 VoiceStudio → Voice cloning，录一段 5~15 秒干净的你自己的声音，
   建一个声音档案，记下名字，比如 `Peter`。只克隆你自己的声音。
3. 中文优先选 CosyVoice 3 引擎；默认引擎 OmniVoice 也能用。
4. 启动后确认 `http://localhost:3900` 能打开。

然后跑：

```bash
python3 scripts/tts_voicestudio.py --storyboard example_2min/storyboard.json \
  --out example_2min/assets/audios --voice Peter --model cosyvoice3
```

它调本地 OpenAI 兼容接口 `POST http://localhost:3900/v1/audio/speech`，
每镜出 `shot_XX.mp3`，再写 `durations.json`。edge-tts 和 Muse 自带配音降为备选。

## 替换说明（2026-11-24，Node 3 和 Node 4 已替换，实测通过）

- **Node 3 视觉锚点**：原方案 Liblib / Bing DALL·E 3 / 即梦手动生关键帧，
  已替换为 `scripts/anchor_muse.py`。它按分镜生成 20 条统一锚点提示词
  （Peter 本人照片、灰色休闲卫衣、宿舍书桌、写实 B-roll、无字幕、屏幕虚化），
  输出 `example_2min/assets/anchor_prompts.json`；Muse 按提示词逐镜生成竖屏视频，
  放到 `example_2min/assets/videos/shot_XX.mp4`。
- **Node 4 配音**：原方案 edge-tts（zh-CN-YunxiNeural）在虚拟机里连不上
  `speech.platform.bing.com`（SSL 报错），已替换为 `scripts/tts_muse.py`
  （Muse 自带配音，接口与 `tts_edge.py` 一致，同样输出 `shot_XX.mp3` 和
  `durations.json`）。实测：20 段，总 96.6 秒。要 Yunxi 音色，在自己电脑上跑
  `tts_edge.py`；Peter 自己配音优先，录好后用 `tts_muse.py --probe-only`
  生成 `durations.json`。
