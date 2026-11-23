# AI Video Pipeline (2-Minute Long Video Workflow)

一套专为 **2分钟左右（100s~150s）长视频** 打造的 **100% 全免费、模块化 AI 视频生成工作流**。

支持直接在 **Muse** 或本地通过 Python + FFmpeg 自动化运行，包含剧本创作、分镜拆解、提示词适配、免费广播级配音、音画自动对齐与最终剪辑导出。

---

## 🌟 核心特性

- **100% 零成本闭环**：所有环节均使用开源库（`edge-tts`、`ffmpeg`）或平台每日免费积分（快手可灵、豆包即梦、MiniMax海螺、LiblibAI），无需购买任何付费 API。
- **长视频分治架构**：将 2 分钟长视频精准拆解为 16~20 个 4~6 秒独立镜头，彻底避免单次长生成带来的画面崩坏与动作畸变。
- **音画精准对齐**：先生成毫秒级精度的 TTS 旁白音频，再基于真实音频时长驱动视频拼接与微调。
- **专业级混音标准**：旁白人声自动标准化至 `-14 dB`，背景音乐自动闪避压制至 `-22 dB`。
- **剪映草稿一键导出**：支持输出剪映/CapCut 工程草稿文件，一键自动打智能黄色高亮花字字幕。

---

## 📂 项目结构

```text
ai-video-pipeline/
├── pipeline_dag.json                 # Muse 工作流节点定义与数据流转拓扑
├── README.md                         # 项目使用说明
├── scripts/
│   ├── 01_script_to_storyboard.py    # 剧本快速拆解为分镜 JSON
│   ├── 02_prompt_compiler.py         # 分镜 JSON -> 多模型生图/生视频 Prompt 编译
│   ├── 03_free_tts_generator.py      # 微软 Edge-TTS 免费批量配音脚本
│   ├── 04_ffmpeg_auto_stitch.py      # FFmpeg 自动对齐、混音与成片渲染
│   └── 05_jianying_draft_export.py   # 导出为剪映电脑版草稿
└── example_2min/
    ├── sample_script_2min.md         # 2分钟标准剧本示例（成长与创业认知）
    └── sample_storyboard.json        # 对应 18 镜头的完整结构化分镜表
```

---

## 🚀 快速上手

### 1. 环境准备
确保本机已安装 Python 3.8+ 及 FFmpeg：
```bash
pip install edge-tts
# 检查 ffmpeg
ffmpeg -version
```

### 2. 执行完整流水线

#### Step 1: 拆解分镜
```bash
python scripts/01_script_to_storyboard.py --input example_2min/sample_script_2min.md --output workspace/storyboard.json
```

#### Step 2: 编译生图/生视频提示词
```bash
python scripts/02_prompt_compiler.py --input workspace/storyboard.json --model jimeng
```

#### Step 3: 批量生成免费配音
```bash
python scripts/03_free_tts_generator.py --input workspace/storyboard.json --output-dir workspace/audios/
```

#### Step 4: 自动化剪辑成片
将生成的视频片段放入 `workspace/videos/`，背景音乐放入 `workspace/bgm.mp3`：
```bash
python scripts/04_ffmpeg_auto_stitch.py --storyboard workspace/storyboard.json --video-dir workspace/videos/ --audio-dir workspace/audios/ --bgm workspace/bgm.mp3 --output workspace/final_output.mp4
```

---

## 📄 License
MIT License. Created by [fanpeter853-glitch](https://github.com/fanpeter853-glitch).
