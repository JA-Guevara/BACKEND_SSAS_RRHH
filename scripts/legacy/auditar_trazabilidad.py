import json
import os
import re
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
frontend_dir = backend_dir.parent / "frontend_ssas_rrhh" / "src"

with open(backend_dir / "openapi_dump.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

backend_ops = []
for path, ops in schema["paths"].items():
    for method, op in ops.items():
        if method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            backend_ops.append({
                "method": method.upper(),
                "path": path,
                "summary": op.get("summary", ""),
                "tags": op.get("tags", ["General"]),
                "operation_id": op.get("operationId", "")
            })

fe_files = [
    f for f in (list(frontend_dir.glob("**/*.ts")) + list(frontend_dir.glob("**/*.tsx")))
    if "schema.d.ts" not in f.name
]

def find_refs(path):
    # build pattern
    tokens = path.split("/")
    pattern_tokens = []
    for token in tokens:
        if token.startswith("{") and token.endswith("}"):
            pattern_tokens.append(r"(\$\{[^}]+\}|[^/\"`\?]+)")
        elif token:
            pattern_tokens.append(re.escape(token))
        else:
            pattern_tokens.append("")
    pattern = "/".join(pattern_tokens)
    pat = re.compile(pattern)

    refs = []
    for f in fe_files:
        content = f.read_text(encoding="utf-8")
        if pat.search(content):
            refs.append(str(f.relative_to(frontend_dir.parent)).replace("\\", "/"))
    return refs

used = []
unused = []

for op in backend_ops:
    refs = find_refs(op["path"])
    if refs:
        used.append({"op": op, "refs": refs})
    else:
        unused.append(op)

print(f"=== RESULTADOS DE AUDITORÍA REAL DE TRAZABILIDAD ===")
print(f"Total endpoints backend: {len(backend_ops)}")
print(f"Endpoints con llamadas en frontend: {len(used)}")
print(f"Endpoints sin llamadas directas en frontend: {len(unused)}")

print("\n--- Endpoints conectados en frontend ---")
for item in used:
    op = item["op"]
    print(f"  [OK] {op['method']:6} {op['path']:50} -> {item['refs'][0]}")

print("\n--- Endpoints pendientes o sin UI en frontend ---")
for op in unused:
    print(f"  [PENDIENTE] {op['method']:6} {op['path']:50} [{op['tags'][0]}] ({op['summary']})")
