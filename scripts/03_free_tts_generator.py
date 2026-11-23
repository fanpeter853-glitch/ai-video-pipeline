#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_free_tts_generator.py
Uses Microsoft Edge-TTS (100% free, no API key, zero cost) to generate broadcast-grade voiceover audio files.
"""

import json
import argparse
import os
import asyncio
import subprocess

async def generate_shot_audio(text, voice, output_path, rate="+0%", volume="+0%"):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
        await communicate.save(output_path)
        return True
    except ImportError:
        # Fallback to CLI command if package is invoked via subprocess
        cmd = ["edge-tts", "--voice", voice, "--text", text, "--rate", rate, "--volume", volume, "--write-media", output_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0
    except Exception as e:
        print(f"Error generating audio for '{text[:15]}...': {e}")
        return False

async def batch_generate_tts(storyboard_path, output_dir, voice="zh-CN-YunxiNeural", rate="+0%"):
    with open(storyboard_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    shots = data.get("shots", [])
    manifest = []

    print(f"🎙️ Starting Edge-TTS batch generation with voice [{voice}]...")
    for shot in shots:
        shot_id = shot.get("shot_id")
        voiceover = shot.get("voiceover", "").strip()
        if not voiceover:
            continue

        audio_file = os.path.join(output_dir, f"{shot_id}.mp3")
        print(f"  -> Generating {shot_id}: '{voiceover[:20]}...'")
        
        success = await generate_shot_audio(voiceover, voice, audio_file, rate=rate)
        if success and os.path.exists(audio_file):
            manifest.append({
                "shot_id": shot_id,
                "audio_file": audio_file,
                "voiceover": voiceover,
                "status": "ready"
            })
        else:
            print(f"  ❌ Failed to generate {shot_id}")

    manifest_path = os.path.join(output_dir, "audio_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"✅ Generated {len(manifest)} audio files in {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Batch generate free voiceover audio via edge-tts")
    parser.add_argument("--input", "-i", required=True, help="Path to storyboard JSON")
    parser.add_argument("--output-dir", "-o", default="workspace/audios", help="Directory to save MP3s")
    parser.add_argument("--voice", "-v", default="zh-CN-YunxiNeural", help="Edge TTS voice (e.g. zh-CN-YunxiNeural, zh-CN-XiaoxiaoNeural)")
    parser.add_argument("--rate", "-r", default="+0%", help="Speaking speed rate (e.g. +0%, +5%)")
    args = parser.parse_args()

    asyncio.run(batch_generate_tts(args.input, args.output_dir, args.voice, args.rate))

if __name__ == "__main__":
    main()
