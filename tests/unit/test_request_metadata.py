from starlette.requests import Request

from ssas.core.api.request_metadata import get_client_ip


def _request(*, client: str | None = "127.0.0.1", headers: dict[str, str] | None = None):
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [
            (name.lower().encode(), value.encode()) for name, value in (headers or {}).items()
        ],
        "client": (client, 12345) if client is not None else None,
    }
    return Request(scope)


def test_railway_real_ip_has_priority():
    request = _request(
        client="100.64.0.10",
        headers={"X-Real-IP": "200.87.10.20", "X-Forwarded-For": "198.51.100.2"},
    )

    assert get_client_ip(request) == "200.87.10.20"


def test_forwarded_chain_uses_original_client():
    request = _request(headers={"X-Forwarded-For": "203.0.113.8, 100.64.0.2"})

    assert get_client_ip(request) == "203.0.113.8"


def test_invalid_proxy_headers_fall_back_to_socket_client():
    request = _request(client="10.20.30.40", headers={"X-Real-IP": "valor-invalido"})

    assert get_client_ip(request) == "10.20.30.40"


def test_ipv6_with_brackets_and_port_is_normalized():
    request = _request(headers={"X-Real-IP": "[2001:db8::1]:443"})

    assert get_client_ip(request) == "2001:db8::1"


def test_missing_client_information_returns_none():
    assert get_client_ip(_request(client=None)) is None

