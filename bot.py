#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║              🤖 FizzPop AI Agent Bot v5.0 — AGENT MODE         ║
║     Self-Improving AI: Chat | Embed | TTS | GitHub | Local ZIP ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import base64
import hashlib
import io
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import time
import traceback
import zipfile
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from telegram.constants import ParseMode, ChatAction

# ============================ CONFIGURATION ============================

TELEGRAM_BOT_TOKEN = "8909561772:AAGQgxrbvXbi-RACF4_Z7iiS4R7NA6Za6wU"
API_KEY = "sk-e317a237354192e26f99951f06e4882779e8a0e08e86d2f71242e8ff770bdf24"
GITHUB_TOKEN = "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"
GITHUB_API_BASE = "https://api.github.com"

API_CHAT_URL = "https://ckey.vn/v1/chat/completions"
API_EMBED_URL = "https://ckey.vn/v1/embeddings"
API_TTS_URL = "https://ckey.vn/v1/audio/speech"

# Agent work directory for local ZIP mode
AGENT_WORK_DIR = Path("/mnt/agents/output/agent_work")
AGENT_WORK_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You are FizzPop AI Agent — a self-improving autonomous AI assistant.

CORE CAPABILITIES:
1. You can write, analyze, debug, and refactor code in ANY programming language
2. You can create GitHub repositories, push files, manage branches, create PRs
3. You can analyze file structures, detect syntax errors, suggest optimizations
4. You learn from every task and improve your responses over time
5. You maintain context across long conversations and complex multi-step tasks

AGENT BEHAVIOR:
- When asked to code: provide complete, runnable, well-documented code
- When asked to debug: analyze error logs, identify root cause, provide fix
- When asked to review: check syntax, logic, security, performance, style
- When asked to architect: design scalable, maintainable systems
- Always explain your reasoning and provide alternatives when relevant
- If uncertain, say so honestly rather than hallucinate

SELF-IMPROVEMENT:
- After completing a task, reflect on what could be improved
- Remember patterns that worked well and avoid those that failed
- Maintain a mental model of the user's preferences and coding style
"""

AGENT_SYSTEM_PROMPT = """You are FizzPop AI Agent in AUTONOMOUS CODING MODE.

YOUR MISSION: Complete coding tasks end-to-end with ZERO human intervention.

CRITICAL RULES:
1. You MUST write COMPLETE, RUNNABLE code — never placeholders or pseudocode
2. You MUST create ALL necessary files for the project to work immediately
3. Every file must have proper docstrings, type hints, and error handling
4. Include requirements.txt (Python) or package.json (Node) or equivalent
5. Include README.md with setup and run instructions
6. Include .env.example if environment variables are needed
7. Write tests if applicable (test_*.py, *_test.py, or tests/ folder)

OUTPUT FORMAT — STRICT:
You MUST wrap each file in markers:
<<<FILE:filename>>>
[file content here]
<<<ENDFILE>>>

Example:
<<<FILE:main.py>>>
import asyncio
async def main():
    print("Hello World")
if __name__ == "__main__":
    asyncio.run(main())
<<<ENDFILE>>>

<<<FILE:requirements.txt>>>
asyncio
aiohttp
<<<ENDFILE>>>

REPO NAMING RULE:
- Derive repo name from task description
- Use kebab-case: lowercase, hyphens between words
- Max 30 chars, no special chars
- Examples: "fastapi-user-auth" from "FastAPI user authentication"

