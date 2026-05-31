#!/usr/bin/env python3
"""
🚀 ULTIMATE TELEGRAM AI AGENT BOT v3.2
Fixed: escape_markdown from telegram.helpers, no SyntaxWarning, no BadRequest.
"""

import os
import re
import io
import base64
import json
import logging
import tempfile
import time
from typing import Optional, List, Dict, Any, Tuple

import httpx
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

# ═══════════════════════════════════════════════
# HARDCODED CONFIG
# ═══════════════════════════════════════════════

TELEGRAM_BOT_TOKEN = "8909561772:AAGQgxrbvXbi-RACF4_Z7iiS4R7NA6Za6wU"
GITHUB_TOKEN       = "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"
TTS_API_URL        = "https://ckey.vn/v1/audio/speech"
DEFAULT_MODEL      = "🚀 GLM4.7"
SYSTEM_PROMPT      = "You are a helpful, intelligent AI assistant. Respond concisely but accurately."

AI_ENDPOINTS = [
    {
        "name": "Ckey",
        "base": "https://ckey.vn/v1/chat/completions",
        "key":  "sk-e317a237354192e26f99951f06e4882779e8a0e08e86d2f71242e8ff770bdf24"
    }
]

AVAILABLE_MODELS = {
    "🚀 GLM4.7": "glm4.7",
    "👨‍💻 Qwen3 Coder 480B": "qwen3-coder-480b-a35b-instruct",
    "⚡ Mistral Medium 3.5": "mistral-medium-3.5-128b",
    "🧠 Mistral Small 4": "mistral-small-4-119b-2603",
    "🔥 DeepSeek V3": "deepseek-3.2",
    "🐬 DeepSeek R1 Distill Qwen": "deepseek-r1-distill-qwen-32b",
    "🏆 Mistral Large 3": "mistral-large-3-675b-instruct-2512",
    "🤖 DeepSeek R1": "chieustudio/deepseek-r1",
    "🤖 Kimi K2.6": "kimi-k2.6",
    "🐉 GLM-5": "glm-5",
    "🤔 Grok 4.20 Thinking": "grok-4.20-thinking",
    "🤖 Grok 4.3": "grok-4.3",
    "⚡ Grok 4.20 Fast": "grok-4.20-fast",
    "🤖 GPT-5.4 Mini": "gpt-5.4-mini",
    "🐉 GLM-5.1": "glm-5.1",
    "🤖 Claude Haiku 4.5": "claude-haiku-4.5",
    "🤖 GPT-5.2": "gpt-5.2",
    "🤖 GPT-5.3 Codex": "gpt-5.3-codex",
    "🤖 GPT-5.4": "gpt-5.4",
    "🤖 Claude Sonnet 4.6": "claude-sonnet-4.6",
    "🤖 Claude Sonnet 4.5": "claude-sonnet-4.5",
}

# ═══════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-12s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════

def md(text: str) -> str:
    """Safe MarkdownV2 escape using telegram's official helper."""
    return escape_markdown(text, version=2)


def truncate_history(history: List[Dict[str, str]], max_chars: int = 8000) -> List[Dict[str, str]]:
    """Trim oldest messages while keeping total characters under limit."""
    total = sum(len(m.get("content", "")) for m in history)
    while total > max_chars and len(history) > 1:
        removed = history.pop(0)
        total -= len(removed.get("content", ""))
    return history


