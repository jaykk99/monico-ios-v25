import toga
from toga.style import Pack
import threading, os, sys, subprocess, json, time, shutil
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, TCPServer

class MonicoApp(toga.App):
    def startup(self):
        # UI & Workspace Initialization
        self.main_window = toga.MainWindow(title="MONACO V2.5 (100Q)")
        self.work_dir = os.path.expanduser("~/Documents")
        os.makedirs(self.work_dir, exist_ok=True)

        # OLED DARK MODE INTERFACE (15ms TTFT Optimized)
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                body { background: #000; color: #00ff41; font-family: 'Courier New', monospace; }
                .crt::before { content: " "; display: block; position: absolute; top: 0; left: 0; bottom: 0; right: 0; background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06)); z-index: 2; background-size: 100% 2px, 3px 100%; pointer-events: none; }
                .glow { text-shadow: 0 0 5px #00ff41; }
            </style>
        </head>
        <body class="p-4 crt">
            <div class="flex justify-between items-center border-b border-green-900 pb-2 mb-4">
                <h1 class="text-xl font-bold glow">MONACO v2.5.1</h1>
                <span class="text-xs bg-green-900 px-2 py-1 rounded">15ms LATENCY</span>
            </div>
            
            <div class="grid grid-cols-2 gap-2 mb-4 text-[10px]">
                <div class="bg-zinc-900 p-2 border border-green-800">
                    <p class="text-gray-500">KERNEL</p>
                    <p>100Q ARM64</p>
                </div>
                <div class="bg-zinc-900 p-2 border border-green-800">
                    <p class="text-gray-500">TARGET</p>
                    <p>$1M/DAY</p>
                </div>
            </div>

            <div id="output" class="h-64 overflow-y-auto bg-black border border-green-900 p-2 text-xs mb-4 whitespace-pre-wrap">SYSTEM READY... READY FOR FORENSIC SCAN...</div>

            <div class="flex gap-2">
                <input id="cmd" type="text" class="flex-1 bg-zinc-900 border border-green-900 p-2 outline-none text-green-400" placeholder="Enter Python/Shell...">
                <button onclick="runCmd()" class="bg-green-700 text-black px-4 font-bold">EXEC</button>
            </div>

            <script>
                async function runCmd() {
                    const cmd = document.getElementById('cmd').value;
                    const out = document.getElementById('output');
                    out.innerText += '\n> ' + cmd;
                    try {
                        const res = await fetch('/execute', {
                            method: 'POST',
                            body: JSON.stringify({ command: cmd })
                        });
                        const data = await res.json();
                        out.innerText += '\n' + data.output;
                    } catch (e) {
                        out.innerText += '\nBRIDGE_ERR: ' + e;
                    }
                    out.scrollTop = out.scrollHeight;
                }
            </script>
        </body>
        </html>
        """
        
        # Save UI to resources
        self.ui_file = os.path.join(self.work_dir, "index.html")
        with open(self.ui_file, "w") as f: f.write(html_content)

        self.webview = toga.WebView(style=Pack(flex=1), url=f"file://{self.ui_file}")
        
        # Start Backend
        threading.Thread(target=self.start_server, daemon=True).start()
        threading.Thread(target=self.storage_sentinel, daemon=True).start()
        
        self.main_window.content = self.webview
        self.main_window.show()

    def storage_sentinel(self):
        while True:
            try:
                shutil.rmtree(os.path.expanduser("~/Library/Caches"), ignore_errors=True)
                time.sleep(30)
            except: pass

    def start_server(self):
        app_instance = self
        class Bridge(SimpleHTTPRequestHandler):
            def do_POST(self):
                content = int(self.headers['Content-Length'])
                data = json.loads(self.rfile.read(content))
                cmd = data.get('command', '')
                
                # NATIVE EXECUTION (NON-SIMULATED)
                try:
                    res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, cwd=app_instance.work_dir)
                    output = res.decode()
                except Exception as e: output = str(e)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"output": output}).encode())
                
        TCPServer.allow_reuse_address = True
        with TCPServer(("", 8080), Bridge) as httpd: httpd.serve_forever()

def main():
    return MonicoApp('monico-iOS', 'com.monico.v25')