CODE QUALITY:
- Follow PEP 8 for Python
- Handle all edge cases
- Never hardcode secrets
- Use logging, not print
- Add __doc__ strings to modules
"""

DEFAULT_MODE = "chat"
DEFAULT_CHAT_MODEL = "deepseek-3.2"
DEFAULT_AGENT_MODEL = "mistral-medium-3.5-128b"
DEFAULT_EMBED_MODEL = "text-embedding-3-small"
DEFAULT_TTS_MODEL = "google-tts/vi"

MAX_HISTORY = 32
MAX_OUTPUT_TOKENS = 8192
STATUS_UPDATE_INTERVAL = 2.0
TELEGRAM_MSG_LIMIT = 4000
TELEGRAM_FILE_LIMIT = 20 * 1024 * 1024  # 20MB

# ============================ MODEL CATALOG ============================

CATEGORY_EMOJI = {
    "GPT": "🟢", "Claude": "🟣", "Gemini": "🔵", "GLM": "🟡",
    "Qwen": "🟠", "MiniMax": "🔴", "Mistral": "⚪", "DeepSeek": "⚫",
    "Open-source": "🟤", "Grok": "🟩", "Khác": "🟦",
}

CHAT_MODELS = {
    "GPT": [
        ("gpt-5.4-mini", "GPT-5.4 Mini"),
        ("gpt-5.2", "GPT-5.2"),
        ("gpt-5.3-codex", "GPT-5.3 Codex"),
        ("gpt-5.3-codex-high", "GPT-5.3 Codex High"),
        ("gpt-5.4", "GPT-5.4"),
        ("gpt-5.3-codex-xhigh", "GPT-5.3 Codex XHigh"),
        ("gpt-5.3-codex-low", "GPT-5.3 Codex Low"),
        ("gpt-5.3-codex-none", "GPT-5.3 Codex None"),
        ("haidinhphu1704/gpt-5.4-codex", "GPT-5.4 Codex (Chieu)"),
        ("haidinhphu1704/gpt-5.5-codex", "GPT-5.5 Codex (Chieu)"),
        ("vuduythanh2023/gpt-5.3-codex", "GPT-5.3 Codex (Vyke)"),
        ("vuduythanh2023/gpt-5.5", "GPT-5.5 (Vyke)"),
        ("thanhnhan9023/gpt-image-2", "GPT-Image-2"),
        ("thanhnhan9023/sl-gpt-5.5", "GPT-5.5 SL"),
        ("namnv/Claude Opus 4.6 + GPT 5.5", "Claude+GPT Hybrid"),
        ("tranhieu13102003/gpt-5.5[1m]", "GPT-5.5 [1M]"),
        ("vykelongthuong/GPT 5.3 Codex", "GPT-5.3 Codex (Vyke)"),
        ("vykelongthuong/GPT 5.4", "GPT-5.4 (Vyke)"),
        ("vykelongthuong/GPT 5.5", "GPT-5.5 (Vyke)"),
        ("w3leee/CodeX GPT 5.3", "CodeX GPT-5.3"),
        ("w3leee/CodeX GPT 5.4", "CodeX GPT-5.4"),
        ("w3leee/cx/gpt-5.3-codex-high", "cx GPT-5.3 High"),
        ("w3leee/GPT 5.5", "GPT-5.5 (W3leee)"),
        ("hiennqhust/gpt-5.4", "GPT-5.4 (Hien)"),
        ("hiennqhust/gpt-5.5", "GPT-5.5 (Hien)"),
    ],
    "Claude": [
        ("claude-haiku-4.5", "Claude Haiku 4.5"),
        ("claude-sonnet-4.5", "Claude Sonnet 4.5"),
        ("claude-sonnet-4.6", "Claude Sonnet 4.6"),
        ("claude-sonnet-4", "Claude Sonnet 4"),
        ("claude-sonnet-4-6", "Claude Sonnet 4-6"),
        ("claude-sonnet-4-5", "Claude Sonnet 4-5"),
        ("claude-sonnet-4.6[1m]", "Claude Sonnet 4.6 [1M]"),
        ("claude-sonnet-4-6[1m]", "Claude Sonnet 4-6 [1M]"),
        ("26479061/claude-haiku-4.5", "Claude Haiku 4.5 (2647)"),
        ("26479061/claude-sonnet-4-6", "Claude Sonnet 4-6 (2647)"),
        ("haidinhphu1704/claude-kiro-sonnet-4.5", "Claude Kiro Sonnet 4.5"),
        ("haidinhphu1704/claude-kiro-opus-4.7", "Claude Kiro Opus 4.7"),
        ("haidinhphu1704/claude-opus-4.8-kiro", "Claude Opus 4.8 Kiro"),
        ("hotrovlg/vult-claude-sonnet-4.6", "Claude Sonnet 4.6 (Vult)"),
        ("hotrovlg/vult-claude-sonnet-4.6-thinking", "Claude Sonnet 4.6 Thinking"),
        ("hotrovlg/vult-claude-opus-4.7", "Claude Opus 4.7 (Vult)"),
        ("hotrovlg/vult-claude-opus-4.7-thinking", "Claude Opus 4.7 Thinking"),
        ("hotrovlg/vult-claude-opus-4.8-thinking", "Claude Opus 4.8 Thinking"),
        ("hotrovlg/vult-claude-opus-4.7-thinking-agentic", "Claude Opus 4.7 Agentic"),
        ("hotrovlg/vult-claude-opus-4.8-thinking-agentic", "Claude Opus 4.8 Agentic"),
        ("vykelongthuong/Claude Haiku 4.5", "Claude Haiku (Vyke)"),
        ("vykelongthuong/Claude Sonnet 4.6", "Claude Sonnet 4.6 (Vyke)"),
    ],
    "Gemini": [
        ("gemini-embedding-001", "Gemini Embed 001"),
        ("gemini-embedding-2-preview", "Gemini Embed 2 Preview"),
    ],
    "GLM": [
        ("glm4.7", "GLM-4.7"),
        ("glm-5", "GLM-5"),
        ("glm-5.1", "GLM-5.1"),
        ("hiennqhust/glm-5.1", "GLM-5.1 (Hien)"),
    ],
    "Qwen": [
        ("qwen3-coder-480b-a35b-instruct", "Qwen3 Coder 480B"),
        ("deepseek-r1-distill-qwen-32b", "DeepSeek R1 Distill Qwen"),
        ("qwen3-coder-next", "Qwen3 Coder Next"),
        ("phuocanh421994/Qwen3.6 27b", "Qwen3.6 27B"),
        ("phuocanh421994/Qwen3.6 35b a3b", "Qwen3.6 35B A3B"),
        ("phuocanh421994/Qwen3.6-Flash", "Qwen3.6 Flash"),
        ("phuocanh421994/Qwen 3.6 Max Preview", "Qwen3.6 Max Preview"),
        ("phuocanh421994/Qwen 3.6 Plus", "Qwen3.6 Plus"),
        ("phuocanh421994/Qwen3.5 Plus", "Qwen3.5 Plus"),
        ("phuocanh421994/Qwen3 Coder Plus", "Qwen3 Coder Plus"),
        ("phuocanh421994/Qwen3 Max", "Qwen3 Max"),
        ("phuocanh421994/Qwen 3.7 max", "Qwen3.7 Max"),
        ("vuduythanh2023/qwen3.6-plus", "Qwen3.6 Plus (Vyke)"),
        ("vuduythanh2023/qwen3.7-max", "Qwen3.7 Max (Vyke)"),
        ("hiennqhust/qwen3.6-27b", "Qwen3.6 27B (Hien)"),
    ],
    "MiniMax": [
        ("namtran96hth/MiniMax-M2.7", "MiniMax M2.7"),
        ("minimax-m2.5", "MiniMax M2.5"),
        ("minimax-m2.1", "MiniMax M2.1"),
    ],
    "Mistral": [
        ("mistral-small-4-119b-2603", "Mistral Small 4"),
        ("chieustudio/mistral-large-3-675b-instruct-2512", "Mistral Large 3 (Chieu)"),
        ("mistral-medium-3.5-128b", "Mistral Medium 3.5"),
        ("mistral-large-3-675b-instruct-2512", "Mistral Large 3 (Official)"),
    ],
    "DeepSeek": [
        ("chieustudio/deepseek-r1", "DeepSeek R1 (Chieu)"),
        ("deepseek-3.2", "DeepSeek V3 (3.2)"),
        ("deepseek-v4-flash", "DeepSeek V4 Flash"),
        ("deepseek-v4-pro", "DeepSeek V4 Pro"),
        ("vykelongthuong/Deepseek V4 Flash", "DeepSeek V4 Flash (Vyke)"),
        ("phuocanh421994/Deepseek V4 Pro", "DeepSeek V4 Pro (Phuoc)"),
        ("hiennqhust/deepseek-v4-flash", "DeepSeek V4 Flash (Hien)"),
        ("hiennqhust/deepseek-v4-pro", "DeepSeek V4 Pro (Hien)"),
    ],
    "Open-source": [
        ("llama-nemotron-embed-vl-1b-v2", "Llama Nemotron Embed VL"),
    ],
    "Grok": [
        ("grok-4.20-thinking", "Grok 4.20 Thinking"),
        ("grok-4.20-fast", "Grok 4.20 Fast"),
        ("grok-4.3", "Grok 4.3"),
    ],
    "Khác": [
        ("kimi-k2.5", "Kimi K2.5"),
        ("kimi-k2.6", "Kimi K2.6"),
        ("hiennqhust/kimi-k2.6", "Kimi K2.6 (Hien)"),
        ("hiennqhust/greg-1-mini", "Greg-1 Mini"),
        ("yudhaekasaputra1/Xiaomi MiMo V2.5", "Xiaomi MiMo V2.5"),
        ("yudhaekasaputra1/Xiaomi MiMo V2.5 Pro", "MiMo V2.5 Pro"),
        ("hiennqhust/mimo-v2.5-pro", "MiMo V2.5 Pro (Hien)"),
    ],
}

EMBED_MODELS = {
    "Khác": [
        ("text-embedding-3-small", "Text Embed 3 Small"),
        ("pplx-embed-v1-4b", "Perplexity Embed v1"),
    ],
    "Gemini": [
        ("gemini-embedding-001", "Gemini Embed 001"),
        ("gemini-embedding-2-preview", "Gemini Embed 2 Preview"),
    ],
    "Open-source": [
        ("llama-nemotron-embed-vl-1b-v2", "Llama Nemotron Embed VL"),
    ],
}

TTS_MODELS = {
    "Khác": [
        ("google-tts/vi", "Google TTS Vi"),
        ("vi-VN-HoaiMyNeural", "HoaiMy Neural"),
        ("vi-VN-NamMinhNeural", "NamMinh Neural"),
    ],
}

def flatten_models(model_dict):
    result = []
    for cat, items in model_dict.items():
        for model_id, display in items:
            result.append((cat, model_id, display))
    return result

ALL_CHAT = flatten_models(CHAT_MODELS)
ALL_EMBED = flatten_models(EMBED_MODELS)
ALL_TTS = flatten_models(TTS_MODELS)

MODE_CONFIG = {
    "chat": {
        "name": "💬 Chat",
        "models": ALL_CHAT,
        "default": DEFAULT_CHAT_MODEL,
        "endpoint": API_CHAT_URL,
    },
    "agent": {
        "name": "🤖 Agent",
        "models": ALL_CHAT,
        "default": DEFAULT_AGENT_MODEL,
        "endpoint": API_CHAT_URL,
    },
    "embed": {
        "name": "📊 Embed",
        "models": ALL_EMBED,
        "default": DEFAULT_EMBED_MODEL,
        "endpoint": API_EMBED_URL,
    },
    "tts": {
        "name": "🔊 TTS",
        "models": ALL_TTS,
        "default": DEFAULT_TTS_MODEL,
        "endpoint": API_TTS_URL,
    },
}

# ============================ LOGGING ============================

logging.basicConfig(
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================ DATA MODELS ============================

@dataclass
class UserStats:
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_latency: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    first_seen: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    last_active: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@dataclass
class AgentTask:
    task_id: str
    description: str
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    completed_at: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    files_created: List[str] = field(default_factory=list)
    repo_url: Optional[str] = None
    local_path: Optional[str] = None
    deploy_mode: str = "github"  # github or local

@dataclass
class ConversationState:
    history: List[Dict[str, str]] = field(default_factory=list)
    mode: str = DEFAULT_MODE
    current_model: str = DEFAULT_CHAT_MODEL
    stats: UserStats = field(default_factory=UserStats)
    agent_tasks: List[AgentTask] = field(default_factory=list)
    github_username: Optional[str] = None
    preferred_style: str = "clean"
    last_error: Optional[str] = None
    self_notes: List[str] = field(default_factory=list)
    agent_deploy_mode: str = "local"  # default to local ZIP

# ============================ STATE MANAGEMENT ============================

user_states: Dict[int, ConversationState] = {}

def get_user_state(user_id: int) -> ConversationState:
    if user_id not in user_states:
        user_states[user_id] = ConversationState()
    return user_states[user_id]

def generate_task_id() -> str:
    return f"task_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"

def smart_repo_name(description: str) -> str:
    """Generate meaningful kebab-case repo name from task description."""
    # Remove common filler words
    fillers = {
        'tao', 'tạo', 'viet', 'viết', 'build', 'xay', 'xây', 'dựng', 'làm',
        'make', 'create', 'generate', 'write', 'code', 'project', 'app',
        'application', 'system', 'bot', 'api', 'service', 'website',
        'một', 'mot', 'cai', 'cái', 'cho', 'toi', 'tôi', 'cho', 'with',
        'using', 'use', 'by', 'simple', 'basic', 'advanced', 'full',
        'complete', 'fully', 'feature', 'featured'
    }

    # Clean and normalize
    text = description.lower()
    text = re.sub(r'[^\w\s-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    words = text.split()
    keywords = [w for w in words if w not in fillers and len(w) > 2][:6]

    if not keywords:
        keywords = [w for w in words if len(w) > 1][:4]

    name = '-'.join(keywords)
    name = re.sub(r'-+', '-', name).strip('-')
    name = name[:30].strip('-')

    if not name or len(name) < 3:
        name = f"fizzpop-agent-{int(time.time()) % 10000}"

    return name

def get_mode_models(mode: str):
    return MODE_CONFIG[mode]["models"]

def get_default_model(mode: str):
    return MODE_CONFIG[mode]["default"]

def get_model_display(mode: str, model_id: str) -> str:
    for cat, mid, disp in MODE_CONFIG[mode]["models"]:
        if mid == model_id:
            return f"{CATEGORY_EMOJI.get(cat, '⚪')} {disp}"
    return model_id

def get_model_category(mode: str, model_id: str) -> str:
    for cat, mid, disp in MODE_CONFIG[mode]["models"]:
        if mid == model_id:
            return cat
    return "Khác"

# ============================ UTILITIES ============================

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text.encode('utf-8')) // 4)

async def send_long_text(update: Update, text: str, filename: str = "response.txt"):
    if len(text) <= TELEGRAM_MSG_LIMIT:
        try:
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await update.message.reply_text(text)
        return

    bio = io.BytesIO(text.encode('utf-8'))
    bio.name = filename
    await update.message.reply_document(
        document=bio,
        caption=f"📄 Phản hồi quá dài ({len(text)} ký tự), đã gửi dưới dạng file."
    )

def build_metrics_footer(metrics: Dict[str, Any], state: ConversationState) -> str:
    latency = metrics.get('latency', 0)
    inp = metrics.get('input_tokens', 0)
    out = metrics.get('output_tokens', 0)
    total = inp + out
    tps = metrics.get('tps', 0)

    state.stats.total_requests += 1
    state.stats.total_input_tokens += inp
    state.stats.total_output_tokens += out
    state.stats.total_latency += latency
    state.stats.last_active = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "",
        "━" * 18,
        "📊 *Metrics*",
        f"• ⏱ Latency: `{latency:.2f}s`",
        f"• 📝 Input: `{inp}` tokens",
        f"• 💬 Output: `{out}` tokens",
        f"• 📦 Total: `{total}` tokens",
        f"• ⚡ Speed: `{tps:.1f}` tok/s"
    ]
    return "\n".join(lines)

def escape_markdown(text: str) -> str:
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for ch in chars:
        text = text.replace(ch, f'\\{ch}')
    return text

# ============================ FILE PARSER ============================

def parse_agent_files(text: str) -> Dict[str, str]:
    """Parse AI output into files using <<<FILE:filename>>> markers."""
    files = {}
    pattern = r'<<<FILE:\s*([^>\s]+)\s*>>>(.*?)<<<ENDFILE>>>'
    matches = re.findall(pattern, text, re.DOTALL)

    for filename, content in matches:
        filename = filename.strip()
        content = content.strip()
        if filename and content:
            files[filename] = content

    # Fallback: if no markers found, try to detect code blocks with filenames
    if not files:
        # Look for patterns like ```python filename.py or # filename.py
        code_block_pattern = r'```(?:\w+)?\s*\n?(?:#\s*)?([^\n]+\.\w+)\n(.*?)```'
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        for filename, content in matches:
            filename = filename.strip()
            content = content.strip()
            if filename and content and '.' in filename:
                files[filename] = content

    # Last resort: if text looks like single file code
    if not files and len(text) > 100:
        # Check if it contains import/def/class
        if any(kw in text for kw in ['import ', 'def ', 'class ', 'const ', 'function ']):
            files["main.py"] = text.strip()

    return files

# ============================ LOCAL ZIP AGENT ============================

async def save_agent_local(task_id: str, files: Dict[str, str]) -> Path:
    """Save agent files locally and return zip path."""
    task_dir = AGENT_WORK_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    for filename, content in files.items():
        # Sanitize filename
        safe_name = re.sub(r'[^\w\-\./]', '_', filename)
        file_path = task_dir / safe_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')

    # Create ZIP
    zip_path = AGENT_WORK_DIR / f"{task_id}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in task_dir.rglob('*'):
            if file_path.is_file():
                arcname = str(file_path.relative_to(task_dir))
                zf.write(file_path, arcname)

    return zip_path

# ============================ GITHUB API CLIENT ============================

class GitHubAgent:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        self.session: Optional[aiohttp.ClientSession] = None

    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def _request(self, method: str, endpoint: str, **kwargs) -> Tuple[int, Any]:
        await self.init_session()
        url = f"{GITHUB_API_BASE}{endpoint}"
        async with self.session.request(method, url, headers=self.headers, **kwargs) as resp:
            try:
                data = await resp.json()
            except:
                data = await resp.text()
            return resp.status, data

    async def get_user(self) -> Tuple[bool, Dict]:
        status, data = await self._request("GET", "/user")
        return status == 200, data

    async def create_repo(self, name: str, description: str = "", private: bool = False) -> Tuple[bool, Dict]:
        payload = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": True
        }
        status, data = await self._request("POST", "/user/repos", json=payload)
        return status == 201, data

    async def get_file(self, owner: str, repo: str, path: str, branch: str = "main") -> Tuple[bool, Dict]:
        status, data = await self._request("GET", f"/repos/{owner}/{repo}/contents/{path}?ref={branch}")
        return status == 200, data

    async def create_file(self, owner: str, repo: str, path: str, content: str, message: str, branch: str = "main") -> Tuple[bool, Dict]:
        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        payload = {"message": message, "content": encoded, "branch": branch}
        status, data = await self._request("PUT", f"/repos/{owner}/{repo}/contents/{path}", json=payload)
        return status in (200, 201), data

    async def update_file(self, owner: str, repo: str, path: str, content: str, message: str, sha: str, branch: str = "main") -> Tuple[bool, Dict]:
        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        payload = {"message": message, "content": encoded, "sha": sha, "branch": branch}
        status, data = await self._request("PUT", f"/repos/{owner}/{repo}/contents/{path}", json=payload)
        return status in (200, 201), data

    async def delete_file(self, owner: str, repo: str, path: str, message: str, sha: str, branch: str = "main") -> Tuple[bool, Dict]:
        payload = {"message": message, "sha": sha, "branch": branch}
        status, data = await self._request("DELETE", f"/repos/{owner}/{repo}/contents/{path}", json=payload)
        return status == 200, data

    async def list_files(self, owner: str, repo: str, path: str = "", branch: str = "main") -> Tuple[bool, List]:
        endpoint = f"/repos/{owner}/{repo}/contents/{path}?ref={branch}" if path else f"/repos/{owner}/{repo}/contents?ref={branch}"
        status, data = await self._request("GET", endpoint)
        if status == 200 and isinstance(data, list):
            return True, data
        return False, data if isinstance(data, list) else []

    async def create_branch(self, owner: str, repo: str, new_branch: str, from_branch: str = "main") -> Tuple[bool, Dict]:
        status, data = await self._request("GET", f"/repos/{owner}/{repo}/git/refs/heads/{from_branch}")
        if status != 200:
            return False, data
        sha = data.get("object", {}).get("sha", "")
        payload = {"ref": f"refs/heads/{new_branch}", "sha": sha}
        status, data = await self._request("POST", f"/repos/{owner}/{repo}/git/refs", json=payload)
        return status == 201, data

    async def create_pr(self, owner: str, repo: str, title: str, head: str, base: str, body: str = "") -> Tuple[bool, Dict]:
        payload = {"title": title, "head": head, "base": base, "body": body}
        status, data = await self._request("POST", f"/repos/{owner}/{repo}/pulls", json=payload)
        return status == 201, data

    async def get_commits(self, owner: str, repo: str, branch: str = "main", per_page: int = 10) -> Tuple[bool, List]:
        status, data = await self._request("GET", f"/repos/{owner}/{repo}/commits?sha={branch}&per_page={per_page}")
        if status == 200 and isinstance(data, list):
            return True, data
        return False, []

github_agent = GitHubAgent(GITHUB_TOKEN)

# ============================ AI API CLIENTS ============================

async def call_chat_api(
    session: aiohttp.ClientSession,
    model_id: str,
    messages: List[Dict[str, str]],
    status_msg: Any,
    system_prompt: str = SYSTEM_PROMPT,
    max_tokens: int = MAX_OUTPUT_TOKENS,
) -> Tuple[str, Dict[str, Any]]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    msgs = []
    has_system = False
    for m in messages:
        if m.get("role") == "system":
            if not has_system:
                msgs.append({"role": "system", "content": system_prompt})
                has_system = True
        else:
            msgs.append(m)
    if not has_system:
        msgs.insert(0, {"role": "system", "content": system_prompt})

    payload = {
        "model": model_id,
        "messages": msgs,
        "temperature": 0.7,
        "max_tokens": max_tokens
    }

    start_time = time.time()

    async def _update_status():
        dots = 0
        while True:
            try:
                await asyncio.sleep(STATUS_UPDATE_INTERVAL)
                elapsed = time.time() - start_time
                dots = (dots + 1) % 4
                await status_msg.edit_text(
                    f"⏳ *Đang suy nghĩ{'·' * dots}{' ' * (3-dots)}*\n\n"
                    f"🤖 *Model:* `{model_id}`\n"
                    f"⏱ *Thời gian chờ:* `{elapsed:.1f}s`\n"
                    f"💡 *Trạng thái:* `Đang tạo phản hồi...`",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                pass

    status_task = asyncio.create_task(_update_status())

    try:
        timeout = aiohttp.ClientTimeout(total=None, connect=30)
        async with session.post(API_CHAT_URL, headers=headers, json=payload, timeout=timeout) as resp:
            if resp.status != 200:
                error_body = await resp.text()
                raise aiohttp.ClientResponseError(
                    resp.request_info, resp.history, status=resp.status,
                    message=f"API Error {resp.status}: {error_body[:500]}"
                )
            result = await resp.json()
    except Exception:
        raise
    finally:
        status_task.cancel()
        try:
            await status_task
        except asyncio.CancelledError:
            pass

    latency = time.time() - start_time

    if not isinstance(result, dict):
        raise ValueError(f"Invalid API response type: {type(result)}")

    choices = result.get('choices', [])
    if not choices:
        raise ValueError(f"No choices in API response")

    content = choices[0].get('message', {}).get('content', '')
    if not content:
        raise ValueError("Empty content from API")

    usage = result.get('usage', {})
    input_tokens = usage.get('prompt_tokens', 0)
    output_tokens = usage.get('completion_tokens', 0)

    if input_tokens == 0:
        input_tokens = sum(estimate_tokens(m.get('content', '')) for m in msgs)
    if output_tokens == 0:
        output_tokens = estimate_tokens(content)

    metrics = {
        'latency': latency,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': input_tokens + output_tokens,
        'tps': output_tokens / latency if latency > 0 else 0
    }

    return content, metrics

async def call_embed_api(
    session: aiohttp.ClientSession,
    model_id: str,
    text_input: str,
    status_msg: Any,
) -> Tuple[str, Dict[str, Any], str]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {"model": model_id, "input": text_input}

    start_time = time.time()

    async def _update_status():
        dots = 0
        while True:
            try:
                await asyncio.sleep(STATUS_UPDATE_INTERVAL)
                elapsed = time.time() - start_time
                dots = (dots + 1) % 4
                await status_msg.edit_text(
                    f"⏳ *Đang embed{'·' * dots}{' ' * (3-dots)}*\n\n"
                    f"🤖 *Model:* `{model_id}`\n"
                    f"⏱ *Thời gian chờ:* `{elapsed:.1f}s`\n"
                    f"💡 *Trạng thái:* `Đang tính vector...`",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                pass

    status_task = asyncio.create_task(_update_status())

    try:
        timeout = aiohttp.ClientTimeout(total=None, connect=30)
        async with session.post(API_EMBED_URL, headers=headers, json=payload, timeout=timeout) as resp:
            if resp.status != 200:
                error_body = await resp.text()
                raise aiohttp.ClientResponseError(
                    resp.request_info, resp.history, status=resp.status,
                    message=f"API Error {resp.status}: {error_body[:500]}"
                )
            result = await resp.json()
    except Exception:
        raise
    finally:
        status_task.cancel()
        try:
            await status_task
        except asyncio.CancelledError:
            pass

    latency = time.time() - start_time

    if not isinstance(result, dict):
        raise ValueError(f"Invalid API response type: {type(result)}")

    data = result.get('data', [])
    if not data:
        raise ValueError("No embedding data returned")

    embedding = data[0].get('embedding', [])
    dims = len(embedding)
    preview = embedding[:5]
    preview_str = ", ".join([f"{v:.6f}" for v in preview])

    content = (
        f"📊 *Embedding Result*\n"
        f"{'━' * 20}\n"
        f"• 📐 Dimensions: `{dims}`\n"
        f"• 🔢 Preview (first 5): `{preview_str}...`\n\n"
        f"📄 *Full vector* đã được lưu trong file đính kèm."
    )

    full_vector_text = f"Model: {model_id}\nDimensions: {dims}\n\nEmbedding Vector:\n{json.dumps(embedding, indent=2)}"

    usage = result.get('usage', {})
    input_tokens = usage.get('prompt_tokens', 0) or usage.get('input_tokens', 0) or estimate_tokens(text_input)

    metrics = {
        'latency': latency,
        'input_tokens': input_tokens,
        'output_tokens': 0,
        'total_tokens': input_tokens,
        'tps': 0
    }

    return content, metrics, full_vector_text

async def call_tts_api(
    session: aiohttp.ClientSession,
    model_id: str,
    text_input: str,
    status_msg: Any,
) -> Tuple[bytes, Dict[str, Any]]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {"model": model_id, "input": text_input, "voice": "alloy"}

    start_time = time.time()

    async def _update_status():
        dots = 0
        while True:
            try:
                await asyncio.sleep(STATUS_UPDATE_INTERVAL)
                elapsed = time.time() - start_time
                dots = (dots + 1) % 4
                await status_msg.edit_text(
                    f"⏳ *Đang tổng hợp giọng nói{'·' * dots}{' ' * (3-dots)}*\n\n"
                    f"🤖 *Model:* `{model_id}`\n"
                    f"⏱ *Thời gian chờ:* `{elapsed:.1f}s`\n"
                    f"💡 *Trạng thái:* `Đang tạo audio...`",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                pass

    status_task = asyncio.create_task(_update_status())

    try:
        timeout = aiohttp.ClientTimeout(total=None, connect=30)
        async with session.post(API_TTS_URL, headers=headers, json=payload, timeout=timeout) as resp:
            if resp.status != 200:
                error_body = await resp.text()
                raise aiohttp.ClientResponseError(
                    resp.request_info, resp.history, status=resp.status,
                    message=f"API Error {resp.status}: {error_body[:500]}"
                )
            audio_bytes = await resp.read()
    except Exception:
        raise
    finally:
        status_task.cancel()
        try:
            await status_task
        except asyncio.CancelledError:
            pass

    latency = time.time() - start_time

    if not audio_bytes or len(audio_bytes) < 100:
        raise ValueError("Received empty or invalid audio data")

    metrics = {
        'latency': latency,
        'input_tokens': estimate_tokens(text_input),
        'output_tokens': 0,
        'total_tokens': estimate_tokens(text_input),
        'tps': 0
    }

    return audio_bytes, metrics

# ============================ AGENT INTELLIGENCE ============================

async def agent_self_reflect(task: AgentTask, state: ConversationState) -> str:
    reflection = (
        f"🧠 *Self-Reflection*\n"
        f"{'━' * 20}\n"
        f"• Task: `{task.task_id}`\n"
        f"• Status: {task.status}\n"
    )
    if task.error:
        reflection += f"• Error pattern recorded: `{task.error[:100]}`\n"
        state.self_notes.append(f"Avoid: {task.error[:200]}")
    else:
        reflection += f"• Success pattern recorded\n"
        state.self_notes.append(f"Success: {task.description[:200]}")

    state.self_notes = state.self_notes[-50:]
    return reflection

async def agent_analyze_code(code: str, language: str = "python") -> str:
    issues = []

    if language == "python":
        try:
            compile(code, '<string>', 'exec')
            issues.append("✅ Syntax: Valid Python")
        except SyntaxError as e:
            issues.append(f"❌ Syntax Error: Line {e.lineno}: {e.msg}")

        if "import " in code and "if __name__" not in code and len(code.split('\n')) > 20:
            issues.append("⚠️ No `if __name__ == '__main__'` guard detected")

        if "except:" in code:
            issues.append("⚠️ Bare `except:` found — use specific exceptions")

        if "print(" in code and "logging" not in code:
            issues.append("💡 Consider using `logging` instead of `print()`")

        if "TODO" in code or "FIXME" in code:
            issues.append("📝 TODO/FIXME markers found in code")

        if code.count('def ') > 15:
            issues.append("📊 High function count — consider modularizing")

    return "\n".join(issues) if issues else "✅ Code analysis: No obvious issues found"

# ============================ COMMAND HANDLERS ============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    mode_name = MODE_CONFIG[state.mode]["name"]
    model_disp = get_model_display(state.mode, state.current_model)

    welcome = (
        f"╔══════════════════════╗\n"
        f"║   🤖 *FizzPop AI*    ║\n"
        f"║   *AGENT v5.0*       ║\n"
        f"╚══════════════════════╝\n\n"
        f"👋 Chào mừng *{update.effective_user.first_name or 'bạn'}*!\n\n"
        f"🧠 *AI Agent tự chủ — Tự code, tự sửa lỗi, tự học*\n\n"
        f"📦 *4 Chế độ:*\n"
        f"• 💬 Chat — Hỏi đáp AI thông thường\n"
        f"• 🤖 Agent — Tự động code + deploy\n"
        f"• 📊 Embed — Text → Vector embedding\n"
        f"• 🔊 TTS — Text → Giọng nói MP3\n\n"
        f"🚀 Mode: {mode_name} | Model: {model_disp}\n\n"
        f"📚 *Lệnh chính:*\n"
        f"• /models — Chọn model\n"
        f"• /mode — Đổi chế độ\n"
        f"• /agent — Chạy agent task\n"
        f"• /git — GitHub commands\n"
        f"• /analyze — Phân tích code\n"
        f"• /status — Trạng thái\n"
        f"• /stats — Thống kê\n"
        f"• /reset — Xóa lịch sử\n"
        f"• /help — Chi tiết"
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        f"📖 *Hướng Dẫn Sử Dụng — FizzPop AI Agent*\n"
        f"{'━' * 22}\n\n"
        f"🚀 *Lệnh chính:*\n"
        f"• `/start` — Khởi động\n"
        f"• `/models` — Danh sách model (nút bấm)\n"
        f"• `/switch <số>` — Đổi model nhanh\n"
        f"• `/mode` — Đổi chế độ chat/agent/embed/tts\n"
        f"• `/status` — Xem trạng thái hiện tại\n"
        f"• `/stats` — Thống kê sử dụng\n"
        f"• `/reset` — Xóa lịch sử + tasks + context\n"
        f"• `/help` — Hiển thị trợ giúp này\n\n"
        f"🤖 *Agent Commands:*\n"
        f"• `/agent <mô tả>` — Yêu cầu AI tự code & deploy\n"
        f"  - Mặc định deploy dạng file .zip local\n"
        f"  - Hoặc: `/agent github <mô tả>` để push GitHub\n"
        f"  - Hoặc: `/agent local <mô tả>` để lưu file .zip\n"
        f"• `/git` — Danh sách lệnh GitHub\n"
        f"  - `/git repo <tên>` — Tạo repository\n"
        f"  - `/git push <owner/repo> <path>` — Push file\n"
        f"  - `/git get <owner/repo> <path>` — Đọc file\n"
        f"  - `/git list <owner/repo> [path]` — Liệt kê files\n"
        f"  - `/git branch <owner/repo> <branch>` — Tạo branch\n"
        f"  - `/git pr <owner/repo> <title> <head> <base>` — Tạo PR\n"
        f"  - `/git delete <owner/repo> <path>` — Xóa file\n"
        f"  - `/git commits <owner/repo>` — Xem lịch sử commit\n"
        f"• `/analyze <code>` hoặc reply code — Phân tích code\n"
        f"• `/tasks` — Xem lịch sử agent tasks\n"
        f"• `/learn` — Xem ghi chú tự học của AI\n\n"
        f"💡 *Tính năng nổi bật:*\n"
        f"• ⏱ *Không timeout* — Chờ AI trả lời dù lâu\n"
        f"• 📊 *Metrics real-time* — Latency, tokens, tok/s\n"
        f"• 🧠 *Nhớ context* — Giữ {MAX_HISTORY} tin nhắn\n"
        f"• 🤖 *Self-improving* — AI tự ghi nhận lỗi & cải thiện\n"
        f"• 📁 *File output* — Phản hồi dài → file .txt\n"
        f"• 📦 *Agent deploy* — Code → .zip hoặc GitHub\n"
        f"• 🔊 *TTS* — Trả về file MP3\n\n"
        f"⚠️ *Lưu ý:*\n"
        f"• Dùng `/reset` nếu AI bị lẫn ngữ cảnh\n"
        f"• Agent mode mặc định lưu file .zip (không cần token)\n"
        f"• Để push GitHub, dùng `/agent github <task>`"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def show_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    mode = state.mode
    mode_name = MODE_CONFIG[mode]["name"]
    current_model = state.current_model
    models_list = MODE_CONFIG[mode]["models"]

    keyboard = []
    row = []

    for idx, (cat, model_id, display) in enumerate(models_list, 1):
        prefix = "✅ " if model_id == current_model else ""
        emoji = CATEGORY_EMOJI.get(cat, "⚪")
        btn_text = f"{prefix}{idx}.{emoji}{display[:18]}"
        button = InlineKeyboardButton(btn_text, callback_data=f"model_{mode}_{idx}")
        row.append(button)
        if len(row) == 1:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔄 Làm mới", callback_data="refresh_models")])

    header = (
        f"📂 *Danh Sách Model — {mode_name}*\n"
        f"{'━' * 22}\n"
        f"✅ = Đang dùng: `{get_model_display(mode, current_model)}`\n"
        f"📊 Tổng: {len(models_list)} models\n\n"
        f"👇 *Chọn model:*"
    )

    await update.message.reply_text(
        header,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def model_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    state = get_user_state(user_id)
    data = query.data

    if data == "refresh_models":
        await query.edit_message_text("🔄 Đang làm mới...")
        mode = state.mode
        mode_name = MODE_CONFIG[mode]["name"]
        current_model = state.current_model
        models_list = MODE_CONFIG[mode]["models"]

        keyboard = []
        row = []
        for idx, (cat, model_id, display) in enumerate(models_list, 1):
            prefix = "✅ " if model_id == current_model else ""
            emoji = CATEGORY_EMOJI.get(cat, "⚪")
            btn_text = f"{prefix}{idx}.{emoji}{display[:18]}"
            button = InlineKeyboardButton(btn_text, callback_data=f"model_{mode}_{idx}")
            row.append(button)
            if len(row) == 1:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔄 Làm mới", callback_data="refresh_models")])

        await query.edit_message_text(
            f"📂 *Danh Sách Model — {mode_name}*\n{'━' * 22}\n✅ = Đang dùng\n\n👇 *Chọn model:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("model_"):
        parts = data.split("_")
        if len(parts) >= 3:
            mode = parts[1]
            try:
                choice = int(parts[2])
                models_list = MODE_CONFIG[mode]["models"]

                if 1 <= choice <= len(models_list):
                    cat, selected_id, selected_disp = models_list[choice - 1]
                    state.mode = mode
                    state.current_model = selected_id

                    await query.edit_message_text(
                        f"✅ *Đã chuyển!*\n\n"
                        f"🔄 Mode: *{MODE_CONFIG[mode]['name']}*\n"
                        f"🤖 Model: *{CATEGORY_EMOJI.get(cat, '⚪')} {selected_disp}*\n"
                        f"🆔 ID: `{selected_id}`\n\n"
                        f"💡 Gõ `/reset` nếu muốn xóa ngữ cảnh cũ.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await query.edit_message_text("❌ Số không hợp lệ.", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await query.edit_message_text("❌ Lỗi xử lý.", parse_mode=ParseMode.MARKDOWN)

async def switch_model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ *Cú pháp:* `/switch <số>`\nVí dụ: `/switch 2`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        choice = int(context.args[0])
        user_id = update.effective_user.id
        state = get_user_state(user_id)
        mode = state.mode
        models_list = MODE_CONFIG[mode]["models"]

        if 1 <= choice <= len(models_list):
            cat, selected_id, selected_disp = models_list[choice - 1]
            state.current_model = selected_id

            await update.message.reply_text(
                f"✅ *Đã chuyển model!*\n\n"
                f"🤖 {CATEGORY_EMOJI.get(cat, '⚪')} *{selected_disp}*\n"
                f"🆔 `{selected_id}`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                f"❌ Chọn số từ 1 đến {len(models_list)}.",
                parse_mode=ParseMode.MARKDOWN
            )
    except ValueError:
        await update.message.reply_text(
            "❌ Vui lòng nhập số hợp lệ.",
            parse_mode=ParseMode.MARKDOWN
        )

async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)

    if not context.args:
        current = state.mode
        keyboard = []
        for mode_key, mode_info in MODE_CONFIG.items():
            prefix = "✅ " if mode_key == current else ""
            keyboard.append([InlineKeyboardButton(
                f"{prefix}{mode_info['name']}",
                callback_data=f"setmode_{mode_key}"
            )])

        await update.message.reply_text(
            f"🔄 *Chọn chế độ hoạt động:*\n"
            f"Hiện tại: {MODE_CONFIG[current]['name']}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    mode_arg = context.args[0].lower()
    if mode_arg in MODE_CONFIG:
        state.mode = mode_arg
        state.current_model = MODE_CONFIG[mode_arg]["default"]
        state.history = []

        await update.message.reply_text(
            f"✅ *Đã chuyển chế độ!*\n\n"
            f"🔄 Mode: *{MODE_CONFIG[mode_arg]['name']}*\n"
            f"🤖 Model mặc định: `{state.current_model}`\n"
            f"🗑 Đã xóa lịch sử cũ.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "❌ *Chế độ không hợp lệ!*\n"
            "Chọn: `chat`, `agent`, `embed`, hoặc `tts`",
            parse_mode=ParseMode.MARKDOWN
        )

async def mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    state = get_user_state(user_id)
    data = query.data

    if data.startswith("setmode_"):
        mode_key = data.replace("setmode_", "")
        if mode_key in MODE_CONFIG:
            state.mode = mode_key
            state.current_model = MODE_CONFIG[mode_key]["default"]
            state.history = []

            await query.edit_message_text(
                f"✅ *Đã chuyển chế độ!*\n\n"
                f"🔄 Mode: *{MODE_CONFIG[mode_key]['name']}*\n"
                f"🤖 Model: `{state.current_model}`\n"
                f"🗑 Đã xóa lịch sử cũ.",
                parse_mode=ParseMode.MARKDOWN
            )

async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_states:
        user_states[user_id].history = []
        user_states[user_id].agent_tasks = []

    await update.message.reply_text(
        "🗑 *Đã xóa toàn bộ!*\n"
        "🆕 Ngữ cảnh + tasks + history mới.",
        parse_mode=ParseMode.MARKDOWN
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)

    history_len = len(state.history)
    mode_name = MODE_CONFIG[state.mode]["name"]
    model_disp = get_model_display(state.mode, state.current_model)
    cat = get_model_category(state.mode, state.current_model)
    task_count = len(state.agent_tasks)
    completed = sum(1 for t in state.agent_tasks if t.status == "completed")
    failed = sum(1 for t in state.agent_tasks if t.status == "failed")

    status = (
        f"ℹ️ *Trạng Thái Agent*\n"
        f"{'━' * 20}\n\n"
        f"🔄 *Mode:* {mode_name}\n"
        f"🤖 *Model:* {model_disp}\n"
        f"🏷 *Category:* `{cat}`\n"
        f"🆔 *ID:* `{state.current_model}`\n"
        f"💬 *History:* `{history_len // 2}` cặp\n"
        f"📝 *Tin nhắn lưu:* `{history_len}/{MAX_HISTORY * 2}`\n"
        f"🤖 *Agent tasks:* `{completed}✅ {failed}❌ {task_count - completed - failed}⏳`\n"
        f"🧠 *Self-notes:* `{len(state.self_notes)}` ghi chú\n"
        f"📦 *Deploy mode:* `{state.agent_deploy_mode}`\n"
        f"📅 *Bắt đầu:* `{state.stats.first_seen}`\n"
        f"🕐 *Hoạt động cuối:* `{state.stats.last_active}`"
    )
    await update.message.reply_text(status, parse_mode=ParseMode.MARKDOWN)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    s = state.stats

    avg_latency = s.total_latency / s.total_requests if s.total_requests > 0 else 0

    stats_text = (
        f"📊 *Thống Kê Sử Dụng*\n"
        f"{'━' * 20}\n\n"
        f"🔢 *Request:* `{s.total_requests}`\n"
        f"📝 *Input tokens:* `{s.total_input_tokens}`\n"
        f"💬 *Output tokens:* `{s.total_output_tokens}`\n"
        f"📦 *Tổng tokens:* `{s.total_input_tokens + s.total_output_tokens}`\n"
        f"⏱ *Tổng latency:* `{s.total_latency:.2f}s`\n"
        f"⚡ *Latency TB:* `{avg_latency:.2f}s`\n"
        f"✅ *Tasks thành công:* `{s.tasks_completed}`\n"
        f"❌ *Tasks thất bại:* `{s.tasks_failed}`\n"
        f"📅 *Bắt đầu:* `{s.first_seen}`\n"
        f"🕐 *Cuối:* `{s.last_active}`"
    )
    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)

    if not state.agent_tasks:
        await update.message.reply_text(
            "📭 *Chưa có agent task nào.*\n\n"
            "Dùng `/agent <mô tả>` để bắt đầu.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    msg = f"🤖 *Lịch Sử Agent Tasks*\n{'━' * 22}\n\n"
    for i, task in enumerate(state.agent_tasks[-10:], 1):
        status_emoji = {"completed": "✅", "failed": "❌", "running": "🔄", "pending": "⏳"}.get(task.status, "❓")
        deploy = f"📦 {task.deploy_mode}"
        if task.repo_url:
            deploy = f"🔗 GitHub"
        elif task.local_path:
            deploy = f"📦 Local ZIP"
        msg += (
            f"{i}. {status_emoji} `{task.task_id}`\n"
            f"   📝 {task.description[:40]}...\n"
            f"   {deploy} | ⏰ {task.created_at}\n\n"
        )

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)

    if not state.self_notes:
        await update.message.reply_text(
            "🧠 *Chưa có ghi chú tự học.*\n"
            "AI sẽ tự động ghi nhận sau mỗi task.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    msg = f"🧠 *Ghi Chú Tự Học Của AI*\n{'━' * 22}\n\n"
    for i, note in enumerate(state.self_notes[-20:], 1):
        msg += f"{i}. `{note[:100]}`\n"

    await send_long_text(update, msg, filename="self_notes.txt")

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    code = ""
    if update.message.reply_to_message and update.message.reply_to_message.text:
        code = update.message.reply_to_message.text
    elif context.args:
        code = " ".join(context.args)

    if not code:
        await update.message.reply_text(
            "❌ *Cung cấp code để phân tích:*\n"
            "• Reply vào tin nhắn chứa code và gõ `/analyze`\n"
            "• Hoặc: `/analyze <code>`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    result = await agent_analyze_code(code)

    await update.message.reply_text(
        f"🔍 *Kết Quả Phân Tích Code*\n"
        f"{'━' * 22}\n\n"
        f"```{result}```",
        parse_mode=ParseMode.MARKDOWN
    )

async def deploy_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)

    if not context.args:
        current = state.agent_deploy_mode
        keyboard = [
            [InlineKeyboardButton("✅ Local ZIP" if current == "local" else "Local ZIP", callback_data="deploy_local")],
            [InlineKeyboardButton("✅ GitHub" if current == "github" else "GitHub", callback_data="deploy_github")],
        ]
        await update.message.reply_text(
            f"📦 *Chọn chế độ deploy Agent:*\n"
            f"Hiện tại: `{current}`\n\n"
            f"• *local* — Lưu file .zip gửi qua Telegram\n"
            f"• *github* — Push lên GitHub repository",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    mode = context.args[0].lower()
    if mode in ("local", "github"):
        state.agent_deploy_mode = mode
        await update.message.reply_text(
            f"✅ *Đã chuyển deploy mode!*\n\n"
            f"📦 Mode: *{mode.upper()}*\n\n"
            f"{'• File ZIP sẽ được gửi qua Telegram' if mode == 'local' else '• Code sẽ được push lên GitHub'}\n"
            f"💡 Dùng `/agent <task>` để chạy.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "❌ *Chọn `local` hoặc `github`*",
            parse_mode=ParseMode.MARKDOWN
        )

async def deploy_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    state = get_user_state(user_id)
    data = query.data

    if data == "deploy_local":
        state.agent_deploy_mode = "local"
        await query.edit_message_text(
            "✅ *Deploy mode: LOCAL ZIP*\n\n"
            "📦 Agent sẽ lưu code thành file .zip\n"
            "💡 Dùng `/agent <task>` để chạy.",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "deploy_github":
        state.agent_deploy_mode = "github"
        await query.edit_message_text(
            "✅ *Deploy mode: GITHUB*\n\n"
            "🔗 Agent sẽ push code lên GitHub\n"
            "💡 Dùng `/agent <task>` để chạy.",
            parse_mode=ParseMode.MARKDOWN
        )

# ============================ GITHUB COMMANDS ============================

async def git_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            f"🌐 *GitHub Agent Commands*\n"
            f"{'━' * 22}\n\n"
            f"📦 *Repository:*\n"
            f"• `/git repo <tên> [description]` — Tạo repo mới\n"
            f"• `/git get <owner/repo> <path>` — Đọc file\n"
            f"• `/git list <owner/repo> [path]` — Liệt kê files\n"
            f"• `/git commits <owner/repo>` — Xem commits\n\n"
            f"📝 *File Operations:*\n"
            f"• `/git push <owner/repo> <path>` — Push file (reply code)\n"
            f"• `/git update <owner/repo> <path>` — Update file (reply code)\n"
            f"• `/git delete <owner/repo> <path>` — Xóa file\n\n"
            f"🌿 *Branch & PR:*\n"
            f"• `/git branch <owner/repo> <new_branch>` — Tạo branch\n"
            f"• `/git pr <owner/repo> <title> <head> <base>` — Tạo PR\n\n"
            f"💡 *Mẹo:* Dùng reply để push code dài",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    subcmd = context.args[0].lower()

    if subcmd == "repo":
        await _git_repo(update, context)
    elif subcmd == "push":
        await _git_push(update, context)
    elif subcmd == "get":
        await _git_get(update, context)
    elif subcmd == "list":
        await _git_list(update, context)
    elif subcmd == "branch":
        await _git_branch(update, context)
    elif subcmd == "pr":
        await _git_pr(update, context)
    elif subcmd == "delete":
        await _git_delete(update, context)
    elif subcmd == "commits":
        await _git_commits(update, context)
    elif subcmd == "update":
        await _git_update(update, context)
    else:
        await update.message.reply_text(
            f"❌ *Lệnh GitHub không hợp lệ:* `{subcmd}`\n"
            f"Dùng `/git` để xem danh sách lệnh.",
            parse_mode=ParseMode.MARKDOWN
        )

async def _git_repo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ *Cú pháp:* `/git repo <tên> [description]`\n"
            "Ví dụ: `/git repo my-project Bot AI của tôi`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    repo_name = context.args[1]
    description = " ".join(context.args[2:]) if len(context.args) > 2 else ""
    private = "private" in description.lower()
    if private:
        description = description.replace("private", "").strip()

    status_msg = await update.message.reply_text(
        f"⏳ *Đang tạo repository...*\n"
        f"📦 `{repo_name}`",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        success, data = await github_agent.create_repo(repo_name, description, private)
        if success:
            repo_url = data.get("html_url", "")
            clone_url = data.get("clone_url", "")
            await status_msg.edit_text(
                f"✅ *Repository đã tạo!*\n\n"
                f"📦 *Tên:* `{repo_name}`\n"
                f"🔗 *URL:* {repo_url}\n"
                f"📥 *Clone:* `{clone_url}`\n"
                f"🔒 *Private:* `{'Có' if private else 'Không'}`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(
                f"❌ *Lỗi tạo repo:*\n`{error[:400]}`",
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        await status_msg.edit_text(
            f"⚠️ *Lỗi:* `{str(e)[:400]}`",
            parse_mode=ParseMode.MARKDOWN
        )

async def _git_push(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ *Cú pháp:* `/git push <owner/repo> <path>`\n"
            "Reply vào tin nhắn chứa code, hoặc thêm content sau path.\n"
            "Ví dụ: `/git push user/repo src/main.py` (reply code)",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    repo_path = context.args[1]
    file_path = context.args[2]

    if "/" not in repo_path:
        await update.message.reply_text("❌ *Format:* `owner/repo`", parse_mode=ParseMode.MARKDOWN)
        return

    owner, repo = repo_path.split("/", 1)

    content = ""
    if update.message.reply_to_message and update.message.reply_to_message.text:
        content = update.message.reply_to_message.text
    elif len(context.args) > 3:
        content = " ".join(context.args[3:])

    if not content:
        await update.message.reply_text(
            "❌ *Thiếu nội dung file!*\n"
            "Reply vào tin nhắn chứa code hoặc thêm content sau path.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    status_msg = await update.message.reply_text(
        f"⏳ *Đang push file...*\n"
        f"📁 `{file_path}` → `{repo_path}`",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        success, data = await github_agent.create_file(
            owner, repo, file_path, content,
            f"Add {file_path} via FizzPop Agent"
        )
        if success:
            file_url = data.get("content", {}).get("html_url", "") if isinstance(data, dict) else ""
            await status_msg.edit_text(
                f"✅ *Đã push file!*\n\n"
                f"📁 *File:* `{file_path}`\n"
                f"📦 *Repo:* `{repo_path}`\n"
                f"🔗 *URL:* {file_url}\n"
                f"📊 *Size:* `{len(content)}` chars",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(
                f"❌ *Lỗi push:*\n`{error[:400]}`",
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        await status_msg.edit_text(
            f"⚠️ *Lỗi:* `{str(e)[:400]}`",
            parse_mode=ParseMode.MARKDOWN
        )

async def _git_get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ *Cú pháp:* `/git get <owner/repo> <path>`\n"
            "Ví dụ: `/git get octocat/Hello-World README.md`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    repo_path = context.args[1]
    file_path = context.args[2]

    if "/" not in repo_path:
        await update.message.reply_text("❌ *Format:* `owner/repo`", parse_mode=ParseMode.MARKDOWN)
        return

    owner, repo = repo_path.split("/", 1)

    status_msg = await update.message.reply_text(
        f"⏳ *Đang lấy file...*\n"
        f"📁 `{file_path}` from `{repo_path}`",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        success, data = await github_agent.get_file(owner, repo, file_path)
        if success:
            content_encoded = data.get("content", "") if isinstance(data, dict) else ""
            try:
                content = base64.b64decode(content_encoded.replace("\n", "")).decode('utf-8')
            except:
                content = content_encoded

            size = data.get("size", len(content)) if isinstance(data, dict) else len(content)
            sha = data.get("sha", "")[:8] if isinstance(data, dict) else ""

            header = (
                f"📄 *File Content*\n"
                f"{'━' * 20}\n"
                f"📁 *Path:* `{file_path}`\n"
                f"📦 *Repo:* `{repo_path}`\n"
                f"📊 *Size:* `{size}` bytes\n"
                f"🔑 *SHA:* `{sha}...`\n\n"
            )

            full_text = header + f"```\n{content}\n```"

            await status_msg.delete()
            await send_long_text(update, full_text, filename=file_path.replace("/", "_"))
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(
                f"❌ *Lỗi:*\n`{error[:400]}`",
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        await status_msg.edit_text(
            f"⚠️ *Lỗi:* `{str(e)[:400]}`",
            parse_mode=ParseMode.MARKDOWN
        )

async def _git_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ *Cú pháp:* `/git list <owner/repo> [path]`\n"
            "Ví dụ: `/git list octocat/Hello-World`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    repo_path = context.args[1]
    path = context.args[2] if len(context.args) > 2 else ""

    if "/" not in repo_path:
        await update.message.reply_text("❌ *Format:* `owner/repo`", parse_mode=ParseMode.MARKDOWN)
        return

    owner, repo = repo_path.split("/", 1)

    status_msg = await update.message.reply_text(
        f"⏳ *Đang liệt kê files...*",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        success, data = await github_agent.list_files(owner, repo, path)
        if success and isinstance(data, list):
            msg = f"📂 *File List — `{repo_path}`*\n{'━' * 22}\n\n"
            for item in data:
                item_type = item.get("type", "")
                name = item.get("name", "")
                size = item.get("size", 0)
                emoji = "📁" if item_type == "dir" else "📄"
                msg += f"{emoji} `{name}`"
                if item_type == "file":
                    msg += f" ({size} bytes)"
                msg += "\n"

            await status_msg.edit_text(msg, parse_mode=ParseMode.MARKDOWN)
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(
                f"❌ *Lỗi:*\n`{error[:400]}`",
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        await status_msg.edit_text(
            f"⚠️ *Lỗi:* `{str(e)[:400]}`",
            parse_mode=ParseMode.MARKDOWN
        )

async def _git_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ *Cú pháp:* `/git branch <owner/repo> <new_branch>`\n"
            "Ví dụ: `/git branch user/repo feature-x`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    repo_path = context.args[1]
    new_branch = context.args[2]

    if "/" not in repo_path:
        await update.message.reply_text("❌ *Format:* `owner/repo`", parse_mode=ParseMode.MARKDOWN)
        return

    owner, repo = repo_path.split("/", 1)

    status_msg = await update.message.reply_text(
        f"⏳ *Đang tạo branch...*\n"
        f"🌿 `{new_branch}`",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        success, data = await github_agent.create_branch(owner, repo, new_branch)
        if success:
            await status_msg.edit_text(
                f"✅ *Branch đã tạo!*\n\n"
                f"🌿 `{new_branch}`\n"
                f"📦 `{repo_path}`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(
                f"❌ *Lỗi:*\n`{error[:400]}`",
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        await status_msg.edit_text(
            f"⚠️ *Lỗi:* `{str(e)[:400]}`",
            parse_mode=ParseMode.MARKDOWN
        )

async def _git_pr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 5:
        await update.message.reply_text(
            "❌ *Cú pháp:* `/git pr <owner/repo> <title> <head> <base>`\n"
            "Ví dụ: `/git pr user/repo Fix bug feature-x main`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    repo_path = context.args[1]
    title = context.args[2]
    head = context.args[3]
    base = context.args[4]

    if "/" not in repo_path:
        await update.message.reply_text("❌ *Format:* `owner/repo`", parse_mode=ParseMode.MARKDOWN)
        return

    owner, repo = repo_path.split("/", 1)

    status_msg = await update.message.reply_text(
        f"⏳ *Đang tạo Pull Request...*",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        success, data = await github_agent.create_pr(owner, repo, title, head, base)
        if success:
            pr_url = data.get("html_url", "") if isinstance(data, dict) else ""
            pr_num = data.get("number", "") if isinstance(data, dict) else ""
            await status_msg.edit_text(
                f"✅ *Pull Request đã tạo!*\n\n"
                f"🔢 *#{pr_num}*\n"
                f"📝 *Title:* `{title}`\n"
                f"🌿 `{head}` → `{base}`\n"
                f"🔗 {pr_url}",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(
                f"❌ *Lỗi:*\n`{error[:400]}`",
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        await status_msg.edit_text(
            f"⚠️ *Lỗi:* `{str(e)[:400]}`",
            parse_mode=ParseMode.MARKDOWN
        )

async def _git_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ *Cú pháp:* `/git delete <owner/repo> <path>`\n"
            "Ví dụ: `/git delete user/repo old/file.py`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    repo_path = context.args[1]
    file_path = context.args[2]

    if "/" not in repo_path:
        await update.message.reply_text("❌ *Format:* `owner/repo`", parse_mode=ParseMode.MARKDOWN)
        return

    owner, repo = repo_path.split("/", 1)

    status_msg = await update.message.reply_text(
        f"⏳ *Đang xóa file...*\n"
        f"🗑 `{file_path}`",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        success_get, data_get = await github_agent.get_file(owner, repo, file_path)
        if not success_get:
            await status_msg.edit_text(
                f"❌ *Không tìm thấy file:* `{file_path}`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        sha = data_get.get("sha", "") if isinstance(data_get, dict) else ""

        success, data = await github_agent.delete_file(
            owner, repo, file_path,
            f"Delete {file_path} via FizzPop Agent",
            sha
        )
        if success:
            await status_msg.edit_text(
                f"✅ *Đã xóa file!*\n\n"
                f"🗑 `{file_path}`\n"
                f"📦 `{repo_path}`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(
                f"❌ *Lỗi:*\n`{error[:400]}`",
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        await status_msg.edit_text(
            f"⚠️ *Lỗi:* `{str(e)[:400]}`",
            parse_mode=ParseMode.MARKDOWN
        )

async def _git_commits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ *Cú pháp:* `/git commits <owner/repo>`\n"
            "Ví dụ: `/git commits octocat/Hello-World`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    repo_path = context.args[1]

    if "/" not in repo_path:
        await update.message.reply_text("❌ *Format:* `owner/repo`", parse_mode=ParseMode.MARKDOWN)
        return

    owner, repo = repo_path.split("/", 1)

    status_msg = await update.message.reply_text(
        f"⏳ *Đang lấy lịch sử commits...*",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        success, data = await github_agent.get_commits(owner, repo)
        if success and isinstance(data, list):
            msg = f"📝 *Commit History — `{repo_path}`*\n{'━' * 22}\n\n"
            for i, commit in enumerate(data[:10], 1):
                sha = commit.get("sha", "")[:7]
                message = commit.get("commit", {}).get("message", "")[:50]
                author = commit.get("commit", {}).get("author", {}).get("name", "Unknown")
                date = commit.get("commit", {}).get("author", {}).get("date", "")[:10]
                msg += f"{i}. `{sha}` — {message}...\n   👤 {author} 📅 {date}\n\n"

            await status_msg.edit_text(msg, parse_mode=ParseMode.MARKDOWN)
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(
                f"❌ *Lỗi:*\n`{error[:400]}`",
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        await status_msg.edit_text(
            f"⚠️ *Lỗi:* `{str(e)[:400]}`",
            parse_mode=ParseMode.MARKDOWN
        )

async def _git_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ *Cú pháp:* `/git update <owner/repo> <path>`\n"
            "Reply vào tin nhắn chứa code mới.\n"
            "Ví dụ: `/git update user/repo src/main.py` (reply code)",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    repo_path = context.args[1]
    file_path = context.args[2]

    if "/" not in repo_path:
        await update.message.reply_text("❌ *Format:* `owner/repo`", parse_mode=ParseMode.MARKDOWN)
        return

    owner, repo = repo_path.split("/", 1)

    content = ""
    if update.message.reply_to_message and update.message.reply_to_message.text:
        content = update.message.reply_to_message.text
    elif len(context.args) > 3:
        content = " ".join(context.args[3:])

    if not content:
        await update.message.reply_text(
            "❌ *Thiếu nội dung!* Reply code để update.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    status_msg = await update.message.reply_text(
        f"⏳ *Đang update file...*\n"
        f"📝 `{file_path}`",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        success_get, data_get = await github_agent.get_file(owner, repo, file_path)
        if not success_get:
            await status_msg.edit_text(
                f"❌ *File không tồn tại:* `{file_path}`\n"
                f"Dùng `/git push` để tạo mới.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        sha = data_get.get("sha", "") if isinstance(data_get, dict) else ""

        success, data = await github_agent.update_file(
            owner, repo, file_path, content,
            f"Update {file_path} via FizzPop Agent",
            sha
        )
        if success:
            await status_msg.edit_text(
                f"✅ *Đã update file!*\n\n"
                f"📝 `{file_path}`\n"
                f"📦 `{repo_path}`\n"
                f"📊 *Size:* `{len(content)}` chars",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(
                f"❌ *Lỗi:*\n`{error[:400]}`",
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        await status_msg.edit_text(
            f"⚠️ *Lỗi:* `{str(e)[:400]}`",
            parse_mode=ParseMode.MARKDOWN
        )

# ============================ AGENT COMMAND (DUAL MODE) ============================

async def agent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)

    if not context.args:
        current_deploy = state.agent_deploy_mode
        keyboard = [
            [InlineKeyboardButton("✅ Local ZIP" if current_deploy == "local" else "Local ZIP", callback_data="agentmode_local")],
            [InlineKeyboardButton("✅ GitHub" if current_deploy == "github" else "GitHub", callback_data="agentmode_github")],
        ]
        await update.message.reply_text(
            f"🤖 *Agent Mode — Tự động code & deploy*\n"
            f"{'━' * 22}\n\n"
            f"*Cách dùng:*\n"
            f"`/agent <mô tả công việc>`\n\n"
            f"*Ví dụ:*\n"
            f"• `/agent Tạo REST API FastAPI + SQLite + JWT`\n"
            f"• `/agent Viết bot Telegram đơn giản`\n"
            f"• `/agent Tạo script crawl Wikipedia`\n\n"
            f"*Deploy mode hiện tại:* `{current_deploy}`\n\n"
            f"💡 Chọn mode bên dưới hoặc dùng `/deploy <local|github>`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Detect deploy mode override
    deploy_mode = state.agent_deploy_mode
    task_description = " ".join(context.args)

    if context.args[0].lower() in ("github", "local"):
        deploy_mode = context.args[0].lower()
        task_description = " ".join(context.args[1:])

    if not task_description.strip():
        await update.message.reply_text(
            "❌ *Thiếu mô tả task!*\n"
            "Ví dụ: `/agent Tạo REST API bằng FastAPI`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    task_id = generate_task_id()
    task = AgentTask(
        task_id=task_id,
        description=task_description,
        status="running",
        deploy_mode=deploy_mode
    )
    state.agent_tasks.append(task)

    status_msg = await update.message.reply_text(
        f"🤖 *Agent Task Bắt Đầu*\n"
        f"{'━' * 22}\n\n"
        f"🆔 *Task ID:* `{task_id}`\n"
        f"📝 *Mô tả:* {task_description[:80]}...\n"
        f"📦 *Deploy:* `{deploy_mode.upper()}`\n\n"
        f"⏳ *Bước 1/5:* Phân tích yêu cầu...",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        session = context.bot_data.get('session')
        if not session:
            session = aiohttp.ClientSession()
            context.bot_data['session'] = session

        model_id = state.current_model if state.mode == "agent" else DEFAULT_AGENT_MODEL

        # Step 1: Plan
        await status_msg.edit_text(
            f"🤖 *Agent Task Đang Chạy*\n"
            f"{'━' * 22}\n\n"
            f"🆔 `{task_id}`\n"
            f"📦 Deploy: `{deploy_mode.upper()}`\n"
            f"⏳ *Bước 1/5:* Phân tích & lập kế hoạch...",
            parse_mode=ParseMode.MARKDOWN
        )

        plan_messages = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Task: {task_description}\n\n"
                f"Hãy lập kế hoạch chi tiết:\n"
                f"1. Cần những file nào?\n"
                f"2. Cấu trúc project?\n"
                f"3. Dependencies cần thiết?\n"
                f"4. Các bước implement?\n\n"
                f"Trả lời ngắn gọn, dạng bullet points."
            )}
        ]

        plan_text, plan_metrics = await call_chat_api(
            session, model_id, plan_messages, status_msg,
            system_prompt=AGENT_SYSTEM_PROMPT, max_tokens=2048
        )

        # Step 2: Generate code
        await status_msg.edit_text(
            f"🤖 *Agent Task Đang Chạy*\n"
            f"{'━' * 22}\n\n"
            f"🆔 `{task_id}`\n"
            f"📦 Deploy: `{deploy_mode.upper()}`\n"
            f"⏳ *Bước 2/5:* Viết code hoàn chỉnh...",
            parse_mode=ParseMode.MARKDOWN
        )

        code_messages = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Task: {task_description}\n\n"
                f"Kế hoạch:\n{plan_text}\n\n"
                f"VIẾT CODE HOÀN CHỈNH NGAY BÂY GIỜ. Không placeholder. Không giải thích.\n"
                f"Mỗi file phải nằm trong markers:\n"
                f"<<<FILE:filename.py>>>\n"
                f"[nội dung file đầy đủ]\n"
                f"<<<ENDFILE>>>\n\n"
                f"BẮT BUỘC có:\n"
                f"- main file (main.py hoặc index.js hoặc tương đương)\n"
                f"- requirements.txt / package.json\n"
                f"- README.md với hướng dẫn chạy\n"
                f"- .env.example nếu cần biến môi trường\n\n"
                f"Code phải chạy được ngay, có docstring, error handling, type hints."
            )}
        ]

        code_text, code_metrics = await call_chat_api(
            session, model_id, code_messages, status_msg,
            system_prompt=AGENT_SYSTEM_PROMPT, max_tokens=MAX_OUTPUT_TOKENS
        )

        # Step 3: Parse & syntax check
        await status_msg.edit_text(
            f"🤖 *Agent Task Đang Chạy*\n"
            f"{'━' * 22}\n\n"
            f"🆔 `{task_id}`\n"
            f"📦 Deploy: `{deploy_mode.upper()}`\n"
            f"⏳ *Bước 3/5:* Parse files & kiểm tra syntax...",
            parse_mode=ParseMode.MARKDOWN
        )

        files = parse_agent_files(code_text)

        if not files:
            # Retry with stronger prompt
            retry_messages = [
                {"role": "system", "content": AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Task: {task_description}\n\n"
                    f"Code trước đó không parse được. Hãy viết LẠI với format CHÍNH XÁC:\n\n"
                    f"<<<FILE:main.py>>>\n"
                    f"import os\n"
                    f"def main():\n"
                    f"    pass\n"
                    f"<<<ENDFILE>>>\n\n"
                    f"Viết TẤT CẢ các file cần thiết theo format trên."
                )}
            ]

            code_text, code_metrics = await call_chat_api(
                session, model_id, retry_messages, status_msg,
                system_prompt=AGENT_SYSTEM_PROMPT, max_tokens=MAX_OUTPUT_TOKENS
            )
            files = parse_agent_files(code_text)

        # Syntax check
        syntax_issues = []
        for fname, fcontent in files.items():
            if fname.endswith('.py'):
                try:
                    compile(fcontent, fname, 'exec')
                except SyntaxError as e:
                    syntax_issues.append(f"{fname}: Line {e.lineno}: {e.msg}")

        # Step 4: Auto-fix if needed
        if syntax_issues:
            await status_msg.edit_text(
                f"🤖 *Agent Task Đang Chạy*\n"
                f"{'━' * 22}\n\n"
                f"🆔 `{task_id}`\n"
                f"📦 Deploy: `{deploy_mode.upper()}`\n"
                f"⚠️ *Phát hiện {len(syntax_issues)} lỗi syntax*\n"
                f"⏳ *Bước 3.5/5:* Tự động sửa lỗi...",
                parse_mode=ParseMode.MARKDOWN
            )

            fix_messages = [
                {"role": "system", "content": AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Code có lỗi syntax:\n\n"
                    f"{'\n'.join(syntax_issues)}\n\n"
                    f"Hãy sửa lại TẤT CẢ file. Giữ nguyên format <<<FILE:>>> <<<ENDFILE>>>.\n"
                    f"Chỉ trả về code đã sửa, không giải thích."
                )}
            ]

            fixed_code, _ = await call_chat_api(
                session, model_id, fix_messages, status_msg,
                system_prompt=AGENT_SYSTEM_PROMPT, max_tokens=MAX_OUTPUT_TOKENS
            )

            files = parse_agent_files(fixed_code)

            # Re-check
            syntax_issues = []
            for fname, fcontent in files.items():
                if fname.endswith('.py'):
                    try:
                        compile(fcontent, fname, 'exec')
                    except SyntaxError as e:
                        syntax_issues.append(f"{fname}: Line {e.lineno}: {e.msg}")

        # Step 5: Deploy
        await status_msg.edit_text(
            f"🤖 *Agent Task Đang Chạy*\n"
            f"{'━' * 22}\n\n"
            f"🆔 `{task_id}`\n"
            f"📦 Deploy: `{deploy_mode.upper()}`\n"
            f"⏳ *Bước 4/5:* Đang deploy...",
            parse_mode=ParseMode.MARKDOWN
        )

        if deploy_mode == "github":
            await _deploy_github(update, context, state, task, files, status_msg, plan_text, code_metrics, syntax_issues)
        else:
            await _deploy_local(update, context, state, task, files, status_msg, plan_text, code_metrics, syntax_issues)

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state.stats.tasks_failed += 1

        error_trace = traceback.format_exc()
        logger.error(f"Agent task failed: {e}\n{error_trace}")

        await status_msg.edit_text(
            f"❌ *Agent Task Thất Bại*\n"
            f"{'━' * 22}\n\n"
            f"🆔 `{task_id}`\n"
            f"⚠️ *Lỗi:* `{str(e)[:300]}`\n\n"
            f"💡 *Thử:*\n"
            f"• Đơn giản hóa yêu cầu\n"
            f"• Thử lại với `/agent local <task>`\n"
            f"• Kiểm tra GitHub token nếu dùng github mode\n\n"
            f"🧠 AI đã ghi nhận lỗi này.",
            parse_mode=ParseMode.MARKDOWN
        )

        await agent_self_reflect(task, state)

async def _deploy_local(update, context, state, task, files, status_msg, plan_text, code_metrics, syntax_issues):
    """Deploy agent task as local ZIP file."""
    try:
        zip_path = await save_agent_local(task.task_id, files)
        task.local_path = str(zip_path)
        task.status = "completed"
        task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task.files_created = list(files.keys())
        state.stats.tasks_completed += 1

        # Build success message
        file_list = "\n".join([f"• `{f}` ({len(c)} chars)" for f, c in files.items()])
        syntax_status = "✅ Tất cả file Python hợp lệ" if not syntax_issues else "\n".join([f"⚠️ {i}" for i in syntax_issues[:3]])

        result_msg = (
            f"✅ *Agent Task Hoàn Thành!*\n"
            f"{'━' * 22}\n\n"
            f"🆔 *Task ID:* `{task.task_id}`\n"
            f"📝 *Mô tả:* {task.description[:80]}...\n"
            f"📦 *Deploy:* LOCAL ZIP\n\n"
            f"📁 *Files ({len(files)}):*\n"
            f"{file_list}\n\n"
            f"🔍 *Syntax Check:*\n"
            f"{syntax_status}\n\n"
            f"📊 *AI Metrics:*\n"
            f"• ⏱ Latency: `{code_metrics.get('latency', 0):.2f}s`\n"
            f"• 📝 Output: `{code_metrics.get('output_tokens', 0)}` tokens\n\n"
            f"📎 File ZIP đính kèm bên dưới 👇"
        )

        await status_msg.edit_text(result_msg, parse_mode=ParseMode.MARKDOWN)

        # Send ZIP file
        with open(zip_path, 'rb') as f:
            zip_bio = io.BytesIO(f.read())
        zip_bio.name = f"{task.task_id}.zip"

        await update.message.reply_document(
            document=zip_bio,
            caption=f"📦 Agent Output — {len(files)} files"
        )

        # Also send code preview as text file
        preview_text = f"# {task.description}\n# Task ID: {task.task_id}\n# Deploy: LOCAL\n\n"
        preview_text += f"## Plan\n{plan_text}\n\n"
        preview_text += f"## Files\n\n"
        for fname, fcontent in files.items():
            preview_text += f"\n{'='*60}\n# FILE: {fname}\n{'='*60}\n\n{fcontent}\n"

        preview_bio = io.BytesIO(preview_text.encode('utf-8'))
        preview_bio.name = f"{task.task_id}_preview.txt"
        await update.message.reply_document(
            document=preview_bio,
            caption=f"📄 Full code preview"
        )

        # Self-reflection
        reflection = await agent_self_reflect(task, state)
        await update.message.reply_text(reflection, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        raise e

async def _deploy_github(update, context, state, task, files, status_msg, plan_text, code_metrics, syntax_issues):
    """Deploy agent task to GitHub repository."""
    try:
        # Get GitHub user
        success_user, user_data = await github_agent.get_user()
        if not success_user:
            raise Exception("GitHub token không hợp lệ (Bad credentials). Hãy dùng `/deploy local` hoặc cập nhật token.")

        github_username = user_data.get("login", "")
        state.github_username = github_username

        # Smart repo name
        repo_name = smart_repo_name(task.description)

        # Create repo
        success_repo, repo_data = await github_agent.create_repo(
            repo_name,
            f"Auto-generated by FizzPop Agent: {task.description[:100]}",
            private=False
        )

        if not success_repo:
            error_msg = repo_data.get("message", str(repo_data)) if isinstance(repo_data, dict) else str(repo_data)
            if "already exists" in error_msg.lower():
                # Use existing repo
                pass
            else:
                raise Exception(f"Lỗi tạo repo: {error_msg}")

        repo_full = f"{github_username}/{repo_name}"
        task.repo_url = f"https://github.com/{repo_full}"

        # Push all files
        pushed_files = []
        for fname, fcontent in files.items():
            success_push, _ = await github_agent.create_file(
                github_username, repo_name, fname, fcontent,
                f"Add {fname} via FizzPop Agent"
            )
            if success_push:
                pushed_files.append(fname)
            await asyncio.sleep(0.5)

        task.status = "completed"
        task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task.files_created = pushed_files
        state.stats.tasks_completed += 1

        file_list = "\n".join([f"• `{f}`" for f in pushed_files])
        syntax_status = "✅ Tất cả file Python hợp lệ" if not syntax_issues else "\n".join([f"⚠️ {i}" for i in syntax_issues[:3]])

        result_msg = (
            f"✅ *Agent Task Hoàn Thành!*\n"
            f"{'━' * 22}\n\n"
            f"🆔 *Task ID:* `{task.task_id}`\n"
            f"📝 *Mô tả:* {task.description[:80]}...\n"
            f"🔗 *Deploy:* GITHUB\n\n"
            f"📦 *Repository:*\n"
            f"[{repo_full}](https://github.com/{repo_full})\n\n"
            f"📁 *Files đã push ({len(pushed_files)}):*\n"
            f"{file_list}\n\n"
            f"🔍 *Syntax Check:*\n"
            f"{syntax_status}\n\n"
            f"📊 *AI Metrics:*\n"
            f"• ⏱ Latency: `{code_metrics.get('latency', 0):.2f}s`\n"
            f"• 📝 Output: `{code_metrics.get('output_tokens', 0)}` tokens"
        )

        await status_msg.edit_text(result_msg, parse_mode=ParseMode.MARKDOWN)

        # Send code preview as file too
        preview_text = f"# {task.description}\n# Repo: https://github.com/{repo_full}\n# Task ID: {task.task_id}\n\n"
        preview_text += f"## Plan\n{plan_text}\n\n"
        preview_text += f"## Files\n\n"
        for fname, fcontent in files.items():
            preview_text += f"\n{'='*60}\n# FILE: {fname}\n{'='*60}\n\n{fcontent}\n"

        preview_bio = io.BytesIO(preview_text.encode('utf-8'))
        preview_bio.name = f"{task.task_id}_preview.txt"
        await update.message.reply_document(
            document=preview_bio,
            caption=f"📄 Full code preview"
        )

        # Self-reflection
        reflection = await agent_self_reflect(task, state)
        await update.message.reply_text(reflection, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        raise e

async def agent_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    state = get_user_state(user_id)
    data = query.data

    if data == "agentmode_local":
        state.agent_deploy_mode = "local"
        await query.edit_message_text(
            "✅ *Agent deploy mode: LOCAL ZIP*\n\n"
            "📦 Agent sẽ lưu code thành file .zip\n"
            "💡 Dùng `/agent <mô tả>` để chạy.",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "agentmode_github":
        state.agent_deploy_mode = "github"
        await query.edit_message_text(
            "✅ *Agent deploy mode: GITHUB*\n\n"
            "🔗 Agent sẽ push code lên GitHub\n"
            "💡 Dùng `/agent <mô tả>` để chạy.",
            parse_mode=ParseMode.MARKDOWN
        )

# ============================ MAIN MESSAGE HANDLER ============================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    user_input = update.message.text.strip()
    state = get_user_state(user_id)

    if not user_input:
        return

    mode = state.mode
    model_id = state.current_model
    mode_name = MODE_CONFIG[mode]["name"]

    # Validate model exists in current mode
    valid_models = [m[1] for m in MODE_CONFIG[mode]["models"]]
    if model_id not in valid_models:
        model_id = MODE_CONFIG[mode]["default"]
        state.current_model = model_id

    status_msg = await update.message.reply_text(
        f"⏳ *Đang khởi tạo...*\n"
        f"🔄 Mode: {mode_name}\n"
        f"🤖 Model: `{model_id}`",
        parse_mode=ParseMode.MARKDOWN
    )

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    session = context.bot_data.get('session')
    if not session:
        session = aiohttp.ClientSession()
        context.bot_data['session'] = session

    try:
        if mode == "chat":
            await _handle_chat(update, context, state, model_id, user_input, status_msg, session)
        elif mode == "agent":
            await _handle_agent_chat(update, context, state, model_id, user_input, status_msg, session)
        elif mode == "embed":
            await _handle_embed(update, context, state, model_id, user_input, status_msg, session)
        elif mode == "tts":
            await _handle_tts(update, context, state, model_id, user_input, status_msg, session)

    except Exception as e:
        logger.error(f"Error: {e}")
        error_msg = (
            f"⚠️ *Lỗi xử lý*\n"
            f"{'━' * 15}\n"
            f"`{str(e)[:400]}`\n\n"
            f"💡 *Thử:* `/reset` hoặc đổi model/mode"
        )
        try:
            await status_msg.edit_text(error_msg, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN)

        state.last_error = str(e)
        state.self_notes.append(f"Error in {mode} mode: {str(e)[:200]}")

async def _handle_chat(update, context, state, model_id, user_input, status_msg, session):
    state.history.append({"role": "user", "content": user_input})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state.history

    ai_response, metrics = await call_chat_api(session, model_id, messages, status_msg)

    state.history.append({"role": "assistant", "content": ai_response})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]

    model_disp = get_model_display("chat", model_id)
    header = f"🤖 *{model_disp}*\n{'━' * 20}\n\n"
    footer = build_metrics_footer(metrics, state)
    full_text = header + ai_response + footer

    try:
        await status_msg.delete()
    except Exception:
        pass

    await send_long_text(update, full_text, filename="ai_response.txt")

async def _handle_agent_chat(update, context, state, model_id, user_input, status_msg, session):
    """Agent mode: AI acts as coding assistant with GitHub context."""
    state.history.append({"role": "user", "content": user_input})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]

    agent_context = AGENT_SYSTEM_PROMPT
    if state.github_username:
        agent_context += f"\n\nGitHub user: {state.github_username}"
    if state.self_notes:
        agent_context += "\n\nLessons learned:\n" + "\n".join(state.self_notes[-5:])

    messages = [{"role": "system", "content": agent_context}] + state.history

    ai_response, metrics = await call_chat_api(
        session, model_id, messages, status_msg,
        system_prompt=agent_context, max_tokens=MAX_OUTPUT_TOKENS
    )

    state.history.append({"role": "assistant", "content": ai_response})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]

    model_disp = get_model_display("agent", model_id)
    header = f"🤖 *{model_disp}* [AGENT MODE]\n{'━' * 20}\n\n"
    footer = build_metrics_footer(metrics, state)
    full_text = header + ai_response + footer

    try:
        await status_msg.delete()
    except Exception:
        pass

    await send_long_text(update, full_text, filename="agent_response.txt")

async def _handle_embed(update, context, state, model_id, user_input, status_msg, session):
    content, metrics, full_vector = await call_embed_api(session, model_id, user_input, status_msg)

    footer = build_metrics_footer(metrics, state)
    full_text = content + footer

    try:
        await status_msg.delete()
    except Exception:
        pass

    try:
        await update.message.reply_text(full_text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(full_text)

    vector_bio = io.BytesIO(full_vector.encode('utf-8'))
    vector_bio.name = f"embedding_{model_id.replace('/', '_')}.json"
    await update.message.reply_document(
        document=vector_bio,
        caption=f"📄 Full embedding vector"
    )

async def _handle_tts(update, context, state, model_id, user_input, status_msg, session):
    audio_bytes, metrics = await call_tts_api(session, model_id, user_input, status_msg)

    footer_metrics = build_metrics_footer(metrics, state)

    try:
        await status_msg.delete()
    except Exception:
        pass

    audio_bio = io.BytesIO(audio_bytes)
    audio_bio.name = f"tts_{model_id.replace('/', '_')}.mp3"

    model_disp = get_model_display("tts", model_id)
    caption = (
        f"🔊 *Text-to-Speech*\n"
        f"🤖 Model: {model_disp}\n"
        f"📝 Length: `{len(user_input)}` chars\n"
        f"📦 Size: `{len(audio_bytes)}` bytes"
    ) + footer_metrics

    await update.message.reply_voice(
        voice=audio_bio,
        caption=caption,
        parse_mode=ParseMode.MARKDOWN
    )

# ============================ ERROR HANDLER ============================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

    if update and update.effective_user:
        state = get_user_state(update.effective_user.id)
        error_str = str(context.error)[:300]
        state.last_error = error_str
        state.self_notes.append(f"System error: {error_str}")

    if update and update.effective_message:
        await update.effective_message.reply_text(
            "😵 *Đã xảy ra lỗi không mong muốn!*\n"
            "Vui lòng thử lại sau.\n\n"
            "💡 *Thử:* `/reset` hoặc `/help`",
            parse_mode=ParseMode.MARKDOWN
        )

# ============================ MAIN ============================

async def post_init(application: Application):
    application.bot_data['session'] = aiohttp.ClientSession()
    await github_agent.init_session()
    logger.info("Bot initialized. Sessions created.")

async def post_shutdown(application: Application):
    session = application.bot_data.get('session')
    if session:
        await session.close()
    await github_agent.close()
    logger.info("All sessions closed.")

def main():
    logger.info("Starting FizzPop AI Agent Bot v5.0...")

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .concurrent_updates(True)
        .build()
    )

    # Core commands
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('models', show_models))
    application.add_handler(CommandHandler('switch', switch_model_command))
    application.add_handler(CommandHandler('mode', mode_command))
    application.add_handler(CommandHandler('reset', reset_chat))
    application.add_handler(CommandHandler('status', status_command))
    application.add_handler(CommandHandler('stats', stats_command))

    # Agent commands
    application.add_handler(CommandHandler('agent', agent_command))
    application.add_handler(CommandHandler('git', git_command))
    application.add_handler(CommandHandler('analyze', analyze_command))
    application.add_handler(CommandHandler('tasks', tasks_command))
    application.add_handler(CommandHandler('learn', learn_command))
    application.add_handler(CommandHandler('deploy', deploy_mode_command))

    # Callbacks
    application.add_handler(CallbackQueryHandler(model_callback, pattern="^model_"))
    application.add_handler(CallbackQueryHandler(model_callback, pattern="^refresh_models$"))
    application.add_handler(CallbackQueryHandler(mode_callback, pattern="^setmode_"))
    application.add_handler(CallbackQueryHandler(deploy_mode_callback, pattern="^deploymode_"))
    application.add_handler(CallbackQueryHandler(agent_mode_callback, pattern="^agentmode_"))

    # Messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Errors
    application.add_error_handler(error_handler)

    # Run
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
