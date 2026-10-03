import json
import sys
from pathlib import Path

from ssas.analisis_cv.domain.analysis import AnalisisCvError
from ssas.analisis_cv.infrastructure.extraction.cv_extractor import extract_file


def main() -> int:
    try:
        text = extract_file(Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
        print(json.dumps({"text": text}))
        return 0
    except AnalisisCvError as exc:
        print(json.dumps({"error": str(exc)}))
    except Exception:  # noqa: BLE001 - parser errors must not leak document content
        print(json.dumps({"error": "El documento CV esta danado o no es valido"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
