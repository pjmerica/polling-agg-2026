"""Serve the live dashboard on the home network, so a phone or another computer on the same Wi-Fi can open it.

Same page and data as on this PC (refreshes every 15 s), nothing public. Serves only dashboard.html and
data/raw/dashboard/ (not the rest of the folder). The first run may bring up a Windows Firewall prompt: allow it
on private networks.

    py "Election night simulator/scripts/serve_home.py"            # port 8765
"""
import argparse
import functools
import http.server
import os
import socket

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ALLOWED = ("/dashboard.html", "/data/raw/dashboard/live_data.js")


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", ""):
            self.send_response(302)
            self.send_header("Location", "/dashboard.html")
            self.end_headers()
            return
        if path not in ALLOWED:
            self.send_error(404)
            return
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):          # quiet: one line per request would flood the window all night
        pass


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.168.1.1", 9))       # no packet is sent; this just picks the Wi-Fi interface
        return s.getsockname()[0]
    except OSError:
        return "this-pc's-ip"
    finally:
        s.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    srv = http.server.ThreadingHTTPServer(("0.0.0.0", a.port), functools.partial(Handler, directory=ROOT))
    print(f"On this PC:          http://localhost:{a.port}/dashboard.html")
    print(f"On your phone (same Wi-Fi): http://{lan_ip()}:{a.port}/dashboard.html")
    print("Ctrl+C stops it.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
