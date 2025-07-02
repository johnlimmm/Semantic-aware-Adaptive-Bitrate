# sudo apt install python3-pip git
# sudo python3 -m pip install --break-system-packages torch torchvision torchaudio opencv-python
# sudo python3 -m pip install --break-system-packages git+https://github.com/openai/CLIP.git

import os
import glob
import torch
import clip
import cv2
import numpy as np
from PIL import Image
import csv
import gc

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

chunk_dir = "/usr/local/nginx/html/stream/hls"
sample_every = 5
res_label = "1080p"
level = "2"  
# 1080p에 해당하는 stream 번호로, 
# 1080p 청크의 semantic score를 모든 manifest파일에 주입하기 위함.

def compute_chunk_importance(frames):
    embeddings = []
    for i, frame in enumerate(frames):
        if i % sample_every != 0:
            continue
        resized = cv2.resize(frame, (224, 224))
        pil_frame = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
        input_tensor = preprocess(pil_frame).unsqueeze(0).to(device)
        with torch.no_grad():
            embedding = model.encode_image(input_tensor).cpu().numpy()
        embeddings.append(embedding[0])
    if not embeddings:
        return 0.0
    embeddings = np.array(embeddings)
    mean_embedding = np.mean(embeddings, axis=0)
    diversity = np.mean(np.linalg.norm(embeddings - mean_embedding, axis=1))
    return diversity

print(f"\n[▶] Processing ...")
pattern = os.path.join(chunk_dir, f"stream-{level}-*.ts")
files = sorted(glob.glob(pattern))

chunk_scores = []
for chunk_id, filepath in enumerate(files):
    cap = cv2.VideoCapture(filepath)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()

    if not frames:
        print(f"[!] Skipping empty: {os.path.basename(filepath)}")
        continue

    score = compute_chunk_importance(frames)
    chunk_scores.append(score)
    print(f"[{res_label}] Chunk {chunk_id}: {score:.4f}")
    gc.collect()

# 점수 정규화
min_score, max_score = min(chunk_scores), max(chunk_scores)
if min_score == max_score:
    normalized = [0.0 for _ in chunk_scores]
else:
    normalized = [(s - min_score) / (max_score - min_score) for s in chunk_scores]

# semantic score 저장
csv_path = f"semantic_score.csv"
with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["chunk_id", "semantic_score"])
    for i, score in enumerate(normalized):
        writer.writerow([i, round(score, 4)])

print(f"[▶] Saved: {csv_path}")