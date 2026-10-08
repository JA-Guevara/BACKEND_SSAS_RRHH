import re
from pathlib import Path

src_dir = Path(r"d:\Uagrm\2 - 2026\Sistemas de Informacion II\Proyecto Princial\frontend_ssas_rrhh\src")

api_files = list((src_dir / "features").glob("**/api/*Api.ts"))
ui_files = list(src_dir.glob("**/*.tsx"))

api_exports = {} # filename -> list of exported functions / methods

for af in api_files:
    content = af.read_text(encoding="utf-8")
    funcs = set()
    # match export function xxx
    for m in re.finditer(r"export\s+function\s+([a-zA-Z0-9_]+)", content):
        funcs.add(m.group(1))
    # match export async function xxx
    for m in re.finditer(r"export\s+async\s+function\s+([a-zA-Z0-9_]+)", content):
        funcs.add(m.group(1))
    # match export const xxxApi = { method: ... }
    m_obj = re.search(r"export\s+const\s+([a-zA-Z0-9_]+Api)\s*=\s*\{([^}]+)\}", content, re.DOTALL)
    if m_obj:
        obj_name = m_obj.group(1)
        body = m_obj.group(2)
        for line in body.splitlines():
            line = line.strip()
            m_meth = re.match(r"^([a-zA-Z0-9_]+)\s*:\s*", line)
            if m_meth:
                funcs.add(f"{obj_name}.{m_meth.group(1)}")
    
    api_exports[af.name] = funcs

print("=== VERIFICACIÓN DE USO REAL DE FUNCIONES API EN COMPONENTES UI (TSX) ===")

ui_contents = {u.name: u.read_text(encoding="utf-8") for u in ui_files}

for api_file, funcs in sorted(api_exports.items()):
    print(f"\n--- {api_file} ---")
    for f in sorted(funcs):
        token = f.split(".")[-1]
        used_in = [uname for uname, ucontent in ui_contents.items() if re.search(rf"\b{token}\b", ucontent)]
        status = f"USADO en {', '.join(used_in[:3])}" if used_in else "SIN CONSUMO EN UI (Solo definido en API)"
        print(f"  {f:35} -> {status}")
