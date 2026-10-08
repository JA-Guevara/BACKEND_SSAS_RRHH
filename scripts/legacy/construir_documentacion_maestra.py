import json
import os
import re
from pathlib import Path

# Paths
root_dir = Path(__file__).resolve().parent.parent.parent
docs_dir = root_dir / "docs"
docs_dir.mkdir(exist_ok=True)

backend_dir = root_dir / "backend_ssas_rrhh"
frontend_dir = root_dir / "frontend_ssas_rrhh" / "src"

# Load OpenAPI dump
with open(backend_dir / "openapi_dump.json", "r", encoding="utf-8") as f:
    spec = json.load(f)

# Load existing 02 for metadata (ID, PA/CU, scope, permissions)
text_02 = (backend_dir / "docs" / "02_API_ENDPOINTS.md").read_text(encoding="utf-8")

# Extract metadata per endpoint from 02
metadata_02 = {}
current_id = None
current_method = None
current_path = None
current_block = []

lines_02 = text_02.splitlines()
for line in lines_02:
    m = re.match(r"^##\s+\[(API-[A-Z0-9]+)\]\s+([A-Z]+)\s+`([^`]+)`", line)
    if m:
        if current_id and current_method and current_path:
            metadata_02[(current_method, current_path)] = {
                "id": current_id,
                "block": "\n".join(current_block)
            }
        current_id = m.group(1)
        current_method = m.group(2)
        current_path = m.group(3)
        current_block = [line]
    elif current_id:
        current_block.append(line)

if current_id and current_method and current_path:
    metadata_02[(current_method, current_path)] = {
        "id": current_id,
        "block": "\n".join(current_block)
    }

print(f"Extracted metadata for {len(metadata_02)} operations from 02_API_ENDPOINTS.md")
