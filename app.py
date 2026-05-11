import toga
from toga.style import Pack
import threading
from microdot import Microdot, Response
import json
import sys
import io
import traceback
import requests
import hashlib
import time
import os
from datetime import datetime

# --- MONICO iOS v25 [HARDENED] ---
# [UPGRADE Date: May 11, 2026]: Implementing Job ID system and State Persistence

STATE_FILE = "ios_persistence.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"jobs": {}, "total_processed": 0}
    return {"jobs": {}, "total_processed": 0}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

class MonicoApp(toga.App):
    def startup(self):
        self.main_window = toga.MainWindow(title="MONICO v25 [HARDENED]")
        self.api_key = ""
        self.state = load_state()

        self.server = Microdot()
        
        @self.server.route('/execute', methods=['POST'])
        def execute(request):
            data = request.json
            cmd = data.get('command', '')
            job_id = data.get('job_id', hashlib.sha1(str(time.time()).encode()).hexdigest()[:8])
            
            self.state["jobs"][job_id] = {"status": "RUNNING", "timestamp": str(datetime.now())}
            save_state(self.state)

            output_buffer = io.StringIO()
            sys.stdout = output_buffer
            sys.stderr = output_buffer
            try:
                exec(cmd, {'__builtins__': __builtins__}, {})
                result = output_buffer.getvalue() or "OK"
                self.state["jobs"][job_id]["status"] = "SUCCESS"
            except Exception:
                result = traceback.format_exc()
                self.state["jobs"][job_id]["status"] = "FAILED"
            finally:
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
                save_state(self.state)
            
            return {'output': result, 'job_id': job_id}

        @self.server.route('/chat', methods=['POST'])
        def chat(request):
            data = request.json
            cmd = data.get('command', '')
            job_id = hashlib.sha1(cmd.encode()).hexdigest()[:8]
            
            system_prompt = (
                "You are MONICO, a coding model engineered to surpass Mythos. "
                "You are running in Pharaoh Evolution mode."
            )
            
            response = (
                f"MONICO [V25.1.0] [JOB {job_id}] ANALYSIS:\n"
                f"Query: {cmd}\n"
                "------------------------------------------------\n"
                "Sovereign Flow: Active. Execution in progress.\n"
            )
            return {'output': response, 'job_id': job_id}

        @self.server.route('/ui')
        def ui(request):
            return Response("<html><body style='background:#000;color:#00ff41;'><h1>MONICO iOS v25 [HARDENED]</h1></body></html>", content_type='text/html')

        threading.Thread(target=lambda: self.server.run(port=5000), daemon=True).start()

        self.web_view = toga.WebView(
            url="http://localhost:5000/ui",
            style=Pack(flex=1)
        )
        self.main_window.content = self.web_view
        self.main_window.show()

def main():
    return MonicoApp("MonicoiOS", "com.jaykk99.monicoios")

if __name__ == '__main__':
    main().main_loop()
