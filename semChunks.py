# 사용법: python3 semChunks.py detection.mp4

import os
import sys
import subprocess

INPUT_VIDEO = sys.argv[1]
OUTPUT_DIR = "/usr/local/nginx/html/stream/hls"
DURATION = 170  # 초 단위 (2분 50초), Trace 적용하여 실험하기 위해 170으로 맞춤

# ▶ Step 0: 출력 폴더 생성
if not os.path.exists(OUTPUT_DIR):
    print(f"[▶] Output directory does not exist. Creating: {OUTPUT_DIR}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# ▶ Step 1: 기존 HLS 파일 삭제
print("[▶] Step 1: Removing old HLS chunks and playlists...")
for f in os.listdir(OUTPUT_DIR):
    if f.endswith(".ts") or f.endswith(".m3u8"):
        os.remove(os.path.join(OUTPUT_DIR, f))

# ▶ Step 2: FFmpeg 명령어 실행
print(f"[▶] Step 2: Generating HLS chunks from {INPUT_VIDEO}")

ffmpeg_cmd = [
    "ffmpeg",
    "-i", INPUT_VIDEO,
    "-t", str(DURATION),
    "-async", "1",
    "-map", "0:v:0", "-map", "0:v:0", "-map", "0:v:0",
    "-c:v", "libx264",
    "-preset", "fast",
    "-sc_threshold", "0",
    "-g", "30",
    "-keyint_min", "30",
    "-force_key_frames", "expr:gte(t,n_forced*1)",
    "-b:v:0", "500k", "-s:v:0", "426x240", "-profile:v:0", "baseline",
    "-b:v:1", "2000k", "-s:v:1", "1280x720", "-profile:v:1", "main",
    "-b:v:2", "4000k", "-s:v:2", "1920x1080", "-profile:v:2", "high",
    "-f", "hls",
    "-hls_time", "1",
    "-hls_list_size", "0",
    "-hls_flags", "independent_segments",
    "-hls_playlist_type", "event",
    "-hls_segment_filename", f"{OUTPUT_DIR}/stream-%v-%03d.ts",
    "-var_stream_map", "v:0 v:1 v:2",
    "-master_pl_name", "master.m3u8",
    "-master_pl_publish_rate", "10",
    f"{OUTPUT_DIR}/index_%v.m3u8"
]

result = subprocess.run(ffmpeg_cmd)
if result.returncode != 0:
    print("[✖] FFmpeg failed.")
    sys.exit(1)

print("[▶] Step 3: HLS generation complete.")

# ▶ Step 4: 시맨틱 중요도 계산
print("[▶] Step 4: Scoring CLIP based semantic importance (semScoring.py)")
subprocess.run(["python3", "semScoring.py"])

# ▶ Step 5: manifest importance 태깅
print("[▶] Step 5: Tagging importance score to manifest files (tagging.py)")
subprocess.run(["python3", "tagging.py"])

print("[▶] Complete!")
