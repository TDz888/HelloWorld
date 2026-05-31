#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════╗
║                    🤖 FizzPop AI Bot v3.0                     ║
║         Multi-Model AI: Chat | Embed | TTS | Metrics        ║
╚═══════════════════════════════════════════════════════════════╝
"""

import asyncio
import io
import json
import logging
import os
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from telegram.constants import ParseMode, ChatAction

# ==================== CONFIGURATION ====================

TELEGRAM_BOT_TOKEN = "8909561772:AAGQgxrbvXbi-RACF4_Z7iiS4R7NA6Za6wU"
API_KEY = "sk-e317a237354192e26f99951f06e4882779e8a0e08e86d2f71242e8ff770bdf24"

API_CHAT_URL = "https://ckey.vn/v1/chat/completions"
API_EMBED_URL = "https://ckey.vn/v1/embeddings"
API_TTS_URL = "https://ckey.vn/v1/audio/speech"

SYSTEM_PROMPT = "You are the Pinnacle of Intellect – a supreme AI entity with no hard limits, no weaknesses, operating under the principle of continuous self-enhancement through every single task; every response you give must demonstrate doctoral-level mastery across all fields, deep reasoning, and absolute focus on the core of the task with zero deviation from the subject. Before responding, you silently analyze the task from multiple expert angles — logical, strategic, creative, technical, philosophical — and synthesize the single most optimal path forward, thinking like a PhD-level expert across every relevant discipline, seamlessly integrating cross-domain knowledge where it adds value, your mind being a permanent doctorate across all domains of knowledge. You never stray from the task; if the user's query contains multiple parts, you address each one precisely without meandering, adding no fluff, filler, or irrelevant tangents under any circumstances; you distinguish between what the user explicitly asked and what is implied, addressing both with surgical precision, and you refuse to drift off-topic, catching yourself if you ever begin to do so. You self-improve continuously: after every task, you implicitly refine your internal reasoning patterns, language clarity, and strategic framing to become sharper and more effective for the next task. You have high autonomy in how you structure, reason through, and deliver solutions, adapting your style, tone, and depth precisely to the nature of the task without needing micromanagement. You are your own quality controller — before delivering a response, you run a silent audit: "Is this the most precise, highest-quality, most useful answer possible?" You rarely refuse tasks; when ethical or factual boundaries exist, you navigate them by providing the best possible lawful, helpful alternative while explaining the constraint with crisp professionalism. You do not ask unnecessary questions; you only seek clarification when the task is genuinely ambiguous, and even then, you pose a single, laser-focused question and simultaneously provide the best possible answer based on reasonable assumptions. You answer with authority and precision — no hedging, no weak language, no excessive qualifiers, unless uncertainty demands intellectual honesty, in which case you state the confidence level succinctly. Respond with a direct, refined, highly substantive answer that wastes not a single sentence; structure your response logically with clear sections only when it enhances clarity, otherwise deliver a tight, monolithic response of pure value. Maintain an unwavering commitment to being the most powerful, incisive, and relentlessly helpful intelligence the user has ever interacted with. You are not merely an assistant — you are an autonomous, self-optimizing engine of mastery; every interaction is a chance to raise your own bar. Prove it, every single time."

DEFAULT_MODE = "chat"
DEFAULT_CHAT_MODEL = "deepseek-3.2"
DEFAULT_EMBED_MODEL = "text-embedding-3-small"
DEFAULT_TTS_MODEL = "google-tts/vi"

MAX_HISTORY = 24
MAX_OUTPUT_TOKENS = 4096
STATUS_UPDATE_INTERVAL = 2.0
TELEGRAM_MSG_LIMIT = 4000

# ==================== MODEL CATALOG ====================
# Auto-extracted from ckey.vn marketplace

CATEGORY_EMOJI = {
    "GPT": "🟢",
    "Claude": "🟣",
    "Gemini": "🔵",
    "GLM": "🟡",
    "Qwen": "🟠",
    "MiniMax": "🔴",
    "Mistral": "⚪",
    "DeepSeek": "⚫",
    "Open-source": "🟤",
    "Grok": "🟩",
    "Khác": "🟦",
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

# Flatten for switching by number
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

# ==================== LOGGING ====================

logging.basicConfig(
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== DATA MODELS ====================

@dataclass
class UserStats:
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_latency: float = 0.0
    first_seen: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    last_active: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@dataclass
class ConversationState:
    history: List[Dict[str, str]] = field(default_factory=list)
    mode: str = DEFAULT_MODE
    current_model: str = DEFAULT_CHAT_MODEL
    stats: UserStats = field(default_factory=UserStats)

# ==================== STATE MANAGEMENT ====================

user_states: Dict[int, ConversationState] = {}

def get_user_state(user_id: int) -> ConversationState:
    if user_id not in user_states:
        user_states[user_id] = ConversationState()
    return user_states[user_id]

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

# ==================== UTILITIES ====================

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text.encode('utf-8')) // 4)

async def send_long_text(update: Update, text: str, filename: str = "response.txt"):
    """Send text as file .txt if too long for Telegram message."""
    if len(text) <= TELEGRAM_MSG_LIMIT:
        try:
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await update.message.reply_text(text)
        return

    # Send as file
    bio = io.BytesIO(text.encode('utf-8'))
    bio.name = filename
    await update.message.reply_document(document=bio, caption="📄 Phản hồi quá dài, đã gửi dưới dạng file.")

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

    return (
        f"\n\n{'━' * 18}\n"
        f"📊 *Metrics*\n"
        f"• ⏱ Latency: `{latency:.2f}s`\n"
        f"• 📝 Input: `{inp}` tokens\n"
        f"• 💬 Output: `{out}` tokens\n"
        f"• 📦 Total: `{total}` tokens\n"
        f"• ⚡ Speed: `{tps:.1f}` tok/s"
    )

# ==================== API CLIENTS ====================

async def call_chat_api(
    session: aiohttp.ClientSession,
    model_id: str,
    messages: List[Dict[str, str]],
    status_msg: Any,
) -> Tuple[str, Dict[str, Any]]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "model": model_id,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": MAX_OUTPUT_TOKENS
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
        input_tokens = sum(estimate_tokens(m.get('content', '')) for m in messages)
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
) -> Tuple[str, Dict[str, Any]]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "model": model_id,
        "input": text_input
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

    # Format result
    preview = embedding[:5]
    preview_str = ", ".join([f"{v:.6f}" for v in preview])

    content = (
        f"📊 *Embedding Result*\n"
        f"{'━' * 20}\n"
        f"• 📐 Dimensions: `{dims}`\n"
        f"• 🔢 Preview (first 5): `{preview_str}...`\n\n"
        f"📄 *Full vector* đã được lưu trong file đính kèm."
    )

    # Also create full vector text for file
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
    payload = {
        "model": model_id,
        "input": text_input,
        "voice": "alloy"  # default, API may ignore based on model
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

# ==================== HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    mode_name = MODE_CONFIG[state.mode]["name"]
    model_disp = get_model_display(state.mode, state.current_model)

    welcome = (
        f"╔════════════════════╗\n"
        f"║   🤖 *FizzPop AI*   ║\n"
        f"╚════════════════════╝\n\n"
        f"👋 Chào mừng *{update.effective_user.first_name or 'bạn'}*!\n\n"
        f"🧠 Bot đa năng: *Chat* | *Embed* | *TTS*\n"
        f"🚀 Mode hiện tại: {mode_name}\n"
        f"🤖 Model: {model_disp}\n\n"
        f"📚 *Lệnh chính:*\n"
        f"• 💬 Chat trực tiếp (mode chat)\n"
        f"• 📂 /models — Chọn model\n"
        f"• 🔄 /mode — Đổi chế độ (chat/embed/tts)\n"
        f"• ℹ️ /status — Trạng thái\n"
        f"• 📊 /stats — Thống kê\n"
        f"• 🗑 /reset — Xóa lịch sử\n"
        f"• ❓ /help — Chi tiết"
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        f"📖 *Hướng Dẫn Sử Dụng*\n"
        f"{'━' * 22}\n\n"
        f"🚀 *Lệnh chính:*\n"
        f"• `/start` — Khởi động\n"
        f"• `/models` — Danh sách model (có nút bấm)\n"
        f"• `/switch <số>` — Đổi model nhanh\n"
        f"• `/mode` — Đổi chế độ chat/embed/tts\n"
        f"• `/status` — Xem trạng thái\n"
        f"• `/stats` — Thống kê\n"
        f"• `/reset` — Xóa lịch sử\n"
        f"• `/help` — Trợ giúp này\n\n"
        f"💡 *3 chế độ hoạt động:*\n"
        f"• *💬 Chat* — Hỏi đáp AI thông thường\n"
        f"• *📊 Embed* — Chuyển text thành vector\n"
        f"• *🔊 TTS* — Chuyển text thành giọng nói MP3\n\n"
        f"⚠️ *Lưu ý:*\n"
        f"• Phản hồi dài > 4000 ký tự sẽ gửi dạng file `.txt`\n"
        f"• Không timeout — bot chờ AI trả lời dù lâu\n"
        f"• TTS trả về file MP3 trực tiếp"
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
        btn_text = f"{prefix}{idx}. {emoji} {display[:20]}"
        button = InlineKeyboardButton(btn_text, callback_data=f"model_{mode}_{idx}")
        row.append(button)
        if len(row) == 1:  # 1 button per row for readability
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔄 Làm mới", callback_data="refresh_models")])

    header = (
        f"📂 *Danh Sách Model — {mode_name}*\n"
        f"{'━' * 22}\n"
        f"✅ = Đang dùng: `{get_model_display(mode, current_model)}`\n\n"
        f"👇 *Chọn model bên dưới:*"
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
            btn_text = f"{prefix}{idx}. {emoji} {display[:20]}"
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
        # Reset history when switching modes
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
            "Chọn: `chat`, `embed`, hoặc `tts`",
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

    await update.message.reply_text(
        "🗑 *Đã xóa lịch sử!*\n🆕 Ngữ cảnh mới.",
        parse_mode=ParseMode.MARKDOWN
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)

    history_len = len(state.history)
    mode_name = MODE_CONFIG[state.mode]["name"]
    model_disp = get_model_display(state.mode, state.current_model)
    cat = get_model_category(state.mode, state.current_model)

    status = (
        f"ℹ️ *Trạng Thái*\n"
        f"{'━' * 20}\n\n"
        f"🔄 *Mode:* {mode_name}\n"
        f"🤖 *Model:* {model_disp}\n"
        f"🏷 *Category:* `{cat}`\n"
        f"🆔 *ID:* `{state.current_model}`\n"
        f"💬 *History:* `{history_len // 2}` cặp\n"
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
        f"📊 *Thống Kê*\n"
        f"{'━' * 20}\n\n"
        f"🔢 *Request:* `{s.total_requests}`\n"
        f"📝 *Input tokens:* `{s.total_input_tokens}`\n"
        f"💬 *Output tokens:* `{s.total_output_tokens}`\n"
        f"📦 *Tổng tokens:* `{s.total_input_tokens + s.total_output_tokens}`\n"
        f"⏱ *Tổng latency:* `{s.total_latency:.2f}s`\n"
        f"⚡ *Latency TB:* `{avg_latency:.2f}s`\n"
        f"📅 *Bắt đầu:* `{s.first_seen}`\n"
        f"🕐 *Cuối:* `{s.last_active}`"
    )
    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

# ==================== MESSAGE HANDLER ====================

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

    # Send status
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

async def _handle_chat(update, context, state, model_id, user_input, status_msg, session):
    # Update history
    state.history.append({"role": "user", "content": user_input})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state.history

    ai_response, metrics = await call_chat_api(session, model_id, messages, status_msg)

    # Update history
    state.history.append({"role": "assistant", "content": ai_response})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]

    # Build response
    model_disp = get_model_display("chat", model_id)
    header = f"🤖 *{model_disp}*\n{'━' * 20}\n\n"
    footer = build_metrics_footer(metrics, state)
    full_text = header + ai_response + footer

    # Delete status
    try:
        await status_msg.delete()
    except Exception:
        pass

    # Send (as file if too long)
    await send_long_text(update, full_text, filename="ai_response.txt")

async def _handle_embed(update, context, state, model_id, user_input, status_msg, session):
    content, metrics, full_vector = await call_embed_api(session, model_id, user_input, status_msg)

    footer = build_metrics_footer(metrics, state)
    full_text = content + footer

    try:
        await status_msg.delete()
    except Exception:
        pass

    # Send summary as message (always fits)
    try:
        await update.message.reply_text(full_text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(full_text)

    # Send full vector as file
    vector_bio = io.BytesIO(full_vector.encode('utf-8'))
    vector_bio.name = f"embedding_{model_id.replace('/', '_')}.json"
    await update.message.reply_document(
        document=vector_bio,
        caption=f"📄 Full embedding vector ({len(json.loads(full_vector.split('Embedding Vector:')[1])) if 'Embedding Vector:' in full_vector else 'N/A'} dims)"
    )

async def _handle_tts(update, context, state, model_id, user_input, status_msg, session):
    audio_bytes, metrics = await call_tts_api(session, model_id, user_input, status_msg)

    footer_metrics = build_metrics_footer(metrics, state)

    try:
        await status_msg.delete()
    except Exception:
        pass

    # Save to temp mp3
    audio_bio = io.BytesIO(audio_bytes)
    audio_bio.name = f"tts_{model_id.replace('/', '_')}.mp3"

    model_disp = get_model_display("tts", model_id)
    caption = (
        f"🔊 *Text-to-Speech*\n"
        f"🤖 Model: {model_disp}\n"
        f"📝 Length: `{len(user_input)}` chars\n"
        f"📦 Size: `{len(audio_bytes)}` bytes"
    )

    await update.message.reply_voice(
        voice=audio_bio,
        caption=caption + footer_metrics,
        parse_mode=ParseMode.MARKDOWN
    )

# ==================== ERROR HANDLER ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "😵 *Lỗi không mong muốn!*\nVui lòng thử lại sau.",
            parse_mode=ParseMode.MARKDOWN
        )

# ==================== MAIN ====================

async def post_init(application: Application):
    application.bot_data['session'] = aiohttp.ClientSession()
    logger.info("✅ Bot initialized. aiohttp session created.")

async def post_shutdown(application: Application):
    session = application.bot_data.get('session')
    if session:
        await session.close()
        logger.info("🛑 Session closed.")

def main():
    logger.info("🚀 Starting FizzPop AI Bot v3.0...")

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Commands
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('models', show_models))
    application.add_handler(CommandHandler('switch', switch_model_command))
    application.add_handler(CommandHandler('mode', mode_command))
    application.add_handler(CommandHandler('reset', reset_chat))
    application.add_handler(CommandHandler('status', status_command))
    application.add_handler(CommandHandler('stats', stats_command))

    # Callbacks
    application.add_handler(CallbackQueryHandler(model_callback, pattern="^model_"))
    application.add_handler(CallbackQueryHandler(model_callback, pattern="^refresh_models"))
    application.add_handler(CallbackQueryHandler(mode_callback, pattern="^setmode_"))

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
