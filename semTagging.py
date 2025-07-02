import os
import csv

# 설정
semantic_csv = "semantic_score.csv"
manifest_dir = "/usr/local/nginx/html/stream/hls"
levels = {
    "index_0.m3u8": 0,  # 240p
    "index_1.m3u8": 1,  # 720p
    "index_2.m3u8": 2,  # 1080p
}

# semantic score 불러오기
semantic_map = {}
with open(semantic_csv, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        chunk_id = int(row["chunk_id"])
        score = float(row["semantic_score"])
        semantic_map[chunk_id] = score

# 태그 삽입하기(IMPORTANCE, NEXT-IMPORTANCE)
for filename, level in levels.items():
    input_path = os.path.join(manifest_dir, filename)
    output_path = os.path.join(manifest_dir, filename.replace(".m3u8", "_tagged.m3u8"))
    print(f"[▶] Processing {filename} → {os.path.basename(output_path)}")

    with open(input_path, "r") as fin, open(output_path, "w") as fout:
        lines = fin.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            fout.write(line + "\n")

            if line.startswith("#EXTINF"):
                next_line = lines[i + 1].strip()
                ts_name = next_line.split("/")[-1]

                try:
                    chunk_id = int(ts_name.split("-")[-1].split(".")[0])  # e.g., stream-1-012.ts → 12
                    score = semantic_map.get(chunk_id, 0.0)
                    next_score = semantic_map.get(chunk_id + 1, 0.0)
                except:
                    score = 0.0
                    next_score = 0.0

                fout.write(f"#EXT-X-IMPORTANCE:{score:.4f}\n")
                fout.write(f"#EXT-X-NEXT-IMPORTANCE:{next_score:.4f}\n")
                fout.write(next_line + "\n")
                i += 1
            i += 1

    print(f"[▶] Complete tagging playlist manifest!: {output_path}")

# master_tagged.m3u8 생성
master_output = os.path.join(manifest_dir, "master_tagged.m3u8")
level_configs = {
    0: {"bandwidth": 500000, "resolution": "426x240"},
    1: {"bandwidth": 2000000, "resolution": "1280x720"},
    2: {"bandwidth": 4000000, "resolution": "1920x1080"},
}

with open(master_output, "w") as f:
    f.write("#EXTM3U\n")
    f.write("#EXT-X-VERSION:3\n")

    for filename, level in levels.items():
        tagged_filename = filename.replace(".m3u8", "_tagged.m3u8")
        cfg = level_configs.get(level, {})
        if not cfg:
            continue
        f.write(f'#EXT-X-STREAM-INF:BANDWIDTH={cfg["bandwidth"]},RESOLUTION={cfg["resolution"]}\n')
        f.write(f"{tagged_filename}\n")

print(f"[▶] Complete creating master manifest!: {master_output}")
