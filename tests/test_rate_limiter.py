"""Unit tests for rate limiter IP extraction."""

from unittest.mock import MagicMock

from starlette.requests import Request

from rivaflow.api.rate_limit import _get_real_client_ip


def _make_request(headers=None, client_host="10.0.0.1"):
    """Create a mock Starlette Request with given headers and client host."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
    }
    if headers:
        scope["headers"] = [
            (k.lower().encode(), v.encode()) for k, v in headers.items()
        ]

    request = Request(scope)

    # Mock the client attribute
    if client_host:
        mock_client = MagicMock()
        mock_client.host = client_host
        request._client = mock_client
        # Starlette accesses scope["client"] for request.client
        scope["client"] = (client_host, 0)
    else:
        scope["client"] = None

    return request


class TestIPExtractionNoForwardedHeader:
    """Tests for IP extraction when no X-Forwarded-For header is present."""

    def test_returns_client_host(self):
        """Should return request.client.host when no forwarding header."""
        request = _make_request(client_host="192.168.1.100")
        ip = _get_real_client_ip(request)
        assert ip == "192.168.1.100"

    def test_returns_localhost_when_no_client(self):
        """Should return 127.0.0.1 when request.client is None."""
        request = _make_request(client_host=None)
        ip = _get_real_client_ip(request)
        assert ip == "127.0.0.1"

    def test_ipv4_client_host(self):
        """Should handle standard IPv4 addresses."""
        request = _make_request(client_host="203.0.113.50")
        ip = _get_real_client_ip(request)
        assert ip == "203.0.113.50"


class TestXForwardedForParsing:
    """Tests for X-Forwarded-For header parsing."""

    def test_single_ip_in_header(self):
        """Single IP in X-Forwarded-For should be returned."""
        request = _make_request(
            headers={"x-forwarded-for": "203.0.113.50"},
            client_host="10.0.0.1",
        )
        ip = _get_real_client_ip(request)
        assert ip == "203.0.113.50"

    def test_multiple_ips_returns_rightmost(self):
        """Should return the rightmost IP (closest trusted proxy)."""
        request = _make_request(
            headers={"x-forwarded-for": "203.0.113.50, 198.51.100.25, 10.0.0.1"},
            client_host="10.0.0.1",
        )
        ip = _get_real_client_ip(request)
        assert ip == "10.0.0.1"

    def test_two_ips_returns_rightmost(self):
        """With two IPs, should return the second (rightmost)."""
        request = _make_request(
            headers={"x-forwarded-for": "203.0.113.50, 198.51.100.25"},
            client_host="10.0.0.1",
        )
        ip = _get_real_client_ip(request)
        assert ip == "198.51.100.25"

    def test_whitespace_around_ips_is_stripped(self):
        """Leading/trailing whitespace around IPs should be stripped."""
        request = _make_request(
            headers={"x-forwarded-for": "  203.0.113.50 ,  198.51.100.25  "},
            client_host="10.0.0.1",
        )
        ip = _get_real_client_ip(request)
        assert ip == "198.51.100.25"

    def test_spoofed_leftmost_ip_is_ignored(self):
        """Attacker-controlled leftmost IP should be ignored in favor of rightmost."""
        request = _make_request(
            headers={"x-forwarded-for": "1.2.3.4, 5.6.7.8, 10.10.10.10"},
            client_host="10.0.0.1",
        )
        ip = _get_real_client_ip(request)
        # Rightmost is from trusted proxy
        assert ip == "10.10.10.10"
        assert ip != "1.2.3.4"

    def test_forwarded_for_takes_priority_over_client_host(self):
        """X-Forwarded-For should be used instead of client.host when present."""
        request = _make_request(
            headers={"x-forwarded-for": "203.0.113.50"},
            client_host="192.168.1.1",
        )
        ip = _get_real_client_ip(request)
        assert ip == "203.0.113.50"
        assert ip != "192.168.1.1"

    def test_empty_forwarded_for_returns_fallback(self):
        """Empty X-Forwarded-For should fall back to 127.0.0.1."""
        # When the header value is empty string, forwarded is truthy ("")
        # Actually empty string is falsy in Python, so it falls to client.host
        request = _make_request(
            headers={"x-forwarded-for": ""},
            client_host="10.0.0.1",
        )
        ip = _get_real_client_ip(request)
        # Empty string is falsy, so falls back to client.host
        assert ip == "10.0.0.1"

    def test_ipv6_in_forwarded_for(self):
        """Should handle IPv6 addresses in X-Forwarded-For."""
        request = _make_request(
            headers={"x-forwarded-for": "::1, 2001:db8::1"},
            client_host="10.0.0.1",
        )
        ip = _get_real_client_ip(request)
        assert ip == "2001:db8::1"
