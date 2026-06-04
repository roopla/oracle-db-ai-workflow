import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from agents import set_tracing_disabled
from agents.mcp import MCPServerStreamableHttp

from agent_app.oracle_agent_runner import clear_oracle_agent_session, run_oracle_agent

load_dotenv()
set_tracing_disabled(True)

app = FastAPI(title="Oracle DBA AI Agent - Agents SDK")


class ChatRequest(BaseModel):
    message: str
    session_id: str = "web_default"


class ChatResponse(BaseModel):
    answer: str
    tool_calls: list[dict]


class ClearSessionRequest(BaseModel):
    session_id: str = "web_default"


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/tools", response_class=HTMLResponse)
async def list_tools():
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:9000/mcp")

    async with MCPServerStreamableHttp(
        name="Oracle DBA MCP Server",
        params={"url": mcp_server_url},
        client_session_timeout_seconds=30,
    ) as oracle_mcp:
        tools = await oracle_mcp.list_tools()

    rows = ""
    for tool in tools:
        description = clean_description(tool.description)
        rows += f"""
        <tr>
            <td><code>{tool.name}</code></td>
            <td>{description}</td>
        </tr>
        """

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Oracle DBA MCP Tools</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 40px auto;
            background: #f7f7f7;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background: #eee;
        }}
        code {{
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <h1>Available Oracle DBA MCP Tools</h1>
    <p>Total tools: {len(tools)}</p>

    <table>
        <tr>
            <th>Tool</th>
            <th>Description</th>
        </tr>
        {rows}
    </table>
</body>
</html>
"""


def clean_description(description: str | None) -> str:
    if not description:
        return ""

    return description.strip().split("\\n")[0]


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = await run_oracle_agent(
        user_input=request.message,
        interface="web",
        session_id=request.session_id,
        max_turns=20,
    )

    return ChatResponse(
        answer=result["answer"],
        tool_calls=result["tool_calls"],
    )


@app.post("/clear-session")
async def clear_session(request: ClearSessionRequest):
    await clear_oracle_agent_session(request.session_id)

    return {
        "status": "cleared",
        "session_id": request.session_id,
    }


@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Oracle DBA AI Agent</title>

    <style>
        :root {
            --bg: #0f172a;
            --panel: #111827;
            --panel-light: #1f2937;
            --card: #ffffff;
            --muted: #9ca3af;
            --text: #e5e7eb;
            --accent: #38bdf8;
            --accent-dark: #0284c7;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --border: #334155;
            --bubble-user: #2563eb;
            --bubble-agent: #f8fafc;
            --bubble-agent-text: #111827;
            --tool-bg: #ecfeff;
            --tool-border: #67e8f9;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Inter, Arial, Helvetica, sans-serif;
            background:
                radial-gradient(circle at top left, rgba(56, 189, 248, 0.18), transparent 35%),
                radial-gradient(circle at bottom right, rgba(34, 197, 94, 0.10), transparent 30%),
                var(--bg);
            color: var(--text);
            height: 100vh;
            overflow: hidden;
        }

        .app {
            display: grid;
            grid-template-columns: 300px 1fr;
            height: 100vh;
        }

        .sidebar {
            background: rgba(15, 23, 42, 0.92);
            border-right: 1px solid var(--border);
            padding: 24px;
            overflow-y: auto;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 28px;
        }

        .logo {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--accent), var(--success));
            display: flex;
            align-items: center;
            justify-content: center;
            color: #020617;
            font-weight: 800;
            font-size: 18px;
            box-shadow: 0 10px 30px rgba(56, 189, 248, 0.25);
        }

        .brand h1 {
            font-size: 18px;
            margin: 0;
            line-height: 1.2;
        }

        .brand p {
            margin: 4px 0 0;
            font-size: 12px;
            color: var(--muted);
        }

        .status-card {
            background: rgba(31, 41, 55, 0.75);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 16px;
            margin-bottom: 22px;
        }

        .status-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 8px 0;
            font-size: 13px;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 9px;
            border-radius: 999px;
            font-size: 12px;
            background: rgba(34, 197, 94, 0.12);
            color: #86efac;
            border: 1px solid rgba(34, 197, 94, 0.35);
        }

        .dot {
            width: 7px;
            height: 7px;
            background: var(--success);
            border-radius: 50%;
        }

        .section-title {
            font-size: 12px;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin: 22px 0 10px;
        }

        .example {
            width: 100%;
            text-align: left;
            background: rgba(31, 41, 55, 0.65);
            color: var(--text);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 11px 12px;
            margin-bottom: 9px;
            cursor: pointer;
            font-size: 13px;
            transition: 0.15s ease;
        }

        .example:hover {
            border-color: var(--accent);
            transform: translateY(-1px);
            background: rgba(56, 189, 248, 0.08);
        }

        .sidebar-links {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .sidebar-links a {
            color: var(--accent);
            text-decoration: none;
            font-size: 13px;
        }

        .sidebar-links a:hover {
            text-decoration: underline;
        }

        .main {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        .topbar {
            height: 72px;
            border-bottom: 1px solid var(--border);
            background: rgba(15, 23, 42, 0.72);
            backdrop-filter: blur(12px);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 28px;
        }

        .topbar-title h2 {
            margin: 0;
            font-size: 18px;
        }

        .topbar-title p {
            margin: 4px 0 0;
            color: var(--muted);
            font-size: 13px;
        }

        .clear-btn {
            background: transparent;
            color: var(--muted);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 9px 12px;
            cursor: pointer;
        }

        .clear-btn:hover {
            color: white;
            border-color: var(--accent);
        }

        .chat-shell {
            flex: 1;
            overflow-y: auto;
            padding: 28px;
        }

        .welcome {
            max-width: 850px;
            margin: 0 auto 20px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 20px;
            padding: 22px;
        }

        .welcome h2 {
            margin: 0 0 8px;
            font-size: 24px;
        }

        .welcome p {
            color: #cbd5e1;
            line-height: 1.5;
            margin: 0;
        }

        .message {
            max-width: 850px;
            margin: 16px auto;
            display: flex;
            gap: 12px;
            animation: fadeIn 0.18s ease;
        }

        .avatar {
            width: 36px;
            height: 36px;
            min-width: 36px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 13px;
        }

        .avatar.user-avatar {
            background: var(--bubble-user);
            color: white;
        }

        .avatar.agent-avatar {
            background: linear-gradient(135deg, var(--accent), var(--success));
            color: #020617;
        }

        .bubble {
            padding: 15px 16px;
            border-radius: 16px;
            line-height: 1.55;
            overflow-x: auto;
            width: 100%;
        }

        .user-bubble {
            background: var(--bubble-user);
            color: white;
            border-top-left-radius: 4px;
        }

        .agent-bubble {
            background: var(--bubble-agent);
            color: var(--bubble-agent-text);
            border-top-left-radius: 4px;
        }

        .tool-card {
            max-width: 850px;
            margin: 10px auto 10px 48px;
            background: var(--tool-bg);
            color: #164e63;
            border: 1px solid var(--tool-border);
            border-radius: 14px;
            padding: 12px 14px;
            font-size: 13px;
        }

        .tool-title {
            font-weight: 700;
            margin-bottom: 5px;
        }

        .tool-code {
            font-family: Consolas, Monaco, monospace;
            background: rgba(255, 255, 255, 0.65);
            padding: 2px 5px;
            border-radius: 5px;
        }

        .input-bar {
            border-top: 1px solid var(--border);
            background: rgba(15, 23, 42, 0.9);
            padding: 18px 28px;
        }

        .input-inner {
            max-width: 900px;
            margin: 0 auto;
            display: flex;
            gap: 12px;
            align-items: center;
        }

        #message {
            flex: 1;
            min-height: 48px;
            max-height: 140px;
            resize: none;
            border-radius: 14px;
            border: 1px solid var(--border);
            background: #020617;
            color: white;
            padding: 14px 15px;
            font-size: 15px;
            outline: none;
        }

        #message:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.15);
        }

        .send-btn {
            height: 48px;
            padding: 0 22px;
            border: none;
            border-radius: 14px;
            background: linear-gradient(135deg, var(--accent), var(--accent-dark));
            color: white;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 10px 25px rgba(2, 132, 199, 0.25);
        }

        .send-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .typing {
            display: inline-flex;
            gap: 4px;
            align-items: center;
        }

        .typing span {
            width: 7px;
            height: 7px;
            background: #64748b;
            border-radius: 50%;
            animation: bounce 1s infinite;
        }

        .typing span:nth-child(2) {
            animation-delay: 0.15s;
        }

        .typing span:nth-child(3) {
            animation-delay: 0.3s;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            margin-top: 10px;
            font-size: 14px;
        }

        th, td {
            border: 1px solid #cbd5e1;
            padding: 8px;
            text-align: left;
        }

        th {
            background: #e2e8f0;
        }

        code {
            font-family: Consolas, Monaco, monospace;
            background: #e5e7eb;
            padding: 2px 5px;
            border-radius: 5px;
        }

        pre {
            background: #0f172a;
            color: #e5e7eb;
            padding: 12px;
            border-radius: 10px;
            overflow-x: auto;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes bounce {
            0%, 80%, 100% { transform: translateY(0); opacity: 0.5; }
            40% { transform: translateY(-4px); opacity: 1; }
        }

        @media (max-width: 850px) {
            .app {
                grid-template-columns: 1fr;
            }

            .sidebar {
                display: none;
            }

            .topbar {
                padding: 0 16px;
            }

            .chat-shell {
                padding: 16px;
            }

            .input-bar {
                padding: 14px;
            }
        }
    </style>
</head>

<body>
    <div class="app">
        <aside class="sidebar">
            <div class="brand">
                <div class="logo">DB</div>
                <div>
                    <h1>Oracle DBA AI</h1>
                    <p>Agents SDK + MCP</p>
                </div>
            </div>

            <div class="status-card">
                <div class="status-row">
                    <span>Agent</span>
                    <span class="pill"><span class="dot"></span> Online</span>
                </div>
                <div class="status-row">
                    <span>MCP</span>
                    <span id="mcpStatus">Checking...</span>
                </div>
                <div class="status-row">
                    <span>Mode</span>
                    <span>Standalone</span>
                </div>
            </div>

            <div class="section-title">Try these</div>
            <button class="example" onclick="useExample('show me all pdbs')">show me all pdbs</button>
            <button class="example" onclick="useExample('show database users')">show database users</button>
            <button class="example" onclick="useExample('show parameters for sga')">show parameters for sga</button>
            <button class="example" onclick="useExample('show tablespace usage')">show tablespace usage</button>
            <button class="example" onclick="useExample('show invalid objects')">show invalid objects</button>
            <button class="example" onclick="useExample('show blocking sessions')">show blocking sessions</button>

            <div class="section-title">Links</div>
            <div class="sidebar-links">
                <a href="/tools" target="_blank">View MCP Tools</a>
                <a href="/health" target="_blank">Health Check</a>
                <a href="/docs" target="_blank">API Docs</a>
            </div>
        </aside>

        <main class="main">
            <header class="topbar">
                <div class="topbar-title">
                    <h2>Chat with Oracle DBA Agent</h2>
                    <p>Ask about PDBs, parameters, tablespaces, sessions, users, and invalid objects.</p>
                </div>
                <button class="clear-btn" onclick="clearChat()">Clear Chat</button>
            </header>

            <section id="chat" class="chat-shell">
                <div class="welcome" id="welcome">
                    <h2>Welcome 👋</h2>
                    <p>
                        This agent uses the OpenAI Agents SDK, OpenWebUI, MCP tools, and Oracle.
                        It will show which MCP tool was selected before displaying the final answer.
                    </p>
                </div>
            </section>

            <footer class="input-bar">
                <div class="input-inner">
                    <textarea id="message" rows="1" placeholder="Ask Oracle AI..."></textarea>
                    <button id="sendBtn" class="send-btn" onclick="sendMessage()">Send</button>
                </div>
            </footer>
        </main>
    </div>

    <script>
        const chat = document.getElementById("chat");
        const messageInput = document.getElementById("message");
        const sendBtn = document.getElementById("sendBtn");
        const mcpStatus = document.getElementById("mcpStatus");

        async function checkHealth() {
            try {
                const response = await fetch("/health");
                if (response.ok) {
                    mcpStatus.innerHTML = '<span class="pill"><span class="dot"></span> Ready</span>';
                } else {
                    mcpStatus.textContent = "Issue";
                }
            } catch {
                mcpStatus.textContent = "Offline";
            }
        }

        checkHealth();

        messageInput.addEventListener("keydown", function(event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        });

        messageInput.addEventListener("input", function() {
            this.style.height = "auto";
            this.style.height = Math.min(this.scrollHeight, 140) + "px";
        });

        function useExample(text) {
            messageInput.value = text;
            messageInput.focus();
        }

        function getSessionId() {
            let sessionId = localStorage.getItem("oracle_dba_agent_session_id");

            if (!sessionId) {
                sessionId = "web_" + crypto.randomUUID();
                localStorage.setItem("oracle_dba_agent_session_id", sessionId);
            }

            return sessionId;
        }

        async function clearChat() {
            const sessionId = getSessionId();

            try {
                await fetch("/clear-session", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        session_id: sessionId
                    })
                });
            } catch (err) {
                console.log("Could not clear backend session:", err.message);
            }

            chat.innerHTML = `
                <div class="welcome" id="welcome">
                    <h2>Welcome 👋</h2>
                    <p>
                        This agent uses the OpenAI Agents SDK, OpenWebUI, MCP tools, and Oracle.
                        It will show which MCP tool was selected before displaying the final answer.
                    </p>
                </div>
            `;
        }

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            if (["exit", "quit", "clear", "clear history", "reset", "reset session"].includes(message.toLowerCase())) {
                await clearChat();
                messageInput.value = "";
                messageInput.style.height = "auto";
                return;
            }
            
            removeWelcome();

            appendMessage("user", message);
            messageInput.value = "";
            messageInput.style.height = "auto";

            const loadingId = appendLoading();
            sendBtn.disabled = true;

            try {
                const response = await fetch("/chat", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        message,
                        session_id: getSessionId()
                    })
                });

                const data = await response.json();
                removeElement(loadingId);

                if (!response.ok) {
                    appendMessage("agent", data.detail || "Request failed.");
                    return;
                }

                if (data.tool_calls && data.tool_calls.length > 0) {
                    data.tool_calls.forEach(call => appendToolCall(call));
                }

                appendMessage("agent", data.answer || "No answer returned.");
            } catch (err) {
                removeElement(loadingId);
                appendMessage("agent", "Error: " + err.message);
            } finally {
                sendBtn.disabled = false;
                messageInput.focus();
                scrollToBottom();
            }
        }

        function removeWelcome() {
            const welcome = document.getElementById("welcome");
            if (welcome) welcome.remove();
        }

        function appendMessage(role, text) {
            const wrapper = document.createElement("div");
            wrapper.className = "message";

            const avatar = document.createElement("div");
            avatar.className = "avatar " + (role === "user" ? "user-avatar" : "agent-avatar");
            avatar.textContent = role === "user" ? "You" : "AI";

            const bubble = document.createElement("div");
            bubble.className = "bubble " + (role === "user" ? "user-bubble" : "agent-bubble");
            bubble.innerHTML = renderMarkdownLite(text);

            wrapper.appendChild(avatar);
            wrapper.appendChild(bubble);
            chat.appendChild(wrapper);
            scrollToBottom();
        }

        function appendToolCall(call) {
            const div = document.createElement("div");
            div.className = "tool-card";
            div.innerHTML = `
                <div class="tool-title">MCP Tool Used</div>
                <div>Selected MCP tool: <span class="tool-code">${escapeHtml(call.tool)}</span></div>
                <div>Tool arguments: <span class="tool-code">${escapeHtml(call.arguments || "{}")}</span></div>
            `;
            chat.appendChild(div);
            scrollToBottom();
        }

        function appendLoading() {
            const id = "loading-" + Date.now();
            const wrapper = document.createElement("div");
            wrapper.className = "message";
            wrapper.id = id;

            wrapper.innerHTML = `
                <div class="avatar agent-avatar">AI</div>
                <div class="bubble agent-bubble">
                    <div class="typing">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            `;

            chat.appendChild(wrapper);
            scrollToBottom();
            return id;
        }

        function removeElement(id) {
            const el = document.getElementById(id);
            if (el) el.remove();
        }

        function scrollToBottom() {
            chat.scrollTop = chat.scrollHeight;
        }

        function escapeHtml(text) {
            return String(text)
                .replaceAll("&", "&amp;")
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;");
        }

        function renderMarkdownLite(text) {
            let safe = escapeHtml(text);

            safe = safe.replace(/```([\\s\\S]*?)```/g, "<pre>$1</pre>");
            safe = safe.replace(/`([^`]+)`/g, "<code>$1</code>");
            safe = safe.replace(/\\*\\*([^*]+)\\*\\*/g, "<strong>$1</strong>");

            const lines = safe.split("\\n");
            let html = "";
            let tableBuffer = [];

            function flushTable() {
                if (tableBuffer.length === 0) return;

                html += "<table>";
                tableBuffer.forEach((line, index) => {
                    const cells = line
                        .split("|")
                        .map(c => c.trim())
                        .filter(c => c.length > 0);

                    if (cells.length === 0) return;

                    const isSeparator = cells.every(c => /^-+$/.test(c.replaceAll(" ", "")));
                    if (isSeparator) return;

                    html += "<tr>";
                    cells.forEach(cell => {
                        html += index === 0
                            ? `<th>${cell}</th>`
                            : `<td>${cell}</td>`;
                    });
                    html += "</tr>";
                });
                html += "</table>";
                tableBuffer = [];
            }

            for (const line of lines) {
                if (line.trim().startsWith("|") && line.includes("|")) {
                    tableBuffer.push(line);
                } else {
                    flushTable();

                    if (line.trim() === "") {
                        html += "<br>";
                    } else if (line.startsWith("- ")) {
                        html += "• " + line.substring(2) + "<br>";
                    } else {
                        html += line + "<br>";
                    }
                }
            }

            flushTable();
            return html;
        }
    </script>
</body>
</html>
"""