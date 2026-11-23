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
