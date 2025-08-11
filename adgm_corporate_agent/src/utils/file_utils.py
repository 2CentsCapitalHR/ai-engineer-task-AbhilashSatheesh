import json
import os
import zipfile
from typing import List


def ensure_directories(paths: List[str]) -> None:
    for p in paths:
        os.makedirs(p, exist_ok=True)


def save_json_pretty(data, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def zip_files(file_paths: List[str], zip_path: str) -> None:
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for fp in file_paths:
            if os.path.exists(fp):
                z.write(fp, arcname=os.path.basename(fp))


