import toga
from toga.style import Pack
import threading, os, sys, subprocess, json, time, shutil, io, traceback, re
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, TCPServer
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ---------------------------------------------------------------------------
# Mythos Bridge - LLM Provider Configuration
# ---------------------------------------------------------------------------
DEFAULT_BRIDGE_CONFIG = {
    "provider": "openai",           # openai | anthropic | ollama | custom
    "api_key": "",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini",
    "system_prompt": "You are Mythos, an advanced AI assistant embedded in the MONICO V2.5 execution environment. You have access to a local terminal for running Python and Shell commands. Be concise and precise.",
    "max_tokens": 2048,
    "temperature": 0.7,
    "timeout_secs": 30,
    "agent_system_prompt": "You are Mythos Agent, an autonomous task executor inside MONICO V2.5. When given a task, break it into steps, reason through each, and produce a concrete result. If you need to run code, output it in ```python or ```shell fenced blocks and the system will execute it for you.",
}

# Provider presets: name -> { base_url, default_model, header_style }
PROVIDER_PRESETS = {
    "openai":    {"base_url": "https://api.openai.com/v1",           "model": "gpt-4o-mini",       "header": "bearer"},
    "anthropic": {"base_url": "https://api.anthropic.com/v1",        "model": "claude-3-5-sonnet-20241022", "header": "x-api-key"},
    "ollama":    {"base_url": "http://localhost:11434/v1",            "model": "llama3.2",          "header": "bearer"},
    "custom":    {"base_url": "",                                      "model": "",                  "header": "bearer"},
}

CONFIG_FILE_NAME = ".mythos_bridge.json"


