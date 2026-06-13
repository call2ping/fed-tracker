"""
server.py — เว็บเซิร์ฟเวอร์เล็กๆ (stdlib ล้วน) เสิร์ฟไฟล์ static + REST API
================================================================================
รัน:  python server.py            (พอร์ต 8000 หรือกำหนดด้วย env PORT)
เปิด: http://localhost:8000

API:
  GET /api/health           -> {"ok": true}
  GET /api/rate?key=FRED    -> กรอบดอกเบี้ยปัจจุบันจาก FRED (เลี่ยง CORS)
  GET /api/fedwatch?key=FRED-> ความน่าจะเป็น FedWatch คำนวณจาก futures (cache 10 นาที)

เสิร์ฟ frontend จากโฟลเดอร์เดียวกัน → เรียก /api/* ได้โดยไม่มีปัญหา CORS
"""

import json
import os
import time
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import fedwatch

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "8000"))
CACHE_TTL = 600  # วินาที

_cache = {}  # key -> (timestamp, payload)


def _cached(key, producer):
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]
    val = producer()
    _cache[key] = (now, val)
    return val


def _produce_fedwatch(key):
    """คำนวณ FedWatch แล้วบันทึก snapshot ประวัติ (ทำเฉพาะตอน cache miss)"""
    payload = fedwatch.build_payload(fred_key=key)
    try:
        fedwatch.append_history(payload)
    except Exception:  # noqa: BLE001 — บันทึกประวัติพังไม่ควรทำให้ API ล้ม
        pass
    return payload


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HERE, **kwargs)

    def log_message(self, fmt, *args):
        # log แบบกระชับ
        print(f"  {self.command} {self.path}  ->  {args[1] if len(args) > 1 else ''}")

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/"):
            return self._handle_api(parsed)
        return super().do_GET()

    def _handle_api(self, parsed):
        qs = urllib.parse.parse_qs(parsed.query)
        key = qs.get("key", [None])[0] or os.environ.get("FRED_API_KEY")
        route = parsed.path

        try:
            if route == "/api/health":
                return self._send_json({"ok": True})

            if route == "/api/rate":
                rate = fedwatch.fred_current_rate(key) if key else None
                if not rate:
                    return self._send_json(
                        {"error": "ต้องมี FRED API key ที่ถูกต้อง (?key=...)"}, 400)
                return self._send_json(rate)

            if route == "/api/fedwatch":
                cache_key = f"fedwatch:{bool(key)}"
                payload = _cached(cache_key, lambda: _produce_fedwatch(key))
                return self._send_json(payload)

            if route == "/api/history":
                path = os.path.join(HERE, "history.json")
                hist = []
                if os.path.exists(path):
                    try:
                        with open(path, encoding="utf-8") as f:
                            hist = json.load(f)
                    except (ValueError, OSError):
                        hist = []
                return self._send_json(hist)

            return self._send_json({"error": "ไม่พบ endpoint นี้"}, 404)

        except RuntimeError as e:
            # คำนวณ FedWatch ไม่ได้ → 503 ให้ frontend fallback ไปใช้ sample
            return self._send_json({"error": str(e)}, 503)
        except Exception as e:  # noqa: BLE001
            return self._send_json({"error": f"server error: {e}"}, 500)


def main():
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Fed Tracker ทำงานที่  http://localhost:{PORT}")
    print("กด Ctrl+C เพื่อหยุด")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nหยุดเซิร์ฟเวอร์แล้ว")
        srv.shutdown()


if __name__ == "__main__":
    main()
