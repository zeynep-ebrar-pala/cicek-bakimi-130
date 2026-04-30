import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path.cwd() / "backend"))
import data

new_plants = []
for plant in data.PLANTS:
    filename_clean = plant["image"].replace(".jpg", "").replace(".png", "").replace("_", " ")
    if filename_clean not in plant["keywords"]:
        plant["keywords"].append(filename_clean)
    new_plants.append(plant)

with open("backend/data.py", "r", encoding="utf-8") as f:
    content = f.read()

# This is a bit risky but we can replace the PLANTS list
# Actually, I'll just output the updated list to a file and then I can view it
import pprint
with open("scratch/updated_plants.py", "w", encoding="utf-8") as f:
    f.write("PLANTS = " + pprint.pformat(new_plants, indent=4, width=120, sort_dicts=False))
