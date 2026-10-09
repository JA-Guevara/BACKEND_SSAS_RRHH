import io

from PIL import Image

from ssas.platform.infrastructure.storage.logo_storage import (
    _is_svg,
    _sanitize_svg,
    delete_logo_file,
    get_logo_path,
    process_and_save_logo,
)


def test_svg_sanitization_removes_dangerous_elements():
    malicious_svg = b'''<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)">
        <script>alert('xss')</script>
        <circle cx="50" cy="50" r="40" onclick="evil()" stroke="green" fill="yellow" />
    </svg>'''
    assert _is_svg(malicious_svg)
    clean = _sanitize_svg(malicious_svg)
    clean_str = clean.decode("utf-8")
    assert "<script" not in clean_str
    assert "onload" not in clean_str
    assert "onclick" not in clean_str
    assert "circle" in clean_str


def test_process_and_save_logo_raster():
    img = Image.new("RGBA", (800, 600), (255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    content = buf.getvalue()

    empresa_id = "test-empresa-123"
    url = process_and_save_logo(empresa_id, content)
    assert url == f"/api/v1/empresas/{empresa_id}/logo"

    res = get_logo_path(empresa_id)
    assert res is not None
    path, mime = res
    assert mime == "image/png"
    assert path.is_file()

    # Clean up
    delete_logo_file(empresa_id)
    assert get_logo_path(empresa_id) is None
