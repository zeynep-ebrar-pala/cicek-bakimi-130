import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path.cwd() / "backend"))
from data import PLANTS

asset_files = set(os.listdir("assets"))
db_images = set(p["image"] for p in PLANTS)

missing_in_db = asset_files - db_images - {"custom_flower.png"}
missing_in_assets = db_images - asset_files

print(f"Missing in DB: {missing_in_db}")
print(f"Missing in Assets: {missing_in_assets}")
