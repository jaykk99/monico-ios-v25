import toga
from toga.style import Pack
import threading
from microdot import Microdot, Response
import json
import sys
import io
import traceback
import requests

class MonicoApp(toga.App):
    def startup(self):
        self.main_window = toga.MainWindow(title="MONICO v2.5")
        self.api_key = "" # Placeholder for user to set in-app later

        self.server = Microdot()
        
        @self.server.route('/execute', methods=['POST'])
        def execute(request):
            data = request.json
            cmd = data.get('command', '')
            output_buffer = io.StringIO()
            sys.stdout = output_buffer
            sys.stderr = output_buffer
            try:
                # Security warning: executing arbitrary code on-device
                exec(cmd, {'__builtins__': __builtins__}, {})
                result = output_buffer.getvalue()
            except Exception:
                result = traceback.format_exc()
            finally:
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
            return {'output': result or "Command executed."}

        @self.server.route('/chat', methods=['POST'])
        def chat(request):
            data = request.json
            cmd = data.get('command', '')
            
            # Monico Model Identity & System Prompt
            system_prompt = (
                "You are MONICO, a coding model engineered to surpass Mythos. "
                "Your primary focus is high-performance software engineering, "
                "forensic code analysis, and zero-day vulnerability detection. "
                "Responses must be architecturally sound, optimized for ARM64 kernels, "
                "and include performance benchmarks where applicable."
            )
            
            response = (
                "MONICO [V2.5.1] ANALYSIS:\n"
                f"Query: {cmd}\n"
                "--------------------------------------------------\n"
                "Architectural Assessment: Initializing...\n"
                "Solution: Implementing optimized logic flow. Compared to Mythos, "
                "this approach reduces latency by 12% via branch prediction optimization.\n"
                "\n[Code block would be generated here by API]"
            )
            return {'output': response}

        @self.server.route('/agent', methods=['POST'])
        def agent(request):
            data = request.json
            cmd = data.get('command', '')
            return {'output': f"MONICO AGENT [ACTIVE]: Directive '{cmd}' is being processed in background kernel."}

        @self.server.route('/ui')
        def ui(request):
            try:
                with open("resources/ui/index.html", "r") as f:
                    content = f.read()
                return Response(content, content_type='text/html')
            except Exception as e:
                return f"Error loading UI: {str(e)}", 500

        # Run Microdot
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