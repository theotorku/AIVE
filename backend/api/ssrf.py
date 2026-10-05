"""SSRF guard for the public live-audit endpoint.

`POST /api/runs` renders an arbitrary user-supplied URL server-side (Playwright).
Without validation that is a Server-Side Request Forgery vector: an attacker can
point it at cloud metadata (169.254.169.254), loopback, or internal RFC1918
hosts and have the crawler fetch them. This resolves the host and rejects any
non-public address before a crawl is started.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


def _is_blocked(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip.split("%")[0])
    except ValueError:
        # Unparseable address — treat as blocked (fail closed).
        return True
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local   # covers 169.254.0.0/16 (cloud metadata)
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified
    )


def check_url(url: str) -> tuple[bool, str | None]:
    """Return (allowed, reason). A URL is allowed only if it is http(s) and
    every DNS-resolved address is a public IP."""
    try:
        parsed = urlparse(url)
    except Exception:  # noqa: BLE001
        return False, "That URL could not be parsed."
    if parsed.scheme not in ("http", "https"):
        return False, "Only http(s) URLs can be audited."
    host = parsed.hostname
    if not host:
        return False, "That URL has no host."

    try:
        infos = socket.getaddrinfo(host, None)
    except Exception:  # noqa: BLE001
        return False, "That host could not be resolved."

    resolved = {info[4][0] for info in infos}
    if not resolved:
        return False, "That host could not be resolved."
    for ip in resolved:
        if _is_blocked(ip):
            return False, "That URL points to a non-public address."
    return True, None