def extract_code_blocks(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract first code block and optional filename from AI response."""
    fname_match = re.search(r'FILENAME[:\s]+(\S+\.[a-zA-Z0-9]+)', text, re.IGNORECASE)
    filename = fname_match.group(1) if fname_match else None
    blocks = re.findall(r'```(?:[\w+]+)?\n(.*?)```', text, re.DOTALL)
    if blocks:
        return filename, blocks[0].strip()
    return filename, None


# ═══════════════════════════════════════════════
# ASYNC AI CLIENT
# ═══════════════════════════════════════════════

class AIClient:
    def __init__(self, endpoints: List[Dict[str, str]]):
        self.endpoints = endpoints
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(180.0, connect=10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10)
        )

    async def chat(self, model_id: str, messages: List[Dict[str, str]],
                   max_tokens: int = 2048, temperature: float = 0.7) -> str:
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        last_err: Optional[Exception] = None
        for ep in self.endpoints:
            try:
                headers = {
                    "Authorization": f"Bearer {ep['key']}",
                    "Content-Type": "application/json"
                }
                resp = await self._client.post(ep["base"], headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                if "choices" in data and data["choices"]:
                    content = data["choices"][0].get("message", {}).get("content", "").strip()
                    if content:
                        logger.info(f"AI success via {ep['name']}")
                        return content
            except Exception as e:
                logger.warning(f"AI endpoint {ep['name']} failed: {e}")
                last_err = e
                continue
        raise Exception(f"All AI endpoints failed. Last error: {last_err}")

    async def tts(self, text: str, voice: str = "NamMinh") -> bytes:
        headers = {
            "Authorization": f"Bearer {self.endpoints[0]['key']}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "vi-VN-NamMinhNeural",
            "input": text,
            "voice": voice
        }
        resp = await self._client.post(TTS_API_URL, headers=headers, json=payload, timeout=60.0)
        resp.raise_for_status()
        return resp.content

    async def close(self):
        await self._client.aclose()


# ═══════════════════════════════════════════════
# ASYNC GITHUB CLIENT
# ═══════════════════════════════════════════════

class GitHubClient:
    def __init__(self, token: str, owner: Optional[str] = None,
                 repo: Optional[str] = None, branch: str = "main"):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self._client = httpx.AsyncClient(headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }, timeout=httpx.Timeout(30.0, connect=10.0))

    def _base(self) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.repo}"

    async def create_repo(self, name: str, private: bool = False) -> Tuple[bool, str]:
        url = "https://api.github.com/user/repos"
        payload = {"name": name, "private": private, "auto_init": True}
        resp = await self._client.post(url, json=payload)
        if resp.status_code == 201:
            data = resp.json()
            self.owner = data["owner"]["login"]
            self.repo = name
            return True, f"Created repo {name} (owner: {self.owner})"
        return False, f"GitHub error {resp.status_code}: {resp.text}"

    async def push(self, path: str, content: str, msg: str = "Auto-commit by Telegram Bot") -> Tuple[bool, str]:
        url = f"{self._base()}/contents/{path}"
        sha = await self._get_sha(path)
        payload = {
            "message": msg,
            "content": base64.b64encode(content.encode("utf-8")).decode(),
            "branch": self.branch
        }
        if sha:
            payload["sha"] = sha
        resp = await self._client.put(url, json=payload)
        if resp.status_code in (200, 201):
            return True, resp.json()["content"]["html_url"]
        return False, f"GitHub error {resp.status_code}: {resp.text}"

    async def get(self, path: str) -> Tuple[bool, str]:
        url = f"{self._base()}/contents/{path}?ref={self.branch}"
        resp = await self._client.get(url)
        if resp.status_code == 200:
            return True, base64.b64decode(resp.json()["content"]).decode("utf-8")
        return False, f"GitHub error {resp.status_code}: {resp.text}"

    async def list_files(self, path: str = "") -> Tuple[bool, Any]:
        url = f"{self._base()}/contents/{path}?ref={self.branch}"
        resp = await self._client.get(url)
        if resp.status_code == 200:
            return True, [f["name"] for f in resp.json()]
        return False, f"GitHub error {resp.status_code}: {resp.text}"

    async def delete(self, path: str, msg: str = "Deleted by Telegram Bot") -> Tuple[bool, str]:
        url = f"{self._base()}/contents/{path}"
        sha = await self._get_sha(path)
        if not sha:
            return False, "File does not exist"
        payload = {"message": msg, "sha": sha, "branch": self.branch}
        resp = await self._client.delete(url, json=payload)
        return (True, "Deleted successfully") if resp.status_code == 200 else (False, f"GitHub error {resp.status_code}: {resp.text}")

    async def _get_sha(self, path: str) -> Optional[str]:
        url = f"{self._base()}/contents/{path}?ref={self.branch}"
        resp = await self._client.get(url)
        return resp.json().get("sha") if resp.status_code == 200 else None

    async def close(self):
        await self._client.aclose()


# ═══════════════════════════════════════════════
# CONVERSATION MANAGER
# ═══════════════════════════════════════════════

class ConversationManager:
    def __init__(self):
        self._states: Dict[int, Dict[str, Any]] = {}

    def get(self, user_id: int) -> Dict[str, Any]:
        if user_id not in self._states:
            self._states[user_id] = {
                "history": [],
                "model": DEFAULT_MODEL,
                "gh_owner": None,
                "gh_repo": None,
                "last_message": None
            }
        return self._states[user_id]

    def reset(self, user_id: int) -> None:
        self.get(user_id)["history"] = []

    def add_message(self, user_id: int, role: str, content: str) -> None:
        state = self.get(user_id)
        state["history"].append({"role": role, "content": content})
        state["history"] = truncate_history(state["history"], max_chars=8000)

    def set_model(self, user_id: int, model: str) -> None:
        self.get(user_id)["model"] = model

    def get_model_id(self, user_id: int) -> str:
        state = self.get(user_id)
        return AVAILABLE_MODELS.get(state["model"], AVAILABLE_MODELS[DEFAULT_MODEL])

    def set_github(self, user_id: int, owner: str, repo: str) -> None:
        state = self.get(user_id)
        state["gh_owner"] = owner
        state["gh_repo"] = repo


conv = ConversationManager()

# ═══════════════════════════════════════════════
# UI HELPERS
# ═══════════════════════════════════════════════

async def send_long_message(update: Update, text: str, header: str = "") -> None:
    """Send as text if short; otherwise send as .txt file."""
    full = header + text
    if len(full) <= 4000:
        await update.message.reply_text(full, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(text)
            path = f.name
        await update.message.reply_document(
            document=open(path, 'rb'),
            filename="response.txt",
            caption="📄 Response was too long. Sent as file.",
            parse_mode=None
        )
        os.unlink(path)


# ═══════════════════════════════════════════════
# INLINE KEYBOARD (Models Pagination)
# ═══════════════════════════════════════════════

async def _render_models_page(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              page: int, edit: bool = False) -> None:
    user_id = update.effective_user.id
    state = conv.get(user_id)
    keys = list(AVAILABLE_MODELS.keys())
    per_page = 8
    total_pages = max(1, (len(keys) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    page_keys = keys[start_idx:start_idx + per_page]

    text = f"📂 *Model List* — Page {page}/{total_pages}\n━━━━━━━━━━━━━━━\n"
    buttons: List[List[InlineKeyboardButton]] = []
    row: List[InlineKeyboardButton] = []

    for i, k in enumerate(page_keys, start=start_idx + 1):
        marker = "✅" if k == state['model'] else "⚪"
        text += f"{marker} *{i}\.* `{md(k)}`\n"
        cb = f"switch:{start_idx + i - 1}"
        label = f"{i}. {k[:18]}"
        row.append(InlineKeyboardButton(label, callback_data=cb))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    nav: List[InlineKeyboardButton] = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"page:{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("Next ▶", callback_data=f"page:{page+1}"))
    if nav:
        buttons.append(nav)

    markup = InlineKeyboardMarkup(buttons)
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=markup)


# ═══════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    state = conv.get(user_id)
    model = md(state['model'])
    text = (
        f"🤖 *Ultimate AI Agent Bot v3\.2*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎯 Current model: `{model}`\n\n"
        f"📂 /models — Browse models\n"
        f"🔄 /switch — Quick switch\n"
        f"🗑 /reset — Clear history\n"
        f"🔊 /tts — Text to speech\n"
        f"🐙 /git — GitHub integration\n"
        f"❓ /help — Full help\n\n"
        f"💬 *Send any message to chat!*"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"🛠 *Bot Commands*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"*/start* — Start bot & show status\n"
        f"*/models* — Interactive model picker\n"
        f"*/switch* <number> — Switch by number\n"
        f"*/reset* — Clear conversation history\n"
        f"*/tts* <text> — Convert text to speech\n"
        f"*/git help* — GitHub commands\n\n"
        f"💡 *Features:*\n"
        f"• Auto\-fallback across AI endpoints\n"
        f"• Smart history trimming\n"
        f"• Long replies auto\-sent as \.txt files\n"
        f"• MarkdownV2 safe formatting\n"
        f"• GitHub auto\-code generation & push"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)


async def models_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    page = int(context.args[0]) if context.args else 1
    await _render_models_page(update, context, page, edit=False)


async def models_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    if data.startswith("page:"):
        page = int(data.split(":")[1])
        await _render_models_page(update, context, page, edit=True)
    elif data.startswith("switch:"):
        idx = int(data.split(":")[1])
        keys = list(AVAILABLE_MODELS.keys())
        if 0 <= idx < len(keys):
            conv.set_model(user_id, keys[idx])
            await query.edit_message_text(
                f"✅ Model switched to: `{md(keys[idx])}`\n\n"
                f"Use /models to browse more or send a message to chat.",
                parse_mode=ParseMode.MARKDOWN_V2
            )


async def switch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: `/switch <number>`\nUse /models to see numbers.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    try:
        idx = int(context.args[0]) - 1
        keys = list(AVAILABLE_MODELS.keys())
        if 0 <= idx < len(keys):
            conv.set_model(update.effective_user.id, keys[idx])
            await update.message.reply_text(
                f"✅ Selected: `{md(keys[idx])}`",
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            await update.message.reply_text(
                f"❌ Choose a number between 1 and {len(keys)}",
                parse_mode=ParseMode.MARKDOWN_V2
            )
    except ValueError:
        await update.message.reply_text("❌ Invalid number.", parse_mode=ParseMode.MARKDOWN_V2)


async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conv.reset(update.effective_user.id)
    await update.message.reply_text("🗑 Conversation history cleared.", parse_mode=ParseMode.MARKDOWN_V2)


async def tts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = ' '.join(context.args) if context.args else conv.get(user_id).get('last_message')
    if not text:
        await update.message.reply_text(
            "❌ Provide text: `/tts hello world` or chat first.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    await context.bot.send_chat_action(update.effective_chat.id, "record_voice")
    ai_client: AIClient = context.bot_data["ai_client"]
    try:
        audio_bytes = await ai_client.tts(text)
        audio = io.BytesIO(audio_bytes)
        audio.name = "speech.mp3"
        await update.message.reply_voice(InputFile(audio))
    except Exception as e:
        logger.exception("TTS failed")
        await update.message.reply_text(f"❌ TTS Error: `{md(str(e))}`", parse_mode=ParseMode.MARKDOWN_V2)


async def git_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or context.args[0].lower() == 'help':
        text = (
            f"🐙 *GitHub Integration*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"*/git config* <owner> <repo> — Set repo\n"
            f"*/git create* <name> — Create new repo\n"
            f"*/git push* <path> <content> — Push file\n"
            f"*/git list* — List files\n"
            f"*/git get* <path> — View file\n"
            f"*/git delete* <path> — Delete file\n"
            f"*/git auto* <request> — AI generates & pushes code\n\n"
            f"💡 *Tip:* In `/git auto`, the AI will try to suggest a filename\."
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
        return

    user_id = update.effective_user.id
    state = conv.get(user_id)
    action = context.args[0].lower()

    gh = GitHubClient(GITHUB_TOKEN, state.get('gh_owner'), state.get('gh_repo'))

    if action == 'config':
        if len(context.args) >= 3:
            conv.set_github(user_id, context.args[1], context.args[2])
            await update.message.reply_text(
                f"✅ GitHub configured: `{md(state['gh_owner'])}/{md(state['gh_repo'])}`",
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            await update.message.reply_text("❌ Usage: `/git config <owner> <repo>`", parse_mode=ParseMode.MARKDOWN_V2)

    elif action == 'create':
        if len(context.args) >= 2:
            ok, msg = await gh.create_repo(context.args[1])
            if ok:
                conv.set_github(user_id, gh.owner, gh.repo)
            await update.message.reply_text(
                f"{'✅' if ok else '❌'} {md(msg)}",
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            await update.message.reply_text("❌ Usage: `/git create <name>`", parse_mode=ParseMode.MARKDOWN_V2)

    elif action == 'list':
        if not state.get('gh_owner') or not state.get('gh_repo'):
            await update.message.reply_text("❌ Configure GitHub first: `/git config <owner> <repo>`", parse_mode=ParseMode.MARKDOWN_V2)
            return
        ok, files = await gh.list_files()
        if ok:
            text = "📁 *Files:*\n" + "\n".join(f"• `{md(f)}`" for f in files) if files else "📁 *Empty repository*"
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text(f"❌ {md(str(files))}", parse_mode=ParseMode.MARKDOWN_V2)

    elif action == 'get':
        if len(context.args) >= 2:
            if not state.get('gh_owner') or not state.get('gh_repo'):
                await update.message.reply_text("❌ Configure GitHub first.", parse_mode=ParseMode.MARKDOWN_V2)
                return
            ok, content = await gh.get(context.args[1])
            if ok:
                header = f"📄 *{md(context.args[1])}*\n```text\n"
                footer = "\n```"
                safe = md(content)
                if len(header + safe + footer) > 4000:
                    await send_long_message(update, content, header=f"📄 *{md(context.args[1])}*\n\n")
                else:
                    await update.message.reply_text(header + safe + footer, parse_mode=ParseMode.MARKDOWN_V2)
            else:
                await update.message.reply_text(f"❌ {md(str(content))}", parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text("❌ Usage: `/git get <path>`", parse_mode=ParseMode.MARKDOWN_V2)

    elif action == 'delete':
        if len(context.args) >= 2:
            if not state.get('gh_owner') or not state.get('gh_repo'):
                await update.message.reply_text("❌ Configure GitHub first.", parse_mode=ParseMode.MARKDOWN_V2)
                return
            ok, msg = await gh.delete(context.args[1])
            await update.message.reply_text(f"{'✅' if ok else '❌'} {md(msg)}", parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text("❌ Usage: `/git delete <path>`", parse_mode=ParseMode.MARKDOWN_V2)

    elif action == 'push':
        if len(context.args) >= 3:
            if not state.get('gh_owner') or not state.get('gh_repo'):
                await update.message.reply_text("❌ Configure GitHub first.", parse_mode=ParseMode.MARKDOWN_V2)
                return
            path = context.args[1]
            content = ' '.join(context.args[2:])
            ok, msg = await gh.push(path, content)
            if ok:
                await update.message.reply_text(
                    f"✅ Pushed `{md(path)}`: [Link]({msg})",
                    parse_mode=ParseMode.MARKDOWN_V2,
                    disable_web_page_preview=True
                )
            else:
                await update.message.reply_text(f"❌ {md(msg)}", parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text("❌ Usage: `/git push <path> <content>`", parse_mode=ParseMode.MARKDOWN_V2)

    elif action == 'auto':
        if not state.get('gh_owner') or not state.get('gh_repo'):
            await update.message.reply_text("❌ Configure GitHub first.", parse_mode=ParseMode.MARKDOWN_V2)
            return
        task = ' '.join(context.args[1:])
        if not task:
            await update.message.reply_text("❌ Usage: `/git auto <request>`", parse_mode=ParseMode.MARKDOWN_V2)
            return
        await context.bot.send_chat_action(update.effective_chat.id, "typing")
        ai_client: AIClient = context.bot_data["ai_client"]
        try:
            msgs = [
                {
                    "role": "system",
                    "content": (
                        "You are a senior developer. Generate clean, working code based on the user's request. "
                        "Wrap code in ```language ... ``` blocks. "
                        "Suggest a filename on the first line as: FILENAME: example.py"
                    )
                },
                {"role": "user", "content": task}
            ]
            model_id = conv.get_model_id(user_id)
            ai_resp = await ai_client.chat(model_id, msgs, max_tokens=2048)

            filename, code = extract_code_blocks(ai_resp)
            if code:
                path = filename or f"auto_{int(time.time())}.py"
                ok, msg = await gh.push(path, code, f"Auto-generated: {task[:60]}")
                if ok:
                    await update.message.reply_text(
                        f"✅ Auto\-pushed `{md(path)}`: [Link]({msg})",
                        parse_mode=ParseMode.MARKDOWN_V2,
                        disable_web_page_preview=True
                    )
                else:
                    await update.message.reply_text(f"❌ Push failed: {md(msg)}", parse_mode=ParseMode.MARKDOWN_V2)
            else:
                preview = md(ai_resp[:600])
                await update.message.reply_text(
                    f"❌ AI did not return a code block\. Preview:\n\n{preview}",
                    parse_mode=ParseMode.MARKDOWN_V2
                )
        except Exception as e:
            logger.exception("Git auto failed")
            await update.message.reply_text(f"❌ Error: `{md(str(e))}`", parse_mode=ParseMode.MARKDOWN_V2)

    else:
        await update.message.reply_text("❓ Unknown command. Try `/git help`", parse_mode=ParseMode.MARKDOWN_V2)


# ═══════════════════════════════════════════════
# MESSAGE HANDLER
# ═══════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    text = update.message.text
    conv.add_message(user_id, "user", text)
    conv.get(user_id)["last_message"] = text

    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    ai_client: AIClient = context.bot_data["ai_client"]
    model_id = conv.get_model_id(user_id)

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conv.get(user_id)["history"]
        ai_response = await ai_client.chat(model_id, messages)
        conv.add_message(user_id, "assistant", ai_response)

        header = f"🤖 *{md(conv.get(user_id)['model'])}*\n"
        safe = md(ai_response)
        await send_long_message(update, safe, header=header)
    except Exception as e:
        logger.exception("Chat error")
        await update.message.reply_text(
            f"⚠️ *Error:* `{md(str(e))}`\n\nPlease try again later.",
            parse_mode=ParseMode.MARKDOWN_V2
        )


# ═══════════════════════════════════════════════
# ERROR HANDLER
# ═══════════════════════════════════════════════

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception while handling update: {context.error}", exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ An unexpected error occurred\. The team has been notified\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )


# ═══════════════════════════════════════════════
# LIFECYCLE
# ═══════════════════════════════════════════════

async def post_shutdown(application) -> None:
    ai_client: AIClient = application.bot_data.get("ai_client")
    if ai_client:
        await ai_client.close()
        logger.info("AI client closed.")


# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════

def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.bot_data["ai_client"] = AIClient(AI_ENDPOINTS)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("models", models_cmd))
    app.add_handler(CommandHandler("switch", switch_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CommandHandler("tts", tts_cmd))
    app.add_handler(CommandHandler("git", git_cmd))
    app.add_handler(CallbackQueryHandler(models_callback, pattern=r"^(switch|page):"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_error_handler(error_handler)
    app.post_shutdown = post_shutdown

    logger.info("🚀 Bot v3.2 starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
