"""Host-side LAN relay that preserves the real client IP for Docker Desktop."""

import argparse
import ipaddress
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "proxy-connection",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


class NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, url):
        return None


UPSTREAM_OPENER = build_opener(NoRedirectHandler())


def _client_ip(address: str) -> str:
    parsed = ipaddress.ip_address(address)
    if isinstance(parsed, ipaddress.IPv6Address) and parsed.ipv4_mapped:
        return str(parsed.ipv4_mapped)
    return str(parsed)


def _forward_headers(headers, client_ip: str, body_length: int) -> dict[str, str]:
    connection_tokens = {
        token.strip().lower()
        for token in headers.get("Connection", "").split(",")
        if token.strip()
    }
    excluded = HOP_BY_HOP_HEADERS | connection_tokens | {
        "content-length",
        "host",
        "forwarded",
    }

    forwarded = {
        name: value
        for name, value in headers.items()
        if name.lower() not in excluded and not name.lower().startswith("x-forwarded-")
    }
    forwarded["Content-Length"] = str(body_length)
    forwarded["X-Forwarded-For"] = client_ip
    forwarded["X-Real-IP"] = client_ip
    return forwarded


class GatewayRelayHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    upstream = "http://127.0.0.1:8085"
    timeout_seconds = 60

    def do_GET(self):
        self._forward()

    def do_HEAD(self):
        self._forward()

    def do_POST(self):
        self._forward()

    def do_PUT(self):
        self._forward()

    def do_PATCH(self):
        self._forward()

    def do_DELETE(self):
        self._forward()

    def do_OPTIONS(self):
        self._forward()

    def _forward(self):
        try:
            remote_ip = _client_ip(self.client_address[0])
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length < 0:
                self.send_error(400, "Invalid Content-Length")
                return

            body = self.rfile.read(content_length) if content_length else None
            request = Request(
                f"{self.upstream.rstrip('/')}{self.path}",
                data=body,
                headers=_forward_headers(
                    self.headers, remote_ip, len(body) if body else 0
                ),
                method=self.command,
            )

            try:
                upstream_response = UPSTREAM_OPENER.open(
                    request, timeout=self.timeout_seconds
                )
            except HTTPError as response:
                upstream_response = response
            except URLError as exc:
                logging.error("LAN gateway upstream unavailable: %s", exc)
                self.send_error(502, "Gateway unavailable")
                return

            with upstream_response:
                response_body = upstream_response.read()
                self.send_response(upstream_response.status)
                for name, value in upstream_response.headers.items():
                    if name.lower() not in HOP_BY_HOP_HEADERS | {"content-length"}:
                        self.send_header(name, value)
                self.send_header("Content-Length", str(len(response_body)))
                self.send_header("Connection", "close")
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(response_body)
            self.close_connection = True
        except (ValueError, OSError) as exc:
            logging.warning("LAN gateway relay rejected request: %s", exc)
            self.send_error(400, "Invalid request")

    def log_message(self, format_string, *args):
        logging.info(
            "%s %s - %s",
            self.client_address[0],
            self.requestline,
            format_string % args,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Relay LAN requests to the loopback-only Docker gateway."
    )
    parser.add_argument(
        "--listen-host",
        required=True,
        help="This computer's LAN interface address, e.g. 10.214.252.246",
    )
    parser.add_argument("--listen-port", type=int, default=8080)
    parser.add_argument("--upstream", default="http://127.0.0.1:8085")
    args = parser.parse_args()

    GatewayRelayHandler.upstream = args.upstream
    server = ThreadingHTTPServer((args.listen_host, args.listen_port), GatewayRelayHandler)
    server.daemon_threads = True
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.info(
        "LAN gateway relay listening on http://%s:%s -> %s",
        args.listen_host,
        args.listen_port,
        args.upstream,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Stopping LAN gateway relay")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
