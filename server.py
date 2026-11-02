import http.server
import socketserver
import os
import json
import urllib.parse
from sees_engine import SEESPhysicsEngine, PhysicsParams

PORT = 8080
os.chdir(os.path.dirname(os.path.abspath(__file__)))

engine = SEESPhysicsEngine()
active_experiment_log = []

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

class SEESHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        global engine, active_experiment_log
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == "/api/telemetry/step":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                dt = float(data.get('dt', 0.1))
                motor_rpm = float(data.get('motor_rpm', 0.0))
                hot_temp = float(data.get('hot_temp', 85.0))
                cold_temp = float(data.get('cold_temp', 25.0))
                piezo_energy = float(data.get('piezo_energy', 0.0))
                aux_load = bool(data.get('aux_load', False))

                result = engine.step(dt, motor_rpm, hot_temp, cold_temp, piezo_energy, aux_load)
                if len(active_experiment_log) < 2000:
                    active_experiment_log.append(result)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return

        elif parsed_url.path == "/api/telemetry/reset":
            engine = SEESPhysicsEngine()
            active_experiment_log = []
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "reset_successful"}).encode('utf-8'))
            return

        super().do_POST()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == "/api/telemetry/log":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(active_experiment_log).encode('utf-8'))
            return

        super().do_GET()

if __name__ == "__main__":
    try:
        with ReusableTCPServer(("", PORT), SEESHandler) as httpd:
            print(f"\n========================================================")
            print(f"🚀 Project S.E.E.S. Advanced Server (v2.0) is LIVE on port {PORT}")
            print(f"👉 Virtual Hardware Lab: http://localhost:{PORT}/index.html")
            print(f"👉 Telemetry API: http://localhost:{PORT}/api/telemetry/step")
            print(f"========================================================\n")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped successfully.")