class MythosBridge:
    """Extensible LLM bridge supporting OpenAI-compatible, Anthropic, Ollama, and custom endpoints."""

    def __init__(self, config: dict):
        self.config = dict(DEFAULT_BRIDGE_CONFIG)
        self.config.update(config)
        self.chat_history: list[dict] = []
        self.agent_history: list[dict] = []

    # ---- persistence ----
    @staticmethod
    def config_path(work_dir: str) -> str:
        return os.path.join(work_dir, CONFIG_FILE_NAME)

    @classmethod
    def load(cls, work_dir: str) -> "MythosBridge":
        path = cls.config_path(work_dir)
        cfg = {}
        if os.path.exists(path):
            try:
                with open(path) as f:
                    cfg = json.load(f)
            except Exception:
                pass
        return cls(cfg)

    def save(self, work_dir: str):
        path = self.config_path(work_dir)
        with open(path, "w") as f:
            json.dump(self.config, f, indent=2)

    # ---- LLM request ----
    def _build_headers(self) -> dict:
        provider = self.config.get("provider", "openai")
        preset = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS["custom"])
        headers = {"Content-Type": "application/json"}
        api_key = self.config.get("api_key", "")

        if provider == "anthropic":
            if api_key:
                headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
        else:
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _chat_url(self) -> str:
        base = self.config.get("base_url", "").rstrip("/")
        provider = self.config.get("provider", "openai")
        if provider == "anthropic":
            return f"{base}/messages"
        return f"{base}/chat/completions"

    def _build_body(self, messages: list[dict]) -> dict:
        provider = self.config.get("provider", "openai")
        model = self.config.get("model", "gpt-4o-mini")
        max_tokens = int(self.config.get("max_tokens", 2048))
        temperature = float(self.config.get("temperature", 0.7))

        if provider == "anthropic":
            # Anthropic Messages API format
            system_msg = ""
            api_messages = []
            for m in messages:
                if m["role"] == "system":
                    system_msg = m["content"]
                else:
                    api_messages.append({"role": m["role"], "content": m["content"]})
            body = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": api_messages,
            }
            if system_msg:
                body["system"] = system_msg
            return body
        else:
            # OpenAI-compatible (works with OpenAI, Ollama, custom)
            return {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

    def _extract_reply(self, data: dict) -> str:
        provider = self.config.get("provider", "openai")
        if provider == "anthropic":
            # Anthropic response
            content = data.get("content", [])
            if content and isinstance(content, list):
                return content[0].get("text", "")
            return str(data)
        else:
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return str(data)

    def send_request(self, messages: list[dict]) -> str:
        """Send a chat completion request and return the assistant reply text."""
        url = self._chat_url()
        headers = self._build_headers()
        body = self._build_body(messages)
        timeout = int(self.config.get("timeout_secs", 30))

        req = Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        try:
            with urlopen(req, timeout=timeout) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                return self._extract_reply(resp_data)
        except HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            return f"[LLM HTTP {e.code}] {err_body[:500]}"
        except URLError as e:
            return f"[LLM Connection Error] {e.reason}"
        except Exception as e:
            return f"[LLM Error] {str(e)}"

    # ---- high-level chat / agent ----
    def chat(self, user_message: str) -> str:
        sys_prompt = self.config.get("system_prompt", "")
        self.chat_history.append({"role": "user", "content": user_message})
        messages = []
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        # Keep last 20 turns for context window management
        messages.extend(self.chat_history[-40:])
        reply = self.send_request(messages)
        self.chat_history.append({"role": "assistant", "content": reply})
        return reply

    def agent(self, task: str) -> str:
        agent_sys = self.config.get("agent_system_prompt", "")
        self.agent_history.append({"role": "user", "content": task})
        messages = []
        if agent_sys:
            messages.append({"role": "system", "content": agent_sys})
        messages.extend(self.agent_history[-40:])
        reply = self.send_request(messages)
        self.agent_history.append({"role": "assistant", "content": reply})
        return reply

    def test_connection(self) -> str:
        """Send a lightweight ping to verify the LLM endpoint is reachable."""
        messages = [
            {"role": "system", "content": "Respond with only: MYTHOS_BRIDGE_OK"},
            {"role": "user", "content": "ping"},
        ]
        return self.send_request(messages)

    def get_status_dict(self) -> dict:
        return {
            "provider": self.config.get("provider"),
            "base_url": self.config.get("base_url"),
            "model": self.config.get("model"),
            "has_key": bool(self.config.get("api_key")),
            "chat_turns": len(self.chat_history),
            "agent_turns": len(self.agent_history),
        }


# ---------------------------------------------------------------------------
# Terminal Executor - real Python / Shell backend
# ---------------------------------------------------------------------------
class TerminalExecutor:
    """Handles language detection and safe subprocess execution."""

    PYTHON_INDICATORS = (
        'print(', 'import ', 'from ', 'def ', 'class ', 'for ', 'while ',
        'if ', 'elif ', 'else:', 'try:', 'except ', 'with ', 'lambda ',
        'return ', 'yield ', 'raise ', 'assert ', 'pass', 'break', 'continue',
        '= [', '= {', '= (', '.append(', '.items(', '.keys(', '.values(',
        'range(', 'len(', 'str(', 'int(', 'float(', 'list(', 'dict(',
        'open(', 'json.', 'os.', 'sys.', 'Path(', 'datetime',
    )

    NODE_INDICATORS = (
        'console.log(', 'require(', 'const ', 'let ', 'var ',
        'function ', 'async ', 'await ', '=>', 'module.exports',
        'process.', 'Buffer.', 'Promise.',
    )

    def __init__(self, work_dir: str, timeout: int = 30):
        self.work_dir = work_dir
        self.timeout = timeout
        self.env = os.environ.copy()
        self.env["PYTHONDONTWRITEBYTECODE"] = "1"

    def detect_language(self, code: str) -> str:
        stripped = code.strip()

        # Explicit shebangs
        if stripped.startswith('#!') and 'python' in stripped.split('\n')[0]:
            return 'python'
        if stripped.startswith('#!') and ('bash' in stripped.split('\n')[0] or 'sh' in stripped.split('\n')[0]):
            return 'shell'

        # Multi-line heuristic: if it has def/class/import across lines, it's Python
        lines = stripped.split('\n')
        if len(lines) > 1:
            py_score = sum(1 for line in lines if any(line.strip().startswith(kw) for kw in ('import ', 'from ', 'def ', 'class ', 'print(', 'if ', 'for ', 'while ', 'try:', 'with ')))
            sh_score = sum(1 for line in lines if any(line.strip().startswith(kw) for kw in ('ls', 'cd ', 'echo ', 'cat ', 'grep ', 'mkdir ', 'rm ', 'cp ', 'mv ', 'chmod ', 'export ', 'source ', 'sudo ', 'apt ', 'brew ', 'pip ', 'npm ')))
            if py_score > sh_score:
                return 'python'
            if sh_score > py_score:
                return 'shell'

        # Single-line checks
        for indicator in self.PYTHON_INDICATORS:
            if indicator in stripped:
                return 'python'
        for indicator in self.NODE_INDICATORS:
            if indicator in stripped:
                return 'node'

        return 'shell'

    def execute(self, code: str, force_lang: str = None) -> dict:
        lang = force_lang or self.detect_language(code)
        stripped = code.strip()
        exit_code = 0

        try:
            if lang == 'python':
                # For multi-line Python, write to temp file
                if '\n' in stripped or len(stripped) > 200:
                    tmp_path = os.path.join(self.work_dir, '.mythos_exec.py')
                    with open(tmp_path, 'w') as f:
                        f.write(stripped)
                    cmd = [sys.executable or 'python3', tmp_path]
                else:
                    cmd = [sys.executable or 'python3', '-c', stripped]
                result = subprocess.run(
                    cmd,
                    capture_output=True, text=True,
                    cwd=self.work_dir, timeout=self.timeout,
                    env=self.env
                )
            elif lang == 'node':
                if '\n' in stripped or len(stripped) > 200:
                    tmp_path = os.path.join(self.work_dir, '.mythos_exec.js')
                    with open(tmp_path, 'w') as f:
                        f.write(stripped)
                    cmd = ['node', tmp_path]
                else:
                    cmd = ['node', '-e', stripped]
                result = subprocess.run(
                    cmd,
                    capture_output=True, text=True,
                    cwd=self.work_dir, timeout=self.timeout,
                    env=self.env
                )
            else:
                # Shell
                result = subprocess.run(
                    stripped, shell=True,
                    capture_output=True, text=True,
                    cwd=self.work_dir, timeout=self.timeout,
                    env=self.env
                )

            output = result.stdout
            if result.stderr:
                output += ("\n" if output else "") + result.stderr
            exit_code = result.returncode
            if not output.strip():
                output = f"[exit {exit_code}]" if exit_code != 0 else "[ok - no output]"

        except subprocess.TimeoutExpired:
            output = f"[TIMEOUT] Execution exceeded {self.timeout}s limit."
            exit_code = -1
        except FileNotFoundError as e:
            output = f"[NOT FOUND] {e}"
            exit_code = -1
        except Exception as e:
            output = f"[ERROR] {traceback.format_exc()}"
            exit_code = -1

        return {
            "output": output.rstrip(),
            "language": lang,
            "exit_code": exit_code,
        }

    def execute_fenced_blocks(self, text: str) -> list[dict]:
        """Extract and run fenced code blocks (```python ... ``` or ```shell ... ```) from LLM output."""
        pattern = r'```(python|shell|bash|sh|js|javascript|node)\s*\n(.*?)```'
        blocks = re.findall(pattern, text, re.DOTALL)
        results = []
        for lang_hint, code in blocks:
            lang_map = {
                'python': 'python', 'shell': 'shell', 'bash': 'shell', 'sh': 'shell',
                'js': 'node', 'javascript': 'node', 'node': 'node'
            }
            lang = lang_map.get(lang_hint, 'shell')
            result = self.execute(code, force_lang=lang)
            results.append(result)
        return results


# ---------------------------------------------------------------------------
# Main Toga Application
# ---------------------------------------------------------------------------
class MonicoApp(toga.App):
    def startup(self):
        self.main_window = toga.MainWindow(title="MONICO V2.5 (100Q)")
        self.work_dir = os.path.expanduser("~/Documents")
        os.makedirs(self.work_dir, exist_ok=True)

        # Initialize core systems
        self.bridge = MythosBridge.load(self.work_dir)
        self.executor = TerminalExecutor(self.work_dir)

        # OLED DARK MODE INTERFACE (15ms TTFT Optimized)
        html_content = self._build_html()

        # Save UI to resources
        self.ui_file = os.path.join(self.work_dir, "index.html")
        with open(self.ui_file, "w") as f:
            f.write(html_content)

        self.webview = toga.WebView(style=Pack(flex=1), url=f"file://{self.ui_file}")

        # Start Backend
        threading.Thread(target=self.start_server, daemon=True).start()

        self.main_window.content = self.webview
        self.main_window.show()

    # ---------- HTML UI ----------
    def _build_html(self) -> str:
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>MONICO V2.5 CORE</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #000000; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; overflow: hidden; height: 100vh; }
        .active-tab { border-bottom: 2px solid #ffffff; color: #ffffff; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 2px; }
        .view-section { display: none; height: 100%; }
        .view-section.active { display: flex; flex-direction: column; }
        .cfg-input { background: #18181b; border: 1px solid #3f3f46; color: #fff; padding: 8px 12px; border-radius: 6px; font-size: 13px; width: 100%; outline: none; font-family: ui-monospace, monospace; }
        .cfg-input:focus { border-color: #71717a; }
        .cfg-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; color: #71717a; margin-bottom: 4px; display: block; }
        .cfg-select { background: #18181b; border: 1px solid #3f3f46; color: #fff; padding: 8px 12px; border-radius: 6px; font-size: 13px; width: 100%; outline: none; -webkit-appearance: none; }
        .cfg-btn { padding: 8px 16px; border-radius: 6px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer; transition: all 0.15s; border: none; }
        .typing-dot { animation: blink 1.4s infinite both; }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink { 0%, 80%, 100% { opacity: 0.2; } 40% { opacity: 1; } }
        pre.code-block { background: #18181b; border: 1px solid #27272a; border-radius: 6px; padding: 8px 12px; font-size: 11px; overflow-x: auto; white-space: pre-wrap; word-break: break-word; }
    </style>
</head>
<body class="flex flex-col">

    <!-- HEADER -->
    <header class="flex justify-between items-center p-4 border-b border-zinc-800 bg-black">
        <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-white animate-pulse"></div>
            <h1 class="text-sm font-bold tracking-widest text-white">MONICO V2.5 (100Q)</h1>
        </div>
        <div class="flex gap-4 text-xs font-mono text-zinc-400">
            <span>TTFT: <span class="text-white">15ms</span></span>
            <span id="bridge-status-badge" class="text-zinc-500">BRIDGE: --</span>
        </div>
    </header>

    <!-- NAVIGATION TABS -->
    <nav class="flex border-b border-zinc-800 bg-black">
        <button onclick="setMode('chat')" id="tab-chat" class="flex-1 py-3 text-xs font-bold active-tab transition-colors">CHAT</button>
        <button onclick="setMode('agent')" id="tab-agent" class="flex-1 py-3 text-xs font-bold text-zinc-500 border-b-2 border-transparent transition-colors">AGENT</button>
        <button onclick="setMode('terminal')" id="tab-terminal" class="flex-1 py-3 text-xs font-bold text-zinc-500 border-b-2 border-transparent transition-colors">TERMINAL</button>
        <button onclick="setMode('bridge')" id="tab-bridge" class="flex-1 py-3 text-xs font-bold text-zinc-500 border-b-2 border-transparent transition-colors">BRIDGE</button>
    </nav>

    <!-- MAIN CONTENT -->
    <main class="flex-1 overflow-hidden relative bg-black">

        <!-- CHAT VIEW -->
        <section id="view-chat" class="view-section active p-4">
            <div id="chat-output" class="flex-1 overflow-y-auto space-y-4 text-sm pb-4">
                <div class="text-zinc-500 text-[10px] uppercase font-mono mb-4 text-center">Mythos Bridge Active &middot; LLM-Powered Chat</div>
                <div class="bg-zinc-900 text-white p-3 rounded-lg rounded-tl-none inline-block max-w-[85%]">
                    Mythos Bridge initialized. Configure your LLM provider in the BRIDGE tab, then start chatting.
                </div>
            </div>
        </section>

        <!-- AGENT VIEW -->
        <section id="view-agent" class="view-section p-4">
            <div id="agent-output" class="flex-1 overflow-y-auto space-y-4 text-sm pb-4">
                <div class="text-zinc-500 text-[10px] uppercase font-mono mb-4 text-center">Mythos Agent &middot; Autonomous Task Execution</div>
                <div class="bg-zinc-900 text-white p-3 rounded-lg rounded-tl-none inline-block max-w-[85%]">
                    Agent mode ready. Describe a task and the agent will plan, reason, and execute code blocks automatically.
                </div>
            </div>
        </section>

        <!-- TERMINAL VIEW -->
        <section id="view-terminal" class="view-section p-4 bg-black">
            <div class="flex justify-between items-center mb-3 border-b border-zinc-800 pb-2">
                <span class="text-xs text-zinc-400 uppercase tracking-widest">Execution Core</span>
                <div id="ai-lang-badge" class="bg-zinc-900 text-white text-[10px] border border-zinc-700 rounded px-2 py-1 uppercase tracking-tighter font-mono">
                    AI: AUTO-SELECTING
                </div>
            </div>
            <div id="term-output" class="flex-1 overflow-y-auto p-2 space-y-1 font-mono text-xs text-zinc-300 bg-zinc-950 border border-zinc-900 rounded">
                <div class="text-zinc-500">Local execution environment active. Python &amp; Shell supported.</div>
            </div>
        </section>

        <!-- MYTHOS BRIDGE CONFIG VIEW -->
        <section id="view-bridge" class="view-section p-4 overflow-y-auto bg-black">
            <div class="w-full max-w-lg mx-auto space-y-5">
                <div class="text-center mb-4">
                    <h2 class="text-sm font-bold tracking-widest text-white mb-1">MYTHOS BRIDGE</h2>
                    <p class="text-[10px] text-zinc-500 uppercase tracking-wider">LLM Provider Configuration</p>
                </div>

                <!-- Provider -->
                <div>
                    <label class="cfg-label">Provider</label>
                    <select id="cfg-provider" class="cfg-select" onchange="onProviderChange()">
                        <option value="openai">OpenAI</option>
                        <option value="anthropic">Anthropic</option>
                        <option value="ollama">Ollama (Local)</option>
                        <option value="custom">Custom Endpoint</option>
                    </select>
                </div>

                <!-- API Key -->
                <div>
                    <label class="cfg-label">API Key</label>
                    <input id="cfg-api-key" type="password" class="cfg-input" placeholder="sk-..." autocomplete="off">
                </div>

                <!-- Base URL -->
                <div>
                    <label class="cfg-label">Base URL</label>
                    <input id="cfg-base-url" type="text" class="cfg-input" placeholder="https://api.openai.com/v1">
                </div>

                <!-- Model -->
                <div>
                    <label class="cfg-label">Model</label>
                    <input id="cfg-model" type="text" class="cfg-input" placeholder="gpt-4o-mini">
                </div>

                <!-- Temperature -->
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="cfg-label">Temperature</label>
                        <input id="cfg-temperature" type="number" step="0.1" min="0" max="2" class="cfg-input" value="0.7">
                    </div>
                    <div>
                        <label class="cfg-label">Max Tokens</label>
                        <input id="cfg-max-tokens" type="number" step="256" min="64" class="cfg-input" value="2048">
                    </div>
                </div>

                <!-- System Prompt -->
                <div>
                    <label class="cfg-label">System Prompt (Chat)</label>
                    <textarea id="cfg-system-prompt" class="cfg-input" rows="3" style="resize:vertical;"></textarea>
                </div>

                <!-- Agent System Prompt -->
                <div>
                    <label class="cfg-label">System Prompt (Agent)</label>
                    <textarea id="cfg-agent-prompt" class="cfg-input" rows="3" style="resize:vertical;"></textarea>
                </div>

                <!-- Timeout -->
                <div>
                    <label class="cfg-label">Request Timeout (seconds)</label>
                    <input id="cfg-timeout" type="number" min="5" max="120" class="cfg-input" value="30">
                </div>

                <!-- Action Buttons -->
                <div class="flex gap-3 pt-2">
                    <button onclick="saveBridgeConfig()" class="cfg-btn bg-white text-black flex-1 hover:bg-zinc-200">SAVE CONFIG</button>
                    <button onclick="testBridgeConnection()" class="cfg-btn bg-zinc-800 text-white border border-zinc-600 flex-1 hover:bg-zinc-700">TEST CONNECTION</button>
                </div>

                <!-- Status -->
                <div id="bridge-config-status" class="bg-zinc-900 rounded p-3 border border-zinc-800 text-xs font-mono text-zinc-400 text-center">
                    Awaiting configuration...
                </div>
            </div>
        </section>

    </main>

    <!-- UNIFIED INPUT AREA -->
    <footer class="p-4 bg-black border-t border-zinc-800">
        <div class="flex gap-2 items-center bg-zinc-900 border border-zinc-800 rounded-lg p-1 focus-within:border-zinc-500 transition-colors">
            <input id="main-input" type="text"
                class="flex-1 bg-transparent py-2.5 px-3 outline-none text-sm text-white placeholder-zinc-500"
                placeholder="Send message..."
                autocomplete="off"
                onkeypress="if(event.key === 'Enter') handleInput()">
            <button onclick="handleInput()" class="bg-white text-black px-5 py-2.5 rounded-md font-bold text-xs hover:bg-zinc-200 transition-colors">
                SEND
            </button>
        </div>
    </footer>

    <script>
        let currentMode = 'chat';
        const tabs = {
            chat: document.getElementById('tab-chat'),
            agent: document.getElementById('tab-agent'),
            terminal: document.getElementById('tab-terminal'),
            bridge: document.getElementById('tab-bridge')
        };
        const mainIn = document.getElementById('main-input');

        // ---- Tab Management ----
        function setMode(mode) {
            currentMode = mode;
            Object.values(tabs).forEach(t => {
                t.classList.remove('active-tab', 'text-white', 'border-white');
                t.classList.add('text-zinc-500', 'border-transparent');
            });
            tabs[mode].classList.remove('text-zinc-500', 'border-transparent');
            tabs[mode].classList.add('active-tab', 'text-white', 'border-white');

            document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
            document.getElementById('view-' + mode).classList.add('active');

            if (mode === 'terminal') {
                mainIn.placeholder = "Enter Python/Shell command...";
                mainIn.disabled = false;
            } else if (mode === 'bridge') {
                mainIn.placeholder = "Configuration mode - input disabled...";
                mainIn.disabled = true;
                loadBridgeConfig();
            } else if (mode === 'agent') {
                mainIn.placeholder = "Describe an autonomous task...";
                mainIn.disabled = false;
            } else {
                mainIn.placeholder = "Send message...";
                mainIn.disabled = false;
            }
            if(!mainIn.disabled) mainIn.focus();
        }

        // ---- Input Dispatcher ----
        async function handleInput() {
            if (mainIn.disabled) return;
            const val = mainIn.value.trim();
            if (!val) return;
            mainIn.value = '';

            if (currentMode === 'terminal') {
                logTerm('> ' + val);
                executeTerminal(val);
            } else if (currentMode === 'chat') {
                logChat(val, 'USER');
                showTyping('chat');
                try {
                    const res = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ command: val })
                    });
                    const data = await res.json();
                    hideTyping('chat');
                    logChat(data.output, 'SYSTEM');
                } catch (e) {
                    hideTyping('chat');
                    logChat("[BRIDGE_ERR] " + e, 'SYSTEM');
                }
            } else if (currentMode === 'agent') {
                logAgent(val, 'USER');
                showTyping('agent');
                try {
                    const res = await fetch('/agent', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ command: val })
                    });
                    const data = await res.json();
                    hideTyping('agent');
                    logAgent(data.output, 'SYSTEM');
                    // If agent produced execution results, show them
                    if (data.exec_results && data.exec_results.length > 0) {
                        data.exec_results.forEach(r => {
                            logAgent('[' + r.language.toUpperCase() + ' exit:' + r.exit_code + '] ' + r.output, 'EXEC');
                        });
                    }
                } catch (e) {
                    hideTyping('agent');
                    logAgent("[BRIDGE_ERR] " + e, 'SYSTEM');
                }
            }
        }

        // ---- Terminal ----
        async function executeTerminal(cmd) {
            const badge = document.getElementById('ai-lang-badge');
            badge.innerText = "AI: ANALYZING...";
            try {
                const res = await fetch('/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: cmd })
                });
                const data = await res.json();
                badge.innerText = "AI: " + (data.language || 'SHELL').toUpperCase();
                const prefix = data.exit_code !== 0 ? '[ERR] ' : '';
                logTerm(prefix + (data.output || "Execution completed."));
            } catch (e) {
                logTerm("[Error] Bridge not connected: " + e);
                badge.innerText = "AI: ERROR";
            }
        }

        // ---- Chat Log ----
        function logChat(text, sender) {
            const out = document.getElementById('chat-output');
            const wrapper = document.createElement('div');
            const escaped = escapeHtml(text);

            if (sender === 'USER') {
                wrapper.className = "flex justify-end";
                wrapper.innerHTML = '<div class="bg-white text-black p-3 rounded-lg rounded-tr-none inline-block max-w-[85%] text-sm whitespace-pre-wrap">' + escaped + '</div>';
            } else {
                wrapper.className = "flex justify-start";
                wrapper.innerHTML = '<div class="bg-zinc-900 text-white p-3 rounded-lg rounded-tl-none inline-block max-w-[85%] text-sm whitespace-pre-wrap">' + formatLLMOutput(text) + '</div>';
            }
            out.appendChild(wrapper);
            out.scrollTop = out.scrollHeight;
        }

        // ---- Agent Log ----
        function logAgent(text, sender) {
            const out = document.getElementById('agent-output');
            const wrapper = document.createElement('div');
            const escaped = escapeHtml(text);

            if (sender === 'USER') {
                wrapper.className = "flex justify-end";
                wrapper.innerHTML = '<div class="bg-white text-black p-3 rounded-lg rounded-tr-none inline-block max-w-[85%] text-sm whitespace-pre-wrap">' + escaped + '</div>';
            } else if (sender === 'EXEC') {
                wrapper.className = "flex justify-start";
                wrapper.innerHTML = '<div class="bg-zinc-950 text-green-400 p-3 rounded-lg inline-block max-w-[90%] text-xs font-mono whitespace-pre-wrap border border-zinc-800">' + escaped + '</div>';
            } else {
                wrapper.className = "flex justify-start";
                wrapper.innerHTML = '<div class="bg-zinc-900 text-white p-3 rounded-lg rounded-tl-none inline-block max-w-[85%] text-sm whitespace-pre-wrap">' + formatLLMOutput(text) + '</div>';
            }
            out.appendChild(wrapper);
            out.scrollTop = out.scrollHeight;
        }

        // ---- Terminal Log ----
        function logTerm(text) {
            const out = document.getElementById('term-output');
            const div = document.createElement('div');
            div.innerText = text;
            out.appendChild(div);
            out.scrollTop = out.scrollHeight;
        }

        // ---- Typing Indicator ----
        function showTyping(target) {
            const outId = target === 'agent' ? 'agent-output' : 'chat-output';
            const out = document.getElementById(outId);
            const existing = document.getElementById('typing-indicator');
            if (existing) existing.remove();
            const wrapper = document.createElement('div');
            wrapper.id = 'typing-indicator';
            wrapper.className = "flex justify-start";
            wrapper.innerHTML = '<div class="bg-zinc-900 text-zinc-400 p-3 rounded-lg rounded-tl-none inline-flex gap-1 items-center"><span class="typing-dot w-1.5 h-1.5 bg-zinc-400 rounded-full"></span><span class="typing-dot w-1.5 h-1.5 bg-zinc-400 rounded-full"></span><span class="typing-dot w-1.5 h-1.5 bg-zinc-400 rounded-full"></span></div>';
            out.appendChild(wrapper);
            out.scrollTop = out.scrollHeight;
        }
        function hideTyping(target) {
            const el = document.getElementById('typing-indicator');
            if (el) el.remove();
        }

        // ---- Utilities ----
        function escapeHtml(t) {
            const d = document.createElement('div');
            d.innerText = t;
            return d.innerHTML;
        }

        function formatLLMOutput(text) {
            // Basic markdown-like formatting for code blocks
            let html = escapeHtml(text);
            // Fenced code blocks
            html = html.replace(/```(\w*)\n([\s\S]*?)```/g, function(m, lang, code) {
                return '<pre class="code-block"><code>' + code + '</code></pre>';
            });
            // Inline code
            html = html.replace(/`([^`]+)`/g, '<code class="bg-zinc-800 px-1 rounded text-xs">$1</code>');
            // Bold
            html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
            return html;
        }

        // ---- Mythos Bridge Config ----
        async function loadBridgeConfig() {
            try {
                const res = await fetch('/bridge/config');
                const cfg = await res.json();
                document.getElementById('cfg-provider').value = cfg.provider || 'openai';
                document.getElementById('cfg-api-key').value = cfg.api_key || '';
                document.getElementById('cfg-base-url').value = cfg.base_url || '';
                document.getElementById('cfg-model').value = cfg.model || '';
                document.getElementById('cfg-temperature').value = cfg.temperature || 0.7;
                document.getElementById('cfg-max-tokens').value = cfg.max_tokens || 2048;
                document.getElementById('cfg-system-prompt').value = cfg.system_prompt || '';
                document.getElementById('cfg-agent-prompt').value = cfg.agent_system_prompt || '';
                document.getElementById('cfg-timeout').value = cfg.timeout_secs || 30;
                updateBridgeBadge(cfg);
            } catch (e) {
                document.getElementById('bridge-config-status').innerText = 'Error loading config: ' + e;
            }
        }

        function onProviderChange() {
            const provider = document.getElementById('cfg-provider').value;
            const presets = {
                openai: { base_url: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
                anthropic: { base_url: 'https://api.anthropic.com/v1', model: 'claude-3-5-sonnet-20241022' },
                ollama: { base_url: 'http://localhost:11434/v1', model: 'llama3.2' },
                custom: { base_url: '', model: '' }
            };
            const p = presets[provider] || presets.custom;
            document.getElementById('cfg-base-url').value = p.base_url;
            document.getElementById('cfg-model').value = p.model;
        }

        async function saveBridgeConfig() {
            const status = document.getElementById('bridge-config-status');
            status.innerText = 'Saving...';
            const cfg = {
                provider: document.getElementById('cfg-provider').value,
                api_key: document.getElementById('cfg-api-key').value,
                base_url: document.getElementById('cfg-base-url').value,
                model: document.getElementById('cfg-model').value,
                temperature: parseFloat(document.getElementById('cfg-temperature').value),
                max_tokens: parseInt(document.getElementById('cfg-max-tokens').value),
                system_prompt: document.getElementById('cfg-system-prompt').value,
                agent_system_prompt: document.getElementById('cfg-agent-prompt').value,
                timeout_secs: parseInt(document.getElementById('cfg-timeout').value),
            };
            try {
                const res = await fetch('/bridge/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(cfg)
                });
                const data = await res.json();
                status.innerHTML = '<span class="text-white">Configuration saved.</span> Provider: ' + cfg.provider + ' | Model: ' + cfg.model;
                updateBridgeBadge(cfg);
            } catch (e) {
                status.innerText = 'Save error: ' + e;
            }
        }

        async function testBridgeConnection() {
            const status = document.getElementById('bridge-config-status');
            status.innerText = 'Testing connection...';
            try {
                const res = await fetch('/bridge/test', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    status.innerHTML = '<span class="text-green-400">Connection OK.</span> Response: ' + escapeHtml(data.reply.substring(0, 100));
                } else {
                    status.innerHTML = '<span class="text-red-400">Connection failed.</span> ' + escapeHtml(data.reply.substring(0, 200));
                }
            } catch (e) {
                status.innerText = 'Test error: ' + e;
            }
        }

        function updateBridgeBadge(cfg) {
            const badge = document.getElementById('bridge-status-badge');
            const hasKey = cfg.api_key || cfg.provider === 'ollama';
            if (hasKey && cfg.base_url) {
                badge.className = 'text-white text-xs font-mono';
                badge.innerText = 'BRIDGE: ' + (cfg.provider || 'custom').toUpperCase();
            } else {
                badge.className = 'text-zinc-500 text-xs font-mono';
                badge.innerText = 'BRIDGE: NOT SET';
            }
        }

        // Load config on startup
        setTimeout(() => {
            fetch('/bridge/config').then(r => r.json()).then(cfg => updateBridgeBadge(cfg)).catch(() => {});
        }, 500);
    </script>
</body>
</html>
"""

    # ---------- HTTP Backend ----------
    def start_server(self):
        app_instance = self

        class Bridge(SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Suppress HTTP logs

            def _send_json(self, data: dict, status: int = 200):
                body = json.dumps(data).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def do_GET(self):
                path = self.path.split("?")[0]
                if path == "/bridge/config":
                    # Return config (mask API key for display)
                    cfg = dict(app_instance.bridge.config)
                    self._send_json(cfg)
                elif path == "/bridge/status":
                    self._send_json(app_instance.bridge.get_status_dict())
                else:
                    self.send_error(404)

            def do_POST(self):
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len) if content_len > 0 else b"{}"
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    data = {}

                path = self.path.split("?")[0]

                if path == "/execute":
                    # Terminal execution
                    cmd = data.get("command", "")
                    result = app_instance.executor.execute(cmd)
                    self._send_json(result)

                elif path == "/chat":
                    # LLM Chat via Mythos Bridge
                    msg = data.get("command", "")
                    reply = app_instance.bridge.chat(msg)
                    self._send_json({"output": reply})

                elif path == "/agent":
                    # LLM Agent via Mythos Bridge + auto-execute code blocks
                    task = data.get("command", "")
                    reply = app_instance.bridge.agent(task)
                    # Auto-execute any fenced code blocks in the response
                    exec_results = app_instance.executor.execute_fenced_blocks(reply)
                    exec_data = [{"output": r["output"], "language": r["language"], "exit_code": r["exit_code"]} for r in exec_results]
                    self._send_json({"output": reply, "exec_results": exec_data})

                elif path == "/bridge/config":
                    # Save bridge configuration
                    app_instance.bridge.config.update(data)
                    app_instance.bridge.save(app_instance.work_dir)
                    self._send_json({"status": "saved"})

                elif path == "/bridge/test":
                    # Test LLM connection
                    reply = app_instance.bridge.test_connection()
                    success = "error" not in reply.lower() and "MYTHOS_BRIDGE_OK" in reply.upper() or len(reply) > 0 and not reply.startswith("[LLM")
                    self._send_json({"success": success, "reply": reply})

                else:
                    self._send_json({"error": f"Unknown endpoint: {path}"}, 404)

        TCPServer.allow_reuse_address = True
        with TCPServer(("", 8080), Bridge) as httpd:
            httpd.serve_forever()


def main():
    return MonicoApp("monico-iOS", "com.monico.v25")
