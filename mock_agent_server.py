from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class MockAgentHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/chat":
            self._send_json(404, {"error": "not found"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8")

        try:
            data = json.loads(raw_body) if raw_body else {}
        except Exception:
            data = {"raw": raw_body}

        message = data.get("message") or data.get("input_text") or ""

        self._send_json(200, {
            "reply": "Mock success: " + message,
            "received": data
        })

    def log_message(self, format, *args):
        print("[MockAgent]", format % args)

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 9000), MockAgentHandler)
    print("Mock Agent server running at http://127.0.0.1:9000/chat")
    server.serve_forever()
