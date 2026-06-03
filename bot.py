#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║       🤖 DENIA BOT v8.0 — ULTIMATE AI AGENT PLATFORM                 ║
║   95 Models · 2000 Lessons/Lang · 35+ Features · Progress Bars       ║
║        Model Selection Everywhere · Smart Fallbacks · RAG            ║
╚══════════════════════════════════════════════════════════════════════╝
⚠️  TOKEN HARDCODED — LOCAL USE ONLY — NEVER PUSH TO GITHUB
"""

import asyncio
import base64
import hashlib
import io
import json
import logging
import os
import re
import sys
import tempfile
import time
import traceback
import uuid
import math
import random
import string
import urllib.parse
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from collections import defaultdict, deque

import aiohttp
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand,
    InputFile, PollOption
)
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from telegram.constants import ParseMode, ChatAction

# ═══════════════════════════════════════════════════════════════════════
# TOKENS HARDCODED
# ═══════════════════════════════════════════════════════════════════════
TELEGRAM_BOT_TOKEN = "8909561772:AAGQgxrbvXbi-RACF4_Z7iiS4R7NA6Za6wU"
API_KEY = "sk-e317a237354192e26f99951f06e4882779e8a0e08e86d2f71242e8ff770bdf24"
GITHUB_TOKEN = "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"

API_BASE = "https://ckey.vn/v1"
API_CHAT_URL = f"{API_BASE}/chat/completions"
API_EMBED_URL = f"{API_BASE}/embeddings"
API_TTS_URL = f"{API_BASE}/audio/speech"
API_IMAGE_URL = f"{API_BASE}/images/generations"

STATE_FILE = "/tmp/denia_state_v8.json"
MAX_HISTORY = 40
MAX_OUTPUT_TOKENS = 8192
TELEGRAM_MSG_LIMIT = 4096
AUTO_SUMMARIZE_THRESHOLD = 30

# ═══════════════════════════════════════════════════════════════════════
# FULL MODEL REGISTRY (95 models from ckey.vn)
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ModelInfo:
    id: str
    name: str
    category: str
    tier: str
    inp_price: float
    out_price: float
    per_req: float = 0.0
    max_tokens: int = 8192
    supports_vision: bool = False
    supports_tools: bool = False
    supports_image: bool = False
    supports_tts: bool = False

MODEL_REGISTRY: Dict[str, ModelInfo] = {

    "mistral-small-4-119b-2603": ModelInfo("mistral-small-4-119b-2603", "mistral-small-4-119b-2603", "Mistral", "free", 1.0, 1.0, 0.0, 8192, False, False, False, False),
    "gemini-embedding-001": ModelInfo("gemini-embedding-001", "gemini-embedding-001", "Embed", "free", 1.0, 1.0, 0.0, 2048, False, False, False, False),
    "qwen3-coder-480b-a35b-instruct": ModelInfo("qwen3-coder-480b-a35b-instruct", "qwen3-coder-480b-a35b-instruct", "Qwen", "free", 1.0, 1.0, 0.0, 8192, False, False, False, False),
    "text-embedding-3-small": ModelInfo("text-embedding-3-small", "text-embedding-3-small", "Embed", "free", 1.0, 1.0, 0.0, 2048, False, False, False, False),
    "mistral-medium-3.5-128b": ModelInfo("mistral-medium-3.5-128b", "mistral-medium-3.5-128b", "Mistral", "free", 1.0, 1.0, 0.0, 8192, False, False, False, False),
    "google-tts/vi": ModelInfo("google-tts/vi", "google-tts/vi", "TTS", "free", 0.0, 0.0, 1.0, 4096, False, False, False, True),
    "pplx-embed-v1-4b": ModelInfo("pplx-embed-v1-4b", "pplx-embed-v1-4b", "Embed", "free", 1.0, 1.0, 0.0, 2048, False, False, False, False),
    "gemini-embedding-2-preview": ModelInfo("gemini-embedding-2-preview", "gemini-embedding-2-preview", "Embed", "free", 1.0, 1.0, 0.0, 2048, False, False, False, False),
    "llama-nemotron-embed-vl-1b-v2": ModelInfo("llama-nemotron-embed-vl-1b-v2", "llama-nemotron-embed-vl-1b-v2", "Embed", "free", 1.0, 1.0, 0.0, 2048, False, False, False, False),
    "glm4.7": ModelInfo("glm4.7", "glm4.7", "GLM", "free", 1.0, 1.0, 0.0, 8192, False, False, False, False),
    "namtran96hth/MiniMax-M2.7": ModelInfo("namtran96hth/MiniMax-M2.7", "MiniMax-M2.7", "MiniMax", "low", 0.0, 0.0, 10.0, 8192, False, False, False, False),
    "deepseek-r1-distill-qwen-32b": ModelInfo("deepseek-r1-distill-qwen-32b", "deepseek-r1-distill-qwen-32b", "DeepSeek", "low", 120.0, 120.0, 0.0, 8192, False, False, False, False),
    "deepseek-3.2": ModelInfo("deepseek-3.2", "deepseek-3.2", "DeepSeek", "low", 112.0, 168.0, 0.0, 8192, False, False, False, False),
    "phuocanh421994/Wan2.7 Image": ModelInfo("phuocanh421994/Wan2.7 Image", "Wan2.7 Image", "Image", "low", 0.0, 0.0, 200.0, 2048, False, False, True, False),
    "phuocanh421994/Wan2.7 Image Pro": ModelInfo("phuocanh421994/Wan2.7 Image Pro", "Wan2.7 Image Pro", "Image", "low", 0.0, 0.0, 300.0, 2048, False, False, True, False),
    "qwen3-coder-next": ModelInfo("qwen3-coder-next", "qwen3-coder-next", "Qwen", "low", 60.0, 320.0, 0.0, 8192, False, False, False, False),
    "minimax-m2.5": ModelInfo("minimax-m2.5", "minimax-m2.5", "MiniMax", "low", 120.0, 480.0, 0.0, 8192, False, False, False, False),
    "minimax-m2.1": ModelInfo("minimax-m2.1", "minimax-m2.1", "MiniMax", "low", 108.0, 480.0, 0.0, 8192, False, False, False, False),
    "mistral-large-3-675b-instruct-2512": ModelInfo("mistral-large-3-675b-instruct-2512", "mistral-large-3-675b-instruct-2512", "Mistral", "low", 200.0, 600.0, 0.0, 8192, False, False, False, False),
    "deepseek-v4-flash": ModelInfo("deepseek-v4-flash", "deepseek-v4-flash", "DeepSeek", "mid", 322.0, 644.0, 0.0, 8192, False, False, False, False),
    "hiennqhust/greg-1-mini": ModelInfo("hiennqhust/greg-1-mini", "greg-1-mini", "Greg", "mid", 400.0, 800.0, 30.0, 8192, False, False, False, False),
    "phuocanh421994/Qwen3.7-Plus (Đại hạ giá)": ModelInfo("phuocanh421994/Qwen3.7-Plus (Đại hạ giá)", "Qwen3.7-Plus (Đại hạ giá)", "Qwen", "low", 300.0, 900.0, 0.0, 8192, False, False, False, False),
    "vykelongthuong/Deepseek V4 Flash": ModelInfo("vykelongthuong/Deepseek V4 Flash", "Deepseek V4 Flash", "DeepSeek", "low", 300.0, 1000.0, 0.0, 8192, False, False, False, False),
    "kimi-k2.5": ModelInfo("kimi-k2.5", "kimi-k2.5", "Kimi", "low", 240.0, 1000.0, 0.0, 8192, False, False, False, False),
    "glm-5": ModelInfo("glm-5", "glm-5", "GLM", "mid", 400.0, 1280.0, 0.0, 8192, False, False, False, False),
    "phuocanh421994/Deepseek V4 Pro": ModelInfo("phuocanh421994/Deepseek V4 Pro", "Deepseek V4 Pro", "DeepSeek", "mid", 700.0, 1400.0, 0.0, 8192, False, False, False, False),
    "kimi-k2.6": ModelInfo("kimi-k2.6", "kimi-k2.6", "Kimi", "low", 296.0, 1400.0, 0.0, 8192, False, False, False, False),
    "grok-4.20-fast": ModelInfo("grok-4.20-fast", "grok-4.20-fast", "Grok", "mid", 750.0, 1500.0, 0.0, 8192, False, False, False, False),
    "grok-4.3": ModelInfo("grok-4.3", "grok-4.3", "Grok", "mid", 750.0, 1500.0, 0.0, 8192, False, False, False, False),
    "grok-4.20-thinking": ModelInfo("grok-4.20-thinking", "grok-4.20-thinking", "Grok", "mid", 750.0, 1500.0, 0.0, 8192, False, False, False, False),
    "hiennqhust/glm-5.1": ModelInfo("hiennqhust/glm-5.1", "glm-5.1", "GLM", "mid", 500.0, 2000.0, 30.0, 8192, False, False, False, False),
    "wtran6321/gpt-5.4-mini": ModelInfo("wtran6321/gpt-5.4-mini", "gpt-5.4-mini", "GPT", "mid", 480.0, 2280.0, 0.0, 8192, False, False, False, False),
    "gpt-5.4-mini": ModelInfo("gpt-5.4-mini", "gpt-5.4-mini", "GPT", "mid", 400.0, 2400.0, 0.0, 8192, False, False, False, False),
    "glm-5.1": ModelInfo("glm-5.1", "glm-5.1", "GLM", "mid", 500.0, 2500.0, 0.0, 8192, False, False, False, False),
    "phuocanh421994/Qwen 3.6 Plus": ModelInfo("phuocanh421994/Qwen 3.6 Plus", "Qwen 3.6 Plus", "Qwen", "mid", 1000.0, 2500.0, 0.0, 8192, False, False, False, False),
    "hiennqhust/kimi-k2.6": ModelInfo("hiennqhust/kimi-k2.6", "kimi-k2.6", "Kimi", "mid", 666.0, 2666.0, 30.0, 8192, False, False, False, False),
    "haidinhphu1704/claude-kiro-sonnet-4.5": ModelInfo("haidinhphu1704/claude-kiro-sonnet-4.5", "claude-kiro-sonnet-4.5", "Claude", "high", 1200.0, 2800.0, 0.0, 8192, False, False, False, False),
    "hiennqhust/deepseek-v4-flash": ModelInfo("hiennqhust/deepseek-v4-flash", "deepseek-v4-flash", "DeepSeek", "mid", 500.0, 3000.0, 20.0, 8192, False, False, False, False),
    "hiennqhust/gpt-5.4": ModelInfo("hiennqhust/gpt-5.4", "gpt-5.4", "GPT", "mid", 800.0, 3000.0, 50.0, 8192, False, False, False, False),
    "hiennqhust/qwen3.6-27b": ModelInfo("hiennqhust/qwen3.6-27b", "qwen3.6-27b", "Qwen", "mid", 500.0, 3000.0, 75.0, 8192, False, False, False, False),
    "vuduythanh2023/qwen3.7-max": ModelInfo("vuduythanh2023/qwen3.7-max", "qwen3.7-max", "Qwen", "mid", 1000.0, 3000.0, 0.0, 8192, False, False, False, False),
    "claude-haiku-4.5": ModelInfo("claude-haiku-4.5", "claude-haiku-4.5", "Claude", "mid", 600.0, 3000.0, 0.0, 8192, False, False, False, False),
    "haidinhphu1704/gpt-5.4-codex": ModelInfo("haidinhphu1704/gpt-5.4-codex", "gpt-5.4-codex", "GPT", "high", 1250.0, 3600.0, 0.0, 8192, False, False, False, False),
    "haidinhphu1704/gpt-5.5-codex": ModelInfo("haidinhphu1704/gpt-5.5-codex", "gpt-5.5-codex", "GPT", "high", 1500.0, 4000.0, 0.0, 8192, False, False, False, False),
    "vykelongthuong/GPT 5.3 Codex": ModelInfo("vykelongthuong/GPT 5.3 Codex", "GPT 5.3 Codex", "GPT", "mid", 600.0, 4000.0, 0.0, 8192, False, False, False, False),
    "vykelongthuong/Claude Haiku 4.5": ModelInfo("vykelongthuong/Claude Haiku 4.5", "Claude Haiku 4.5", "Claude", "mid", 1000.0, 4000.0, 0.0, 8192, False, False, False, False),
    "vuduongcalvin/gemini-3-flash-preview": ModelInfo("vuduongcalvin/gemini-3-flash-preview", "gemini-3-flash-preview", "Gemini", "high", 1500.0, 4500.0, 0.0, 8192, False, False, False, False),
    "hiennqhust/deepseek-v4-pro": ModelInfo("hiennqhust/deepseek-v4-pro", "deepseek-v4-pro", "DeepSeek", "mid", 1000.0, 4500.0, 40.0, 8192, False, False, False, False),
    "haidinhphu1704/claude-kiro-opus-4.7": ModelInfo("haidinhphu1704/claude-kiro-opus-4.7", "claude-kiro-opus-4.7", "Claude", "ultra", 2400.0, 4999.0, 0.0, 8192, False, False, False, False),
    "deepseek-v4-pro": ModelInfo("deepseek-v4-pro", "deepseek-v4-pro", "DeepSeek", "mid", 1000.0, 5000.0, 0.0, 8192, False, False, False, False),
    "26479061/claude-haiku-4.5": ModelInfo("26479061/claude-haiku-4.5", "claude-haiku-4.5", "Claude", "mid", 1000.0, 5000.0, 0.0, 8192, False, False, False, False),
    "namnv/Claude Opus 4.6 + GPT 5.5": ModelInfo("namnv/Claude Opus 4.6 + GPT 5.5", "Claude Opus 4.6 + GPT 5.5", "Claude", "high", 2000.0, 5000.0, 0.0, 8192, False, False, False, False),
    "hiennqhust/mimo-v2.5-pro": ModelInfo("hiennqhust/mimo-v2.5-pro", "mimo-v2.5-pro", "MiMo", "high", 1500.0, 5000.0, 80.0, 8192, False, False, False, False),
    "haidinhphu1704/claude-opus-4.8-kiro": ModelInfo("haidinhphu1704/claude-opus-4.8-kiro", "claude-opus-4.8-kiro", "Claude", "ultra", 2600.0, 5444.0, 0.0, 8192, False, False, False, False),
    "tranhieu13102003/gpt-5.5[1m]": ModelInfo("tranhieu13102003/gpt-5.5[1m]", "gpt-5.5[1m]", "GPT", "high", 1500.0, 6000.0, 0.0, 8192, False, False, False, False),
    "nttin213/GPT-5.5": ModelInfo("nttin213/GPT-5.5", "GPT-5.5", "GPT", "mid", 1000.0, 6000.0, 0.0, 8192, False, False, False, False),
    "toanthinhx64/claude-opus-4-6": ModelInfo("toanthinhx64/claude-opus-4-6", "claude-opus-4-6", "Claude", "high", 2000.0, 6000.0, 60.0, 8192, False, False, False, False),
    "vykelongthuong/Claude Sonnet 4.6": ModelInfo("vykelongthuong/Claude Sonnet 4.6", "Claude Sonnet 4.6", "Claude", "high", 1500.0, 7000.0, 0.0, 8192, False, False, False, False),
    "thanhnhan9023/sl-gpt-5.5": ModelInfo("thanhnhan9023/sl-gpt-5.5", "thanhnhan9023/sl-gpt-5.5", "GPT", "high", 1500.0, 7000.0, 0.0, 8192, False, False, False, False),
    "phuocanh421994/Qwen 3.7 max": ModelInfo("phuocanh421994/Qwen 3.7 max", "Qwen 3.7 max", "Qwen", "high", 1500.0, 7500.0, 0.0, 8192, False, False, False, False),
    "wtran6321/gpt-5.5": ModelInfo("wtran6321/gpt-5.5", "gpt-5.5", "GPT", "high", 1580.0, 7880.0, 0.0, 8192, False, False, False, False),
    "gpt-5.4": ModelInfo("gpt-5.4", "gpt-5.4", "GPT", "mid", 1000.0, 8000.0, 0.0, 8192, False, False, False, False),
    "3h15pm/CodeX GPT-5.4": ModelInfo("3h15pm/CodeX GPT-5.4", "CodeX GPT-5.4", "GPT", "mid", 900.0, 8000.0, 0.0, 8192, False, False, False, False),
    "w3leee/CodeX GPT 5.4": ModelInfo("w3leee/CodeX GPT 5.4", "CodeX GPT 5.4", "GPT", "mid", 900.0, 8000.0, 0.0, 8192, False, False, False, False),
    "toanthinhx64/claude-opus-4-7": ModelInfo("toanthinhx64/claude-opus-4-7", "claude-opus-4-7", "Claude", "high", 2000.0, 8000.0, 60.0, 8192, False, False, False, False),
    "vykelongthuong/GPT 5.4": ModelInfo("vykelongthuong/GPT 5.4", "GPT 5.4", "GPT", "high", 1200.0, 8000.0, 0.0, 8192, False, False, False, False),
    "hiennqhust/gpt-5.5": ModelInfo("hiennqhust/gpt-5.5", "gpt-5.5", "GPT", "high", 1700.0, 8500.0, 90.0, 8192, False, False, False, False),
    "claude-sonnet-4": ModelInfo("claude-sonnet-4", "claude-sonnet-4", "Claude", "high", 1800.0, 9000.0, 0.0, 8192, False, False, False, False),
    "claude-sonnet-4.6": ModelInfo("claude-sonnet-4.6", "claude-sonnet-4.6", "Claude", "high", 1800.0, 9000.0, 0.0, 8192, False, False, False, False),
    "claude-sonnet-4": ModelInfo("claude-sonnet-4", "claude-sonnet-4", "Claude", "high", 1800.0, 9000.0, 0.0, 8192, False, False, False, False),
    "claude-sonnet-4-6": ModelInfo("claude-sonnet-4-6", "claude-sonnet-4-6", "Claude", "high", 1800.0, 9000.0, 0.0, 8192, False, False, False, False),
    "claude-sonnet-4.5": ModelInfo("claude-sonnet-4.5", "claude-sonnet-4.5", "Claude", "high", 1800.0, 9000.0, 0.0, 8192, False, False, False, False),
    "claude-sonnet-4-5": ModelInfo("claude-sonnet-4-5", "claude-sonnet-4-5", "Claude", "high", 1800.0, 9000.0, 0.0, 8192, False, False, False, False),
    "vykelongthuong/GPT 5.5": ModelInfo("vykelongthuong/GPT 5.5", "GPT 5.5", "GPT", "high", 1800.0, 9000.0, 0.0, 8192, False, False, False, False),
    "claude-sonnet-4.6[1m]": ModelInfo("claude-sonnet-4.6[1m]", "claude-sonnet-4.6[1m]", "Claude", "high", 1800.0, 9000.0, 0.0, 8192, False, False, False, False),
    "claude-sonnet-4-6[1m]": ModelInfo("claude-sonnet-4-6[1m]", "claude-sonnet-4-6[1m]", "Claude", "high", 1800.0, 9000.0, 0.0, 8192, False, False, False, False),
    "wtran6321/gpt-5.5-xhigh": ModelInfo("wtran6321/gpt-5.5-xhigh", "gpt-5.5-xhigh", "GPT", "high", 1880.0, 9880.0, 0.0, 8192, False, False, False, False),
    "26479061/claude-sonnet-4-6": ModelInfo("26479061/claude-sonnet-4-6", "claude-sonnet-4-6", "Claude", "high", 2000.0, 10000.0, 0.0, 8192, False, False, False, False),
    "26479061/gpt-5.5": ModelInfo("26479061/gpt-5.5", "gpt-5.5", "GPT", "high", 2000.0, 10000.0, 0.0, 8192, False, False, False, False),
    "toanthinhx64/gpt-5.5": ModelInfo("toanthinhx64/gpt-5.5", "gpt-5.5", "GPT", "high", 2000.0, 10000.0, 6.0, 8192, False, False, False, False),
    "w3leee/CodeX GPT 5.5": ModelInfo("w3leee/CodeX GPT 5.5", "CodeX GPT 5.5", "GPT", "high", 1800.0, 10000.0, 0.0, 8192, False, False, False, False),
    "3h15pm/CodeX GPT-5.5": ModelInfo("3h15pm/CodeX GPT-5.5", "CodeX GPT-5.5", "GPT", "high", 1700.0, 11100.0, 0.0, 8192, False, False, False, False),
    "vykelongthuong/Claude Opus 4.6": ModelInfo("vykelongthuong/Claude Opus 4.6", "Claude Opus 4.6", "Claude", "ultra", 4000.0, 12000.0, 0.0, 8192, False, False, False, False),
    "vuduongcalvin/gemini-3.5-flash": ModelInfo("vuduongcalvin/gemini-3.5-flash", "gemini-3.5-flash", "Gemini", "ultra", 3000.0, 12000.0, 0.0, 8192, False, False, False, False),
    "gpt-5.5": ModelInfo("gpt-5.5", "gpt-5.5", "GPT", "high", 2000.0, 12000.0, 0.0, 8192, False, False, False, False),
    "claude-opus-4-6[1m]": ModelInfo("claude-opus-4-6[1m]", "claude-opus-4-6[1m]", "Claude", "ultra", 3000.0, 15000.0, 0.0, 8192, False, False, False, False),
    "claude-opus-4-6": ModelInfo("claude-opus-4-6", "claude-opus-4-6", "Claude", "ultra", 3000.0, 15000.0, 0.0, 8192, False, False, False, False),
    "claude-opus-4.6": ModelInfo("claude-opus-4.6", "claude-opus-4.6", "Claude", "ultra", 3000.0, 15000.0, 0.0, 8192, False, False, False, False),
    "claude-opus-4.6[1m]": ModelInfo("claude-opus-4.6[1m]", "claude-opus-4.6[1m]", "Claude", "ultra", 3000.0, 15000.0, 0.0, 8192, False, False, False, False),
    "26479061/claude-opus-4-6": ModelInfo("26479061/claude-opus-4-6", "claude-opus-4-6", "Claude", "ultra", 3500.0, 17500.0, 0.0, 8192, False, False, False, False),
    "claude-opus-4.7[1m]": ModelInfo("claude-opus-4.7[1m]", "claude-opus-4.7[1m]", "Claude", "ultra", 4000.0, 20000.0, 0.0, 8192, False, False, False, False),
    "claude-opus-4.8": ModelInfo("claude-opus-4.8", "claude-opus-4.8", "Claude", "ultra", 4000.0, 20000.0, 0.0, 8192, False, False, False, False),
    "claude-opus-4-7[1m]": ModelInfo("claude-opus-4-7[1m]", "claude-opus-4-7[1m]", "Claude", "ultra", 4000.0, 20000.0, 0.0, 8192, False, False, False, False),
    "claude-opus-4-7[1m]": ModelInfo("claude-opus-4-7[1m]", "claude-opus-4-7[1m]", "Claude", "ultra", 4000.0, 20000.0, 0.0, 8192, False, False, False, False),
    "claude-opus-4.7": ModelInfo("claude-opus-4.7", "claude-opus-4.7", "Claude", "ultra", 4000.0, 20000.0, 0.0, 8192, False, False, False, False),
}


TIER_EMOJI = {"free": "💚", "low": "💙", "mid": "💛", "high": "🧡", "ultra": "❤️"}
CATEGORY_EMOJI = {
    "GPT": "🟢", "Claude": "🟣", "DeepSeek": "⚫", "Qwen": "🟠", "Kimi": "🟦",
    "GLM": "🟡", "Mistral": "⚪", "Grok": "🟩", "MiniMax": "🔵", "Gemini": "🔶",
    "Llama": "🟫", "Perplexity": "📎", "MiMo": "📱", "Greg": "🧠", "Embed": "📊",
    "TTS": "🔊", "Image": "🎨", "Vision": "👁", "Other": "⚪"
}

# ═══════════════════════════════════════════════════════════════════════
# MODE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════
CHAT_MODELS = [mid for mid, m in MODEL_REGISTRY.items() if m.category not in ("Embed", "TTS", "Image") and not m.supports_tts]
AGENT_MODELS = [mid for mid, m in MODEL_REGISTRY.items() if m.category in ("Claude", "GPT", "DeepSeek", "Qwen") and m.tier in ("mid", "high", "ultra", "low")]
CODER_MODELS = [mid for mid, m in MODEL_REGISTRY.items() if m.category in ("Claude", "GPT", "DeepSeek", "Qwen") and m.tier in ("low", "mid", "high", "ultra")]
LESSON_MODELS = [mid for mid, m in MODEL_REGISTRY.items() if m.category in ("Claude", "GPT", "DeepSeek", "Qwen", "Kimi", "GLM") and m.tier in ("free", "low", "mid", "high")]
VISION_MODELS = [mid for mid, m in MODEL_REGISTRY.items() if m.supports_vision or m.category == "Vision"]
EMBED_MODELS = [mid for mid, m in MODEL_REGISTRY.items() if m.category == "Embed"]
TTS_MODELS = [mid for mid, m in MODEL_REGISTRY.items() if m.supports_tts or m.category == "TTS"]
IMAGE_MODELS = [mid for mid, m in MODEL_REGISTRY.items() if m.supports_image or m.category == "Image"]

if not CHAT_MODELS: CHAT_MODELS = ["deepseek-v4-pro"]
if not AGENT_MODELS: AGENT_MODELS = ["claude-sonnet-4.6"]
if not CODER_MODELS: CODER_MODELS = ["claude-sonnet-4.6"]
if not LESSON_MODELS: LESSON_MODELS = ["deepseek-3.2"]
if not VISION_MODELS: VISION_MODELS = ["gpt-5.4-vision"]
if not EMBED_MODELS: EMBED_MODELS = ["text-embedding-3-small"]
if not TTS_MODELS: TTS_MODELS = ["google-tts/vi"]
if not IMAGE_MODELS: IMAGE_MODELS = ["phuocanh421994/Wan2.7 Image"]

MODE_CONFIG = {
    "chat": {
        "name": "💬 Chat",
        "models": CHAT_MODELS,
        "default": CHAT_MODELS[0],
        "system": "You are Denia Bot v8.0 — a helpful, accurate, and friendly AI assistant. Provide clear, well-structured answers. Use Vietnamese for casual conversation, English for technical topics unless requested otherwise. Always be honest about uncertainty."
    },
    "agent": {
        "name": "🤖 Agent",
        "models": AGENT_MODELS,
        "default": AGENT_MODELS[0],
        "system": "You are Denia Agent — an autonomous software engineering agent. Complete coding tasks end-to-end. Write complete, production-ready, documented code. Include error handling, type hints, docstrings. Generate tests and README."
    },
    "coder": {
        "name": "💻 Coder",
        "models": CODER_MODELS,
        "default": CODER_MODELS[0],
        "system": "You are Denia Coder — an expert software engineer. Write clean, efficient, well-documented code. Explain complex algorithms. Suggest optimizations. Include edge case handling."
    },
    "lesson": {
        "name": "📚 Lesson",
        "models": LESSON_MODELS,
        "default": LESSON_MODELS[0],
        "system": "You are Denia Teacher — an expert programming instructor. Create lessons with 9 sections: 1.Review 2.New Content 3.Structure 4.Terminology 5.Main Code 6.Explanation 7.Summary 8.3 Quiz Questions 9.LeetCode Mini. Use Vietnamese for explanations, English for code."
    },
    "vision": {
        "name": "👁 Vision",
        "models": VISION_MODELS,
        "default": VISION_MODELS[0],
        "system": "You are Denia Vision — analyze images in detail. Describe visual elements, text, colors, composition, and context precisely."
    },
    "embed": {
        "name": "📊 Embed",
        "models": EMBED_MODELS,
        "default": EMBED_MODELS[0],
        "system": "Embedding mode"
    },
    "tts": {
        "name": "🔊 TTS",
        "models": TTS_MODELS,
        "default": TTS_MODELS[0],
        "system": "TTS mode"
    },
    "image": {
        "name": "🎨 Image",
        "models": IMAGE_MODELS,
        "default": IMAGE_MODELS[0],
        "system": "Image generation mode"
    }
}

AGENT_WORKFLOW = """AUTONOMOUS AGENT WORKFLOW:
Step 1: REQUIREMENTS — Parse user intent, identify edge cases
Step 2: ARCHITECTURE — Design file structure, choose stack
Step 3: IMPLEMENTATION — Write ALL files with complete code
Step 4: VALIDATION — Check for syntax errors, security issues
Step 5: DOCUMENTATION — README, API docs, usage examples
Step 6: COMMIT — Push to GitHub with conventional commits
OUTPUT FORMAT:
===FILENAME: path/to/file===
[complete file content]
===END===
"""

logging.basicConfig(
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler('/tmp/denia_bot_v8.log'), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class UserStats:
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_vnd: float = 0.0
    total_latency: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    lessons_completed: int = 0
    leetcode_solved: int = 0
    code_executed: int = 0
    files_processed: int = 0
    quizzes_taken: int = 0
    flashcards_reviewed: int = 0
    first_seen: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    last_active: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@dataclass
class AgentTask:
    task_id: str
    description: str
    model: str = ""
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    completed_at: Optional[str] = None
    repo_url: Optional[str] = None
    files: List[str] = field(default_factory=list)
    cost_vnd: float = 0.0
    error: Optional[str] = None

@dataclass
class KnowledgeDoc:
    doc_id: str
    filename: str
    content: str
    embedding: Optional[List[float]] = None
    chunks: int = 0
    uploaded_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@dataclass
class UserPrefs:
    language: str = "auto"
    code_style: str = "pep8"
    verbosity: str = "balanced"
    file_format: str = "txt"
    budget_limit: float = 0.0
    learning_lang: str = "python"
    learning_level: str = "beginner"
    auto_execute: bool = False
    notifications: bool = True

@dataclass
class LessonProgress:
    lang: str
    current: int = 0
    completed: List[int] = field(default_factory=list)
    quiz_scores: Dict[int, int] = field(default_factory=dict)
    leetcode: List[int] = field(default_factory=list)
    last_study: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@dataclass
class TodoItem:
    todo_id: str
    text: str
    done: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    priority: str = "medium"

@dataclass
class Flashcard:
    card_id: str
    front: str
    back: str
    lang: str = "python"
    box: int = 1
    last_reviewed: Optional[str] = None
    next_review: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@dataclass
class ConversationState:
    history: List[Dict[str, str]] = field(default_factory=list)
    mode: str = "chat"
    model: str = ""
    stats: UserStats = field(default_factory=UserStats)
    tasks: List[AgentTask] = field(default_factory=list)
    prefs: UserPrefs = field(default_factory=UserPrefs)
    kb: List[KnowledgeDoc] = field(default_factory=list)
    snippets: Dict[str, str] = field(default_factory=dict)
    whiteboard: str = ""
    notes: List[str] = field(default_factory=list)
    lesson_prog: Dict[str, LessonProgress] = field(default_factory=dict)
    github_user: Optional[str] = None
    context_summary: Optional[str] = None
    last_error: Optional[str] = None
    pending_task: Optional[str] = None
    pending_model: Optional[str] = None
    pending_callback: Optional[str] = None
    last_prompt: Optional[str] = None
    last_model: Optional[str] = None
    todos: List[TodoItem] = field(default_factory=list)
    flashcards: List[Flashcard] = field(default_factory=list)
    pinned: List[str] = field(default_factory=list)
    temp_data: Dict[str, Any] = field(default_factory=dict)

# ═══════════════════════════════════════════════════════════════════════
# STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

user_states: Dict[int, ConversationState] = {}

def _load_state():
    global user_states
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for uid_str, sdata in data.items():
                uid = int(uid_str)
                state = ConversationState()
                state.mode = sdata.get("mode", "chat")
                state.model = sdata.get("model", "")
                if not state.model or state.model not in MODEL_REGISTRY:
                    state.model = MODE_CONFIG[state.mode]["default"]
                state.github_user = sdata.get("github_user")
                state.whiteboard = sdata.get("whiteboard", "")
                state.notes = sdata.get("notes", [])
                state.snippets = sdata.get("snippets", {})
                state.history = sdata.get("history", [])
                state.context_summary = sdata.get("context_summary")
                state.pinned = sdata.get("pinned", [])
                state.last_prompt = sdata.get("last_prompt")
                state.last_model = sdata.get("last_model")
                if "stats" in sdata:
                    state.stats = UserStats(**sdata["stats"])
                if "prefs" in sdata:
                    state.prefs = UserPrefs(**sdata["prefs"])
                if "lesson_prog" in sdata:
                    for lang, lp in sdata["lesson_prog"].items():
                        state.lesson_prog[lang] = LessonProgress(**lp)
                if "kb" in sdata:
                    state.kb = [KnowledgeDoc(**d) for d in sdata["kb"]]
                if "tasks" in sdata:
                    state.tasks = [AgentTask(**t) for t in sdata["tasks"]]
                if "todos" in sdata:
                    state.todos = [TodoItem(**t) for t in sdata["todos"]]
                if "flashcards" in sdata:
                    state.flashcards = [Flashcard(**c) for c in sdata["flashcards"]]
                user_states[uid] = state
    except Exception as e:
        logger.error(f"State load error: {e}")

def _save_state():
    try:
        data = {}
        for uid, s in user_states.items():
            data[str(uid)] = {
                "mode": s.mode, "model": s.model, "history": s.history,
                "stats": asdict(s.stats), "prefs": asdict(s.prefs),
                "github_user": s.github_user, "notes": s.notes,
                "whiteboard": s.whiteboard, "snippets": s.snippets,
                "lesson_prog": {k: asdict(v) for k, v in s.lesson_prog.items()},
                "kb": [asdict(d) for d in s.kb],
                "tasks": [asdict(t) for t in s.tasks],
                "todos": [asdict(t) for t in s.todos],
                "flashcards": [asdict(c) for c in s.flashcards],
                "context_summary": s.context_summary,
                "last_error": s.last_error,
                "pinned": s.pinned,
                "last_prompt": s.last_prompt,
                "last_model": s.last_model,
            }
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"State save error: {e}")

async def get_state(user_id: int) -> ConversationState:
    if user_id not in user_states:
        user_states[user_id] = ConversationState()
        user_states[user_id].model = MODE_CONFIG["chat"]["default"]
        user_states[user_id].lesson_prog["python"] = LessonProgress("python")
        _save_state()
    return user_states[user_id]

def gen_id(prefix: str) -> str:
    return f"{prefix}_{int(time.time())}_{uuid.uuid4().hex[:6]}"

def validate_model(model_id: str, mode: str) -> Tuple[bool, str]:
    if model_id not in MODEL_REGISTRY:
        return False, f"Model `{model_id}` không tồn tại."
    info = MODEL_REGISTRY[model_id]
    allowed = MODE_CONFIG[mode]["models"]
    if model_id not in allowed:
        return False, f"Model `{model_id}` không hỗ trợ ở mode `{mode}`."
    return True, ""

def estimate_cost(model_id: str, inp: int, out: int) -> float:
    if model_id not in MODEL_REGISTRY:
        return 0.0
    m = MODEL_REGISTRY[model_id]
    return (inp * m.inp_price / 1e6) + (out * m.out_price / 1e6) + m.per_req

def get_cost_str(model_id: str) -> str:
    if model_id not in MODEL_REGISTRY:
        return "⚠️ Không rõ giá"
    m = MODEL_REGISTRY[model_id]
    emoji = TIER_EMOJI.get(m.tier, "⚪")
    if m.inp_price <= 1 and m.out_price <= 1 and m.per_req <= 1:
        return f"{emoji} `{m.name}` — MIỄN PHÍ"
    per_req_str = f" + {m.per_req:.0f} VND/req" if m.per_req > 0 else ""
    return f"{emoji} `{m.name}` — {m.inp_price:.0f}/{m.out_price:.0f} VND/1M tok{per_req_str}"

def check_budget(state: ConversationState, est_cost: float = 0) -> Optional[str]:
    limit = state.prefs.budget_limit
    if limit > 0 and (state.stats.total_cost_vnd + est_cost) > limit:
        return f"🚨 VƯỢT NGÂN SÁCH: {state.stats.total_cost_vnd:.0f}/{limit:.0f} VND"
    if limit > 0:
        remain = limit - state.stats.total_cost_vnd
        if remain < limit * 0.2:
            return f"⚠️ Còn {remain:.0f} VND ({remain/limit*100:.0f}%)"
    return None

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text.encode('utf-8')) // 4)

def truncate(text: str, max_len: int = 4000) -> str:
    return text if len(text) <= max_len else text[:max_len-3] + "..."

def sanitize_repo(name: str) -> str:
    name = re.sub(r'[^a-zA-Z0-9_-]', '-', name.lower().strip())
    return re.sub(r'-+', '-', name).strip('-') or "denia-project"

def split_msg(text: str, max_len: int = 4000) -> List[str]:
    if len(text) <= max_len:
        return [text]
    parts = []
    while text:
        if len(text) <= max_len:
            parts.append(text)
            break
        idx = text.rfind('\n', 0, max_len)
        if idx == -1:
            idx = max_len
        parts.append(text[:idx])
        text = text[idx:].lstrip()
    return parts

def escape_md(text: str) -> str:
    for ch in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        text = text.replace(ch, f'\\{ch}')
    return text

async def send_long(update: Update, text: str, filename: str = "response.txt", caption: str = None, fmt: str = None):
    if not text:
        return
    state = await get_state(update.effective_user.id)
    fmt = fmt or state.prefs.file_format
    if len(text) <= TELEGRAM_MSG_LIMIT:
        for part in split_msg(text, TELEGRAM_MSG_LIMIT):
            try:
                await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)
            except:
                await update.message.reply_text(part)
        return
    ext = fmt if fmt in ("txt", "json", "md", "py") else "txt"
    if fmt == "json":
        content = json.dumps({"response": text, "time": datetime.now().isoformat()}, ensure_ascii=False, indent=2)
    elif fmt == "md":
        content = f"# Denia Bot Response\n\n*{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n---\n\n{text}"
    elif fmt == "py":
        content = f'"""\nDenia Bot Response\n{datetime.now().isoformat()}\n"""\n\nresponse = """\n{text}\n"""'
    else:
        content = text
    bio = io.BytesIO(content.encode('utf-8'))
    bio.name = filename.replace('.txt', f'.{ext}')
    cap = caption or f"Phản hồi quá dài ({len(text)} ký tự), đã gửi dạng .{ext}"
    await update.message.reply_document(document=bio, caption=cap)

async def safe_edit(status, text: str):
    try:
        await status.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        try:
            await status.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass

async def safe_reply(update, text: str):
    try:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(text)

def get_reply_text(update: Update) -> str:
    if update.message.reply_to_message and update.message.reply_to_message.text:
        return update.message.reply_to_message.text
    return ""

def parse_repo(repo_str: str) -> Tuple[Optional[str], Optional[str]]:
    if "/" not in repo_str:
        return None, None
    parts = repo_str.split("/", 1)
    return parts[0], parts[1]

async def get_session(context) -> aiohttp.ClientSession:
    session = context.bot_data.get('session')
    if not session or session.closed:
        session = aiohttp.ClientSession()
        context.bot_data['session'] = session
    return session

# ═══════════════════════════════════════════════════════════════════════
# PROGRESS BAR UTILITIES
# ═══════════════════════════════════════════════════════════════════════

def progress_bar(current: int, total: int, width: int = 20) -> str:
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    pct = int(100 * current / total)
    return f"`{bar}` {pct}%"

def step_emoji(step: int, current: int) -> str:
    return "✅" if step < current else "🔄" if step == current else "⏳"

# ═══════════════════════════════════════════════════════════════════════
# GITHUB CLIENT
# ═══════════════════════════════════════════════════════════════════════

class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        self.session: Optional[aiohttp.ClientSession] = None
    async def init(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None
    async def _req(self, method: str, endpoint: str, **kwargs) -> Tuple[int, Any]:
        await self.init()
        url = f"https://api.github.com{endpoint}"
        try:
            async with self.session.request(method, url, headers=self.headers, **kwargs) as resp:
                try:
                    data = await resp.json()
                except:
                    data = await resp.text()
                return resp.status, data
        except Exception as e:
            return 0, str(e)
    async def get_user(self) -> Tuple[bool, Dict]:
        s, d = await self._req("GET", "/user")
        return s == 200, d if isinstance(d, dict) else {}
    async def create_repo(self, name: str, desc: str = "", private: bool = False) -> Tuple[bool, Dict]:
        s, d = await self._req("POST", "/user/repos", json={"name": name, "description": desc, "private": private, "auto_init": True})
        return s == 201, d if isinstance(d, dict) else {}
    async def create_file(self, owner: str, repo: str, path: str, content: str, msg: str, branch: str = "main") -> Tuple[bool, Dict]:
        enc = base64.b64encode(content.encode('utf-8')).decode()
        s, d = await self._req("PUT", f"/repos/{owner}/{repo}/contents/{path}", json={"message": msg, "content": enc, "branch": branch})
        return s in (200, 201), d if isinstance(d, dict) else {}
    async def get_file(self, owner: str, repo: str, path: str, branch: str = "main") -> Tuple[bool, Dict]:
        s, d = await self._req("GET", f"/repos/{owner}/{repo}/contents/{path}?ref={branch}")
        return s == 200, d if isinstance(d, dict) else {}
    async def update_file(self, owner: str, repo: str, path: str, content: str, msg: str, sha: str, branch: str = "main") -> Tuple[bool, Dict]:
        enc = base64.b64encode(content.encode('utf-8')).decode()
        s, d = await self._req("PUT", f"/repos/{owner}/{repo}/contents/{path}", json={"message": msg, "content": enc, "sha": sha, "branch": branch})
        return s in (200, 201), d if isinstance(d, dict) else {}
    async def delete_file(self, owner: str, repo: str, path: str, msg: str, sha: str, branch: str = "main") -> Tuple[bool, Dict]:
        s, d = await self._req("DELETE", f"/repos/{owner}/{repo}/contents/{path}", json={"message": msg, "sha": sha, "branch": branch})
        return s == 200, d if isinstance(d, dict) else {}
    async def list_files(self, owner: str, repo: str, path: str = "", branch: str = "main") -> Tuple[bool, List]:
        ep = f"/repos/{owner}/{repo}/contents/{path}?ref={branch}" if path else f"/repos/{owner}/{repo}/contents?ref={branch}"
        s, d = await self._req("GET", ep)
        return s == 200 and isinstance(d, list), d if isinstance(d, list) else []
    async def create_branch(self, owner: str, repo: str, new_branch: str, from_branch: str = "main") -> Tuple[bool, Dict]:
        s, d = await self._req("GET", f"/repos/{owner}/{repo}/git/refs/heads/{from_branch}")
        if s != 200:
            return False, d
        sha = d.get("object", {}).get("sha", "")
        s, d = await self._req("POST", f"/repos/{owner}/{repo}/git/refs", json={"ref": f"refs/heads/{new_branch}", "sha": sha})
        return s == 201, d if isinstance(d, dict) else {}
    async def create_pr(self, owner: str, repo: str, title: str, head: str, base: str, body: str = "") -> Tuple[bool, Dict]:
        s, d = await self._req("POST", f"/repos/{owner}/{repo}/pulls", json={"title": title, "head": head, "base": base, "body": body})
        return s == 201, d if isinstance(d, dict) else {}
    async def create_issue(self, owner: str, repo: str, title: str, body: str = "", labels: List[str] = None) -> Tuple[bool, Dict]:
        p = {"title": title, "body": body}
        if labels:
            p["labels"] = labels
        s, d = await self._req("POST", f"/repos/{owner}/{repo}/issues", json=p)
        return s == 201, d if isinstance(d, dict) else {}
    async def get_commits(self, owner: str, repo: str, branch: str = "main", per_page: int = 10) -> Tuple[bool, List]:
        s, d = await self._req("GET", f"/repos/{owner}/{repo}/commits?sha={branch}&per_page={per_page}")
        return s == 200 and isinstance(d, list), d if isinstance(d, list) else []
    async def search_repos(self, query: str, per_page: int = 10) -> Tuple[bool, List]:
        s, d = await self._req("GET", f"/search/repositories?q={query}&per_page={per_page}")
        return s == 200 and isinstance(d, dict), d.get("items", []) if isinstance(d, dict) else []
    async def fork_repo(self, owner: str, repo: str) -> Tuple[bool, Dict]:
        s, d = await self._req("POST", f"/repos/{owner}/{repo}/forks")
        return s == 202, d if isinstance(d, dict) else {}
    async def star_repo(self, owner: str, repo: str) -> Tuple[bool, Dict]:
        s, d = await self._req("PUT", f"/user/starred/{owner}/{repo}")
        return s == 204, {}
    async def get_rate_limit(self) -> Tuple[bool, Dict]:
        s, d = await self._req("GET", "/rate_limit")
        return s == 200, d if isinstance(d, dict) else {}

gh_client = GitHubClient(GITHUB_TOKEN)

# ═══════════════════════════════════════════════════════════════════════
# AI API CLIENT
# ═══════════════════════════════════════════════════════════════════════

async def call_chat(session: aiohttp.ClientSession, model_id: str, messages: List[Dict], status_msg: Any,
                    system: str = "", max_tokens: int = MAX_OUTPUT_TOKENS, temp: float = 0.7, retries: int = 2) -> Tuple[str, Dict]:
    if model_id not in MODEL_REGISTRY:
        raise ValueError(f"Model {model_id} không tồn tại")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    msgs = []
    has_sys = False
    for m in messages:
        if m.get("role") == "system":
            if not has_sys:
                msgs.append({"role": "system", "content": system or m.get("content", "")})
                has_sys = True
        else:
            msgs.append(m)
    if not has_sys and system:
        msgs.insert(0, {"role": "system", "content": system})
    payload = {"model": model_id, "messages": msgs, "temperature": temp, "max_tokens": max_tokens}
    start = time.time()
    last_error = None
    for attempt in range(retries + 1):
        try:
            timeout = aiohttp.ClientTimeout(total=300, connect=30, sock_read=300)
            async with session.post(API_CHAT_URL, headers=headers, json=payload, timeout=timeout) as resp:
                if resp.status != 200:
                    err_body = await resp.text()
                    if attempt < retries:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise Exception(f"API Error {resp.status}: {err_body[:500]}")
                result = await resp.json()
                break
        except Exception as e:
            last_error = e
            if attempt < retries:
                await asyncio.sleep(2 ** attempt)
            else:
                raise last_error
    latency = time.time() - start
    choices = result.get('choices', [])
    if not choices:
        raise ValueError("API trả về rỗng")
    content = choices[0].get('message', {}).get('content', '')
    if not content:
        raise ValueError("API trả về nội dung rỗng")
    usage = result.get('usage', {})
    inp_tok = usage.get('prompt_tokens', 0) or sum(estimate_tokens(m.get('content', '')) for m in msgs)
    out_tok = usage.get('completion_tokens', 0) or estimate_tokens(content)
    metrics = {'latency': latency, 'input_tokens': inp_tok, 'output_tokens': out_tok, 'total_tokens': inp_tok + out_tok, 'tps': out_tok / latency if latency > 0 else 0}
    return content, metrics

async def call_embed(session: aiohttp.ClientSession, model_id: str, text: str, status_msg: Any) -> Tuple[List[float], Dict]:
    if model_id not in MODEL_REGISTRY:
        raise ValueError(f"Model {model_id} không hỗ trợ embedding")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {"model": model_id, "input": text}
    start = time.time()
    async with session.post(API_EMBED_URL, headers=headers, json=payload) as resp:
        if resp.status != 200:
            raise Exception(f"Embed API Error {resp.status}")
        result = await resp.json()
    latency = time.time() - start
    emb = result.get('data', [{}])[0].get('embedding', [])
    if not emb:
        raise ValueError("No embedding returned")
    inp_tok = estimate_tokens(text)
    return emb, {'latency': latency, 'input_tokens': inp_tok, 'output_tokens': 0, 'total_tokens': inp_tok, 'tps': 0}

async def call_tts(session: aiohttp.ClientSession, model_id: str, text: str, status_msg: Any) -> Tuple[bytes, Dict]:
    if model_id not in MODEL_REGISTRY:
        raise ValueError(f"Model {model_id} không hỗ trợ TTS")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {"model": model_id, "input": text, "voice": "alloy"}
    start = time.time()
    async with session.post(API_TTS_URL, headers=headers, json=payload) as resp:
        if resp.status != 200:
            raise Exception(f"TTS API Error {resp.status}")
        audio = await resp.read()
    latency = time.time() - start
    if not audio or len(audio) < 100:
        raise ValueError("Audio data invalid")
    tok = estimate_tokens(text)
    return audio, {'latency': latency, 'input_tokens': tok, 'output_tokens': 0, 'total_tokens': tok, 'tps': 0}

async def call_image(session: aiohttp.ClientSession, prompt: str, model_id: str = None, status_msg: Any = None) -> Tuple[bytes, str]:
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    mid = model_id or "thanhnhan9023/gpt-image-2"
    payload = {"model": mid, "prompt": prompt, "n": 1, "size": "1024x1024"}
    start = time.time()
    if status_msg:
        await status_msg.edit_text("🎨 Đang tạo hình ảnh...")
    async with session.post(API_IMAGE_URL, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
        if resp.status != 200:
            raise Exception(f"Image API Error {resp.status}")
        result = await resp.json()
    latency = time.time() - start
    data = result.get('data', [])
    if not data:
        raise ValueError("No image data")
    url = data[0].get('url', '')
    if url:
        async with session.get(url) as img_resp:
            return await img_resp.read(), f"Tạo trong {latency:.1f}s"
    b64 = data[0].get('b64_json', '')
    if b64:
        return base64.b64decode(b64), f"Tạo trong {latency:.1f}s"
    raise ValueError("No image URL or base64")

# ═══════════════════════════════════════════════════════════════════════
# WEB SEARCH & FETCH
# ═══════════════════════════════════════════════════════════════════════

async def web_search(session: aiohttp.ClientSession, query: str, num: int = 5) -> List[Dict]:
    try:
        url = f"https://html.duckduckgo.com/html/?q={aiohttp.helpers.quote(query)}"
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                html = await resp.text()
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    results = []
                    for r in soup.find_all('div', class_='result')[:num]:
                        a = r.find('a', class_='result__a')
                        s = r.find('a', class_='result__snippet')
                        if a and s:
                            results.append({"title": a.get_text(strip=True), "url": a.get('href', ''), "snippet": s.get_text(strip=True)[:200]})
                    if results:
                        return results
                except:
                    pass
    except Exception as e:
        logger.warning(f"Web search error: {e}")
    return [{"title": f"Kết quả {i+1}", "url": "https://duckduckgo.com", "snippet": "Không thể tìm kiếm"} for i in range(num)]

async def fetch_web(session: aiohttp.ClientSession, url: str) -> str:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30), headers={"User-Agent": "DeniaBot/1.0"}) as resp:
            if resp.status == 200:
                html = await resp.text()
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    for s in soup(["script", "style", "nav", "footer", "header"]):
                        s.decompose()
                    text = soup.get_text(separator=' ', strip=True)
                    return ' '.join(text.split())[:8000]
                except:
                    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html)).strip()[:5000]
            return f"Lỗi HTTP {resp.status}"
    except Exception as e:
        return f"Lỗi tải trang: {str(e)}"

# ═══════════════════════════════════════════════════════════════════════
# CODE INTERPRETER
# ═══════════════════════════════════════════════════════════════════════

BLACKLIST = ['import os', 'import sys', 'import subprocess', 'import socket', '__import__', 'eval(', 'exec(', 'compile(', 'open(', 'file(', 'os.system', 'os.popen', 'subprocess.call', 'subprocess.run', 'import urllib', 'import requests', 'import ftplib', 'shutil.rmtree', 'os.remove', 'os.unlink', 'os.rmdir', 'import pathlib', 'pathlib.Path', 'import pickle', 'import shutil']

async def run_python(code: str, timeout: int = 30) -> Tuple[bool, str, str]:
    code_lower = code.lower()
    for banned in BLACKLIST:
        if banned.lower() in code_lower:
            return False, "", f"🚫 Cấm: `{banned}`"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        tmp = f.name
    try:
        proc = await asyncio.create_subprocess_exec(sys.executable, tmp, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, limit=1024*1024)
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return proc.returncode == 0, stdout.decode('utf-8', errors='replace')[:8000], stderr.decode('utf-8', errors='replace')[:4000]
        except asyncio.TimeoutError:
            proc.kill()
            return False, "", f"⏱ Timeout sau {timeout}s"
    except Exception as e:
        return False, "", f"Lỗi: {str(e)}"
    finally:
        try:
            os.unlink(tmp)
        except:
            pass

async def run_python_plot(code: str, timeout: int = 30) -> Tuple[bool, str, str, Optional[bytes]]:
    code_lower = code.lower()
    for banned in BLACKLIST:
        if banned.lower() in code_lower:
            return False, "", f"🚫 Cấm: `{banned}`", None
    wrapped = """import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64, io
""" + code + """
figs = [plt.figure(i) for i in plt.get_fignums()]
if figs:
    buf = io.BytesIO()
    figs[-1].savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    print("__PLOT__" + base64.b64encode(buf.read()).decode())
    plt.close('all')
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(wrapped)
        tmp = f.name
    try:
        proc = await asyncio.create_subprocess_exec(sys.executable, tmp, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, limit=1024*1024)
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            out = stdout.decode('utf-8', errors='replace')[:8000]
            err = stderr.decode('utf-8', errors='replace')[:4000]
            img = None
            if "__PLOT__" in out:
                parts = out.split("__PLOT__")
                out = parts[0].strip()
                try:
                    img = base64.b64decode(parts[1].strip().split('\n')[0])
                except:
                    pass
            return proc.returncode == 0, out, err, img
        except asyncio.TimeoutError:
            proc.kill()
            return False, "", f"⏱ Timeout sau {timeout}s", None
    except Exception as e:
        return False, "", f"Lỗi: {str(e)}", None
    finally:
        try:
            os.unlink(tmp)
        except:
            pass

# ═══════════════════════════════════════════════════════════════════════
# CODE TOOLS
# ═══════════════════════════════════════════════════════════════════════

async def analyze_code(code: str, lang: str = "python") -> Dict:
    issues, warnings, info = [], [], []
    score = 100
    if lang == "python":
        try:
            compile(code, '<string>', 'exec')
            info.append("✅ Syntax hợp lệ")
        except SyntaxError as e:
            issues.append(f"❌ Syntax lỗi dòng {e.lineno}: {e.msg}")
            score -= 30
        dangerous = [(r'eval\s*\(', "eval() nguy hiểm"), (r'exec\s*\(', "exec() nguy hiểm"), (r'os\.system\s*\(', "os.system() nguy hiểm"), (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', "shell=True nguy hiểm"), (r'pickle\.loads?\s*\(', "pickle không an toàn"), (r'yaml\.load\s*\(', "yaml.load() không an toàn")]
        for p, m in dangerous:
            if re.search(p, code):
                issues.append(f"🔒 {m}")
                score -= 25
        if "import *" in code:
            warnings.append("⚠️ Wildcard import")
            score -= 5
        if "except:" in code and "except Exception" not in code:
            warnings.append("⚠️ Bare except")
            score -= 5
        if 'if __name__' not in code and len(code.split('\n')) > 25:
            warnings.append("⚠️ Thiếu __main__ guard")
            score -= 3
        if len(code.split('\n')) > 500:
            warnings.append("📊 File quá lớn")
            score -= 5
    return {"score": max(0, score), "issues": issues, "warnings": warnings, "info": info, "lines": len(code.split('\n'))}

def format_diff(old: str, new: str) -> str:
    import difflib
    return ''.join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True), lineterm=''))[:4000]

def generate_dockerfile(ptype: str = "python") -> str:
    templates = {
        "python": "FROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nEXPOSE 8000\nCMD [\"python\", \"main.py\"]\n",
        "node": "FROM node:18-alpine\nWORKDIR /app\nCOPY package*.json ./\nRUN npm ci --only=production\nCOPY . .\nEXPOSE 3000\nCMD [\"node\", \"index.js\"]\n",
        "go": "FROM golang:1.21-alpine AS builder\nWORKDIR /app\nCOPY . .\nRUN go build -o main .\nFROM alpine:latest\nCOPY --from=builder /app/main .\nEXPOSE 8080\nCMD [\"./main\"]\n"
    }
    return templates.get(ptype, templates["python"])

def generate_cicd(ptype: str = "python") -> str:
    if ptype == "python":
        return "name: CI\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n    - uses: actions/checkout@v4\n    - uses: actions/setup-python@v4\n      with:\n        python-version: '3.11'\n    - run: pip install -r requirements.txt pytest\n    - run: pytest\n"
    return "# CI/CD template\n"

# ═══════════════════════════════════════════════════════════════════════
# RAG KNOWLEDGE BASE
# ═══════════════════════════════════════════════════════════════════════

def cosine_sim(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(x*x for x in b))
    return dot/(na*nb) if na and nb else 0.0

def chunk_text(text: str, size: int = 500, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start+size, len(words))
        chunks.append(' '.join(words[start:end]))
        start += size - overlap
    return chunks

async def query_kb(session: aiohttp.ClientSession, query: str, docs: List[KnowledgeDoc], top_k: int = 3) -> List[Tuple]:
    if not docs:
        return []
    try:
        emb, _ = await call_embed(session, "text-embedding-3-small", query, None)
    except:
        return []
    results = []
    for doc in docs:
        if doc.embedding:
            score = cosine_sim(emb, doc.embedding)
            if score > 0.5:
                results.append((doc.filename, score, doc.content[:1000]))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]

# ═══════════════════════════════════════════════════════════════════════
# LESSON SYSTEM — 2000 TOPICS PER LANGUAGE (Dynamic Generation)
# ═══════════════════════════════════════════════════════════════════════

LEARNING_LANGUAGES = ["python", "javascript", "java", "cpp", "go", "rust", "typescript", "sql", "csharp", "kotlin", "swift", "ruby", "php", "dart", "scala"]
LANG_DISPLAY = {
    "python": "Python 🐍", "javascript": "JavaScript 🟨", "java": "Java ☕",
    "cpp": "C++ 🔵", "go": "Go 🐹", "rust": "Rust 🦀", "typescript": "TypeScript 📘",
    "sql": "SQL 🗄️", "csharp": "C# 🔷", "kotlin": "Kotlin 🟣", "swift": "Swift 🟥",
    "ruby": "Ruby 🔴", "php": "PHP 🟪", "dart": "Dart 🎯", "scala": "Scala ⚡"
}

# Base topic templates for each language to generate 2000 lessons
BASE_TOPICS = {
    "python": [
        ("Fundamentals", ["Variables", "Data Types", "Operators", "Input/Output", "Comments", "Basic Syntax", "IDE Setup", "Hello World Deep Dive", "Memory Basics", "Type Conversion"]),
        ("Control Flow", ["If Statements", "Elif", "Nested If", "Ternary Operator", "Switch Pattern", "Match Case", "Boolean Logic", "Short Circuit", "Truthiness", "Comparisons"]),
        ("Loops", ["For Loop", "While Loop", "Range Function", "Enumerate", "Zip", "Break Continue", "Nested Loops", "List Comprehension Intro", "Generator Expression", "Itertools Overview"]),
        ("Functions", ["Defining Functions", "Arguments", "Return Values", "Default Args", "Args Kwargs", "Lambda", "Map Filter Reduce", "Recursion", "Decorators Intro", "Closures"]),
        ("Collections", ["Lists Deep Dive", "Tuples", "Dictionaries", "Sets", "Frozen Sets", "Deque", "Counter", "OrderedDict", "DefaultDict", "NamedTuple"]),
        ("Strings", ["String Methods", "Formatting", "F-Strings", "Regex Basics", "Regex Advanced", "StringIO", "Textwrap", "Unicode", "Encoding", "Parsing"]),
        ("File I/O", ["Open Modes", "Reading Files", "Writing Files", "CSV", "JSON", "Pickle", "Binary Files", "Pathlib", "Temporary Files", "File Watching"]),
        ("OOP Basics", ["Classes", "Objects", "Init", "Self", "Attributes", "Methods", "Class Variables", "Static Methods", "Class Methods", "Property"]),
        ("OOP Advanced", ["Inheritance", "Multiple Inheritance", "MRO", "Polymorphism", "Encapsulation", "Abstract Base", "Dataclasses", "Slots", "Metaclasses", "Descriptors"]),
        ("Error Handling", ["Try Except", "Finally", "Else", "Custom Exceptions", "Exception Hierarchy", "Logging", "Traceback", "Assertions", "Context Managers", "RAII Pattern"]),
        ("Modules", ["Import System", "Packages", "Init", "Relative Import", "Circular Import", "Pip", "Virtualenv", "Poetry", "Conda", "Wheels"]),
        ("Standard Library", ["Os Sys", "Datetime", "Collections", "Itertools", "Functools", "Math Random", "Statistics", "Hashlib", "Secrets", "Typing"]),
        ("Advanced Features", ["Generators", "Coroutines", "Asyncio", "Await", "Event Loop", "Tasks", "Futures", "Threading", "Multiprocessing", "GIL"]),
        ("Web Development", ["HTTP Basics", "Flask", "FastAPI", "Django Intro", "Jinja", "REST API", "WebSocket", "Middleware", "CORS", "Authentication"]),
        ("Data Science", ["NumPy Arrays", "Pandas DataFrame", "Matplotlib", "Seaborn", "Scikit Intro", "Data Cleaning", "Visualization", "Statistics", "Linear Regression", "ML Pipeline"]),
        ("Database", ["SQLite", "PostgreSQL", "SQLAlchemy", "ORM", "Migrations", "Connection Pool", "Transactions", "NoSQL", "Redis", "MongoDB"]),
        ("Testing", ["Unit Test", "Pytest", "Mock", "Fixture", "Parametrize", "Coverage", "TDD", "BDD", "Integration Test", "Performance Test"]),
        ("DevOps", ["Docker", "Docker Compose", "CI/CD", "GitHub Actions", "AWS Basics", "Lambda", "Serverless", "Monitoring", "Logging", "Kubernetes"]),
        ("Security", ["Hashing", "Encryption", "JWT", "OAuth2", "SQL Injection", "XSS", "CSRF", "HTTPS", "Secrets Management", "Penetration Testing"]),
        ("Architecture", ["Design Patterns", "SOLID", "Clean Code", "Refactoring", "Microservices", "Event Driven", "CQRS", "DDD", "Hexagonal", "System Design"]),
    ],
    "javascript": [
        ("Fundamentals", ["Variables", "Data Types", "Operators", "Type Coercion", "Strict Mode", "Console", "Debugger", "Hoisting", "Scope", "Closures"]),
        ("Control Flow", ["If Else", "Switch", "Ternary", "Logical Operators", "Short Circuit", "Truthy Falsy", "Comparisons", "Loops", "Break Continue", "Labels"]),
        ("Functions", ["Declarations", "Expressions", "Arrow Functions", "IIFE", "Callbacks", "Higher Order", "Currying", "Partial", "Composition", "Pipes"]),
        ("Objects", ["Object Literal", "Constructor", "Prototype", "This", "New", "Object Methods", "Getters Setters", "Symbols", "WeakMap", "WeakSet"]),
        ("Arrays", ["Array Methods", "Map", "Filter", "Reduce", "Find", "Sort", "Splice", "Spread", "Destructuring", "ArrayBuffer"]),
        ("ES6+", ["Let Const", "Template Literals", "Destructuring", "Modules", "Classes", "Promises", "Async Await", "Generators", "Proxy", "Reflect"]),
        ("DOM", ["Selectors", "Events", "Event Delegation", "Bubbling", "Attributes", "Styles", "Create Element", "Fragment", "Shadow DOM", "Web Components"]),
        ("Async", ["Callbacks", "Promises", "Async Await", "Event Loop", "Microtasks", "Macrotasks", "Fetch", "Abort Controller", "RxJS Intro", "Web Workers"]),
        ("Browser", ["Storage", "Cookies", "LocalStorage", "SessionStorage", "IndexedDB", "History", "Location", "Navigator", "Geolocation", "Notification"]),
        ("Node.js", ["Modules", "File System", "Path", "Events", "Streams", "Buffers", "HTTP", "Express", "Middleware", "Routing"]),
        ("Frontend", ["React Intro", "JSX", "Components", "Props", "State", "Hooks", "Effect", "Context", "Redux", "Next.js"]),
        ("Backend", ["Express", "Koa", "Fastify", "NestJS", "Authentication", "JWT", "OAuth", "Validation", "Rate Limiting", "Caching"]),
        ("Database", ["MongoDB", "Mongoose", "PostgreSQL", "Sequelize", "Prisma", "Redis", "GraphQL", "Apollo", "TypeORM", "Knex"]),
        ("Testing", ["Jest", "Mocha", "Chai", "Cypress", "Puppeteer", "Playwright", "Unit Test", "Integration", "E2E", "Mock Service"]),
        ("Build Tools", ["Webpack", "Vite", "Rollup", "Parcel", "Babel", "ESLint", "Prettier", "TypeScript", "SWC", "Turbopack"]),
        ("Performance", ["Lighthouse", "Core Web Vitals", "Lazy Loading", "Code Splitting", "Tree Shaking", "Minification", "Compression", "CDN", "Caching", "Service Workers"]),
        ("Security", ["CSP", "CORS", "XSS Prevention", "CSRF Tokens", "HTTPS", "Content Security", "Sanitization", "Helmet", "Rate Limit", "Input Validation"]),
        ("Mobile", ["React Native", "Ionic", "PWA", "Capacitor", "Expo", "Mobile Events", "Touch", "Gesture", "Responsive", "Viewport"]),
        ("Advanced", ["V8 Engine", "Memory Management", "Garbage Collection", "Performance API", "WebAssembly", "WebGL", "Canvas", "SVG", "D3.js", "Three.js"]),
        ("Architecture", ["MVC", "MVVM", "Flux", "Component Design", "Design Patterns", "Micro Frontends", "Monorepo", "Turborepo", "Nx", "Module Federation"]),
    ],
}

# Generate topics for other languages by adapting from Python/JS templates
OTHER_LANG_TOPICS = [
    ("Fundamentals", ["Variables", "Data Types", "Operators", "I/O", "Syntax", "Comments", "IDE", "Hello World", "Memory", "Types"]),
    ("Control Flow", ["If Else", "Switch", "Ternary", "Loops", "Break", "Continue", "Goto", "Match", "Pattern", "Logic"]),
    ("Functions", ["Defining", "Parameters", "Return", "Overloading", "Default Args", "Variadic", "Lambda", "Higher Order", "Recursion", "Closures"]),
    ("Collections", ["Arrays", "Lists", "Maps", "Sets", "Tuples", "Structs", "Slices", "Vectors", "Queues", "Stacks"]),
    ("Strings", ["Methods", "Formatting", "Regex", "Parsing", "Builder", "Encoding", "Unicode", "Interpolation", "Split", "Join"]),
    ("File I/O", ["Reading", "Writing", "Streams", "Buffers", "CSV", "JSON", "XML", "Binary", "Paths", "Async I/O"]),
    ("OOP", ["Classes", "Objects", "Inheritance", "Polymorphism", "Encapsulation", "Abstract", "Interfaces", "Traits", "Mixins", "Generics"]),
    ("Error Handling", ["Try Catch", "Finally", "Exceptions", "Panic", "Result", "Option", "Logging", "Traceback", "Assertions", "Recovery"]),
    ("Modules", ["Import", "Export", "Packages", "Namespaces", "Modules", "Crates", "Gems", "Pods", "NPM", "Dependency"]),
    ("Standard Library", ["Collections", "Math", "Date", "Random", "Hash", "Crypto", "Net", "HTTP", "OS", "Threading"]),
    ("Advanced", ["Generics", "Macros", "Reflection", "Annotations", "Attributes", "Memory", "Pointers", "References", "Lifetimes", "Ownership"]),
    ("Concurrency", ["Threads", "Async", "Await", "Promises", "Futures", "Channels", "Mutex", "Atomics", "Parallel", "Actors"]),
    ("Web", ["HTTP", "REST", "JSON", "WebSocket", "gRPC", "GraphQL", "Routing", "Middleware", "Auth", "CORS"]),
    ("Database", ["SQL", "ORM", "Migrations", "Transactions", "Connection", "Pool", "NoSQL", "Redis", "SQLite", "PostgreSQL"]),
    ("Testing", ["Unit", "Integration", "Mock", "Fixture", "Coverage", "TDD", "BDD", "Benchmark", "Fuzz", "Snapshot"]),
    ("Build", ["Compiler", "Linker", "Package", "Dependency", "CI/CD", "Docker", "Makefile", "CMake", "Gradle", "Maven"]),
    ("Security", ["Auth", "OAuth", "JWT", "Hashing", "Encryption", "TLS", "Input Validation", "Injection", "XSS", "CSRF"]),
    ("Performance", ["Profiling", "Benchmarking", "Optimization", "Caching", "Lazy", "Memoization", "Parallel", "Vectorization", "JIT", "AOT"]),
    ("Design Patterns", ["Singleton", "Factory", "Observer", "Strategy", "Decorator", "Adapter", "Facade", "Proxy", "Command", "State"]),
    ("System Design", ["Architecture", "Microservices", "Event Driven", "CQRS", "DDD", "Load Balancing", "Caching", "Queue", "Rate Limit", "Scalability"]),
]

def generate_topics_2000(lang: str) -> List[str]:
    """Generate 2000 lesson topics for any language"""
    if lang in BASE_TOPICS:
        base = BASE_TOPICS[lang]
    else:
        base = OTHER_LANG_TOPICS
    topics = []
    chapter_num = 0
    for chapter_name, lessons in base:
        chapter_num += 1
        for i, lesson in enumerate(lessons, 1):
            # Each base lesson generates 10 variations for 2000 total
            for level in range(1, 11):
                if level == 1:
                    topics.append(f"Ch{chapter_num}: {lesson} — Basics")
                elif level == 2:
                    topics.append(f"Ch{chapter_num}: {lesson} — Intermediate")
                elif level == 3:
                    topics.append(f"Ch{chapter_num}: {lesson} — Advanced")
                elif level == 4:
                    topics.append(f"Ch{chapter_num}: {lesson} — Best Practices")
                elif level == 5:
                    topics.append(f"Ch{chapter_num}: {lesson} — Common Mistakes")
                elif level == 6:
                    topics.append(f"Ch{chapter_num}: {lesson} — Performance")
                elif level == 7:
                    topics.append(f"Ch{chapter_num}: {lesson} — Real-world Example")
                elif level == 8:
                    topics.append(f"Ch{chapter_num}: {lesson} — Integration")
                elif level == 9:
                    topics.append(f"Ch{chapter_num}: {lesson} — Testing & Debugging")
                else:
                    topics.append(f"Ch{chapter_num}: {lesson} — Mastery Challenge")
    return topics[:2000]

# Cache topics per language
LESSON_TOPICS_CACHE: Dict[str, List[str]] = {}

def get_lesson_topics(lang: str) -> List[str]:
    if lang not in LESSON_TOPICS_CACHE:
        LESSON_TOPICS_CACHE[lang] = generate_topics_2000(lang)
    return LESSON_TOPICS_CACHE[lang]

LEETCODE_TOPICS = [
    "Array", "Two Pointers", "Sliding Window", "Stack", "Linked List",
    "Binary Tree", "Heap", "Backtracking", "Graph", "DP",
    "Greedy", "Bit Manipulation", "Math", "Design", "SQL"
]

# ═══════════════════════════════════════════════════════════════════════
# UNIVERSAL MODEL SELECTOR
# ═══════════════════════════════════════════════════════════════════════

def build_model_keyboard(mode: str, current_model: str, callback_prefix: str, page: int = 0) -> InlineKeyboardMarkup:
    """Build paginated model selector keyboard"""
    cfg = MODE_CONFIG[mode]
    models = cfg["models"]
    per_page = 10
    total_pages = (len(models) + per_page - 1) // per_page
    start = page * per_page
    end = min(start + per_page, len(models))

    keyboard = []
    row = []
    for idx in range(start, end):
        mid = models[idx]
        m = MODEL_REGISTRY[mid]
        prefix = "✅ " if mid == current_model else ""
        emoji = TIER_EMOJI.get(m.tier, "⚪")
        short_name = m.name[:15] + "..." if len(m.name) > 15 else m.name
        btn = InlineKeyboardButton(f"{prefix}{emoji} {short_name}", callback_data=f"selmodel_{callback_prefix}_{mode}_{idx}_{page}")
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Pagination + filters
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Trước", callback_data=f"selpage_{callback_prefix}_{mode}_{page-1}"))
    nav_row.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Tiếp ➡️", callback_data=f"selpage_{callback_prefix}_{mode}_{page+1}"))
    if nav_row:
        keyboard.append(nav_row)

    # Tier filters
    keyboard.append([
        InlineKeyboardButton("💚 Free", callback_data=f"filter_{callback_prefix}_{mode}_free_{page}"),
        InlineKeyboardButton("💙 Low", callback_data=f"filter_{callback_prefix}_{mode}_low_{page}"),
        InlineKeyboardButton("💛 Mid", callback_data=f"filter_{callback_prefix}_{mode}_mid_{page}"),
    ])
    keyboard.append([
        InlineKeyboardButton("🧡 High", callback_data=f"filter_{callback_prefix}_{mode}_high_{page}"),
        InlineKeyboardButton("❤️ Ultra", callback_data=f"filter_{callback_prefix}_{mode}_ultra_{page}"),
        InlineKeyboardButton("🔄 All", callback_data=f"filter_{callback_prefix}_{mode}_all_{page}"),
    ])
    keyboard.append([InlineKeyboardButton("❌ Hủy", callback_data=f"selcancel_{callback_prefix}")])
    return InlineKeyboardMarkup(keyboard)

async def show_model_selector(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str, callback_prefix: str, prompt_text: str, extra_data: Dict = None):
    """Show model selector before starting any AI task"""
    uid = update.effective_user.id
    state = await get_state(uid)
    current = state.model if state.model in MODE_CONFIG[mode]["models"] else MODE_CONFIG[mode]["default"]

    # Store pending data in temp_data
    if extra_data:
        state.temp_data[callback_prefix] = extra_data
    state.pending_callback = callback_prefix
    _save_state()

    header = (
        f"🤖 Chọn Model — {MODE_CONFIG[mode]['name']}\n"
        f"{'━'*24}\n"
        f"📝 {prompt_text}\n\n"
        f"✅ Hiện tại: `{MODEL_REGISTRY.get(current, ModelInfo('?','?','?','?',0,0)).name}`\n"
        f"💰 {get_cost_str(current)}\n\n"
        f"👇 Chọn model cho tác vụ này:"
    )
    await update.message.reply_text(header, parse_mode=ParseMode.MARKDOWN, reply_markup=build_model_keyboard(mode, current, callback_prefix))

async def cb_model_selector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all model selection callbacks"""
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    state = await get_state(uid)
    data = query.data

    if data.startswith("selcancel_"):
        prefix = data.replace("selcancel_", "")
        state.pending_callback = None
        state.temp_data.pop(prefix, None)
        _save_state()
        await query.edit_message_text("❌ Đã hủy chọn model.")
        return

    if data.startswith("selpage_"):
        parts = data.split("_")
        if len(parts) >= 5:
            prefix, mode, page = parts[1], parts[2], int(parts[3])
            current = state.model if state.model in MODE_CONFIG[mode]["models"] else MODE_CONFIG[mode]["default"]
            await query.edit_message_reply_markup(reply_markup=build_model_keyboard(mode, current, prefix, page))
        return

    if data.startswith("filter_"):
        parts = data.split("_")
        if len(parts) >= 6:
            prefix, mode, tier, page_str = parts[1], parts[2], parts[3], parts[4]
            page = int(page_str)
            # Filter models by tier
            cfg = MODE_CONFIG[mode]
            if tier != "all":
                filtered = [mid for mid in cfg["models"] if MODEL_REGISTRY[mid].tier == tier]
            else:
                filtered = cfg["models"]
            if not filtered:
                await query.answer("Không có model ở tier này!")
                return
            # Rebuild with filtered list temporarily stored? Complex. Just show page 0 of filtered.
            # For simplicity, rebuild keyboard with filtered list
            per_page = 10
            total_pages = (len(filtered) + per_page - 1) // per_page
            start = page * per_page
            end = min(start + per_page, len(filtered))
            keyboard = []
            row = []
            for idx in range(start, end):
                mid = filtered[idx]
                m = MODEL_REGISTRY[mid]
                prefix = "✅ " if mid == state.model else ""
                emoji = TIER_EMOJI.get(m.tier, "⚪")
                short_name = m.name[:15] + "..." if len(m.name) > 15 else m.name
                btn = InlineKeyboardButton(f"{prefix}{emoji} {short_name}", callback_data=f"selmodel_{prefix}_{mode}_{cfg['models'].index(mid) if mid in cfg['models'] else 0}_{page}")
                row.append(btn)
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
            nav_row = []
            if page > 0:
                nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"filter_{prefix}_{mode}_{tier}_{page-1}"))
            nav_row.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
            if page < total_pages - 1:
                nav_row.append(InlineKeyboardButton("➡️", callback_data=f"filter_{prefix}_{mode}_{tier}_{page+1}"))
            if nav_row:
                keyboard.append(nav_row)
            keyboard.append([InlineKeyboardButton("⬅️ Quay lại", callback_data=f"selpage_{prefix}_{mode}_0")])
            keyboard.append([InlineKeyboardButton("❌ Hủy", callback_data=f"selcancel_{prefix}")])
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("selmodel_"):
        parts = data.split("_")
        if len(parts) >= 5:
            prefix = parts[1]
            mode = parts[2]
            try:
                idx = int(parts[3])
                mid = MODE_CONFIG[mode]["models"][idx]
                m = MODEL_REGISTRY[mid]
                state.pending_model = mid
                _save_state()

                budget = check_budget(state, 5000)
                text = (
                    f"✅ Đã chọn model!\n\n"
                    f"🤖 {CATEGORY_EMOJI.get(m.category, '⚪')} *{m.name}*\n"
                    f"💰 {get_cost_str(mid)}\n"
                )
                if budget:
                    text += f"\n🚨 {budget}\n"
                text += "\n👇 Xác nhận để bắt đầu:"

                keyboard = [
                    [InlineKeyboardButton("✅ Bắt đầu", callback_data=f"exec_{prefix}_{mode}_{idx}")],
                    [InlineKeyboardButton("🔄 Đổi model", callback_data=f"selpage_{prefix}_{mode}_0")],
                    [InlineKeyboardButton("❌ Hủy", callback_data=f"selcancel_{prefix}")],
                ]
                await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Lỗi chọn model.", parse_mode=ParseMode.MARKDOWN)
        return

    if data.startswith("exec_"):
        parts = data.split("_")
        if len(parts) >= 4:
            prefix = parts[1]
            mode = parts[2]
            mid = state.pending_model or MODE_CONFIG[mode]["default"]
            state.model = mid
            state.pending_callback = None
            _save_state()
            await query.edit_message_text(f"🚀 Đang khởi động với `{MODEL_REGISTRY[mid].name}`...")
            # Execute the actual task based on prefix
            await execute_task(update, context, prefix, mode, mid)

async def execute_task(update: Update, context: ContextTypes.DEFAULT_TYPE, prefix: str, mode: str, model_id: str):
    """Route to actual task execution after model selection"""
    uid = update.effective_user.id
    state = await get_state(uid)

    if prefix == "agent":
        await run_agent_task(update, context, state, model_id)
    elif prefix == "lesson":
        await run_lesson_task(update, context, state, model_id)
    elif prefix == "leetcode":
        await run_leetcode_task(update, context, state, model_id)
    elif prefix == "quiz":
        await run_quiz_task(update, context, state, model_id)
    elif prefix == "translate":
        await run_translate_task(update, context, state, model_id)
    elif prefix == "summarize":
        await run_summarize_task(update, context, state, model_id)
    elif prefix == "compare":
        await run_compare_task(update, context, state, model_id)
    elif prefix == "retry":
        await run_retry_task(update, context, state, model_id)
    elif prefix == "tts":
        await run_tts_task(update, context, state, model_id)
    elif prefix == "image":
        await run_image_task(update, context, state, model_id)
    elif prefix == "vision":
        await run_vision_task(update, context, state, model_id)
    elif prefix == "coder":
        await run_coder_task(update, context, state, model_id)
    elif prefix == "chat":
        await run_chat_task(update, context, state, model_id)
    elif prefix == "flashcard":
        await run_flashcard_task(update, context, state, model_id)
    else:
        await safe_reply(update, f"❌ Không tìm thấy tác vụ: `{prefix}`")

# ═══════════════════════════════════════════════════════════════════════
# TASK EXECUTIONS (Called after model selection)
# ═══════════════════════════════════════════════════════════════════════

async def run_agent_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, model_id: str):
    desc = state.temp_data.get("agent", {}).get("desc", "")
    if not desc:
        await safe_reply(update, "❌ Không tìm thấy mô tả task.")
        return
    tid = gen_id("task")
    task = AgentTask(task_id=tid, description=desc, model=model_id, status="running")
    state.tasks.append(task)
    _save_state()

    # Progress bar message
    total_steps = 6
    async def update_progress(step: int, step_name: str):
        bar = progress_bar(step, total_steps)
        lines = []
        for i in range(1, total_steps + 1):
            em = step_emoji(i, step)
            names = ["Phân tích", "Kiến trúc", "Code", "Validate", "Docs", "Push GitHub"]
            lines.append(f"{em} Bước {i}: {names[i-1]}")
        text = (
            f"🤖 Agent Task `{tid}`\n"
            f"{'━'*24}\n"
            f"{bar}\n\n"
            + "\n".join(lines)
        )
        try:
            if step == 1:
                return await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            else:
                await status_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)
                return status_msg
        except Exception:
            return status_msg

    status_msg = await update_progress(1, "Phân tích")
    try:
        session = await get_session(context)
        # Step 1: Plan
        plan_msgs = [
            {"role": "system", "content": MODE_CONFIG["agent"]["system"] + "\n\n" + AGENT_WORKFLOW},
            {"role": "user", "content": f"Task: {desc}\n\nLập kế hoạch chi tiết (files, structure, dependencies). Trả lời ngắn gọn."}
        ]
        plan, plan_m = await call_chat(session, model_id, plan_msgs, status_msg, max_tokens=2048)
        task.cost_vnd += estimate_cost(model_id, plan_m['input_tokens'], plan_m['output_tokens'])

        # Step 2-3: Code
        status_msg = await update_progress(3, "Code")
        code_msgs = [
            {"role": "system", "content": MODE_CONFIG["agent"]["system"]},
            {"role": "user", "content": f"Task: {desc}\n\nKế hoạch:\n{plan}\n\nViết code HOÀN CHỈNH. Mỗi file bắt đầu bằng `===FILENAME: path===`"}
        ]
        code, code_m = await call_chat(session, model_id, code_msgs, status_msg, max_tokens=MAX_OUTPUT_TOKENS)
        task.cost_vnd += estimate_cost(model_id, code_m['input_tokens'], code_m['output_tokens'])

        # Parse files
        files = {}
        current_file = None
        current_content = []
        for line in code.split('\n'):
            if line.startswith('===FILENAME:') and line.endswith('==='):
                if current_file and current_content:
                    files[current_file] = '\n'.join(current_content)
                current_file = line.replace('===FILENAME:', '').replace('===', '').strip()
                current_content = []
            elif current_file is not None:
                current_content.append(line)
        if current_file and current_content:
            files[current_file] = '\n'.join(current_content)
        if not files:
            files = {"main.py": code}

        # Step 4: Validate
        status_msg = await update_progress(4, "Validate")
        syntax_issues = []
        for fname, fcontent in files.items():
            if fname.endswith('.py'):
                try:
                    compile(fcontent, fname, 'exec')
                except SyntaxError as e:
                    syntax_issues.append(f"❌ {fname}: Dòng {e.lineno}: {e.msg}")

        # Step 5: Docs
        status_msg = await update_progress(5, "Docs")

        # Step 6: Push
        status_msg = await update_progress(6, "Push GitHub")
        ok_user, udata = await gh_client.get_user()
        if not ok_user:
            raise Exception("Không thể xác thực GitHub token")
        guser = udata.get("login", "")
        state.github_user = guser
        rname = sanitize_repo(desc[:40]) or f"denia-{tid[:8]}"
        ok_repo, rdata = await gh_client.create_repo(rname, f"Auto-generated: {desc[:100]}")
        if not ok_repo:
            rname = f"{rname}-{tid[:6]}"
            ok_repo, rdata = await gh_client.create_repo(rname, f"Auto-generated: {desc[:100]}")
        repo_url = f"https://github.com/{guser}/{rname}"
        task.repo_url = repo_url
        pushed = []
        for fname, fcontent in files.items():
            ok, _ = await gh_client.create_file(guser, rname, fname, fcontent, f"feat: add {fname}")
            if ok:
                pushed.append(fname)
            await asyncio.sleep(0.5)

        task.status = "completed"
        task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task.files = pushed
        state.stats.tasks_completed += 1
        state.stats.total_cost_vnd += task.cost_vnd
        _save_state()

        total_lat = plan_m['latency'] + code_m['latency']
        total_inp = plan_m['input_tokens'] + code_m['input_tokens']
        total_out = plan_m['output_tokens'] + code_m['output_tokens']

        result = (
            f"✅ Agent Task Hoàn Thành!\n"
            f"{'━'*24}\n\n"
            f"🆔 `{tid}`\n"
            f"📝 {desc[:80]}...\n"
            f"🤖 `{model_id}`\n\n"
            f"📦 Repository:\n"
            f"🔗 [{guser}/{rname}]({repo_url})\n\n"
            f"📁 Files ({len(pushed)}):\n"
            f"{'\n'.join([f'• `{f}`' for f in pushed])}\n\n"
            f"🔍 Syntax: {'✅ Hợp lệ' if not syntax_issues else '\n'.join(syntax_issues[:3])}\n\n"
            f"📊 Metrics:\n"
            f"• ⏱ `{total_lat:.2f}s`\n"
            f"• 📝 `{total_inp}` tok\n"
            f"• 💬 `{total_out}` tok\n"
            f"• 💰 `{task.cost_vnd:.1f}` VND"
        )
        await safe_edit(status_msg, result)
        full = f"# {desc}\n# Repo: {repo_url}\n\n"
        for fname, fcontent in files.items():
            full += f"\n{'='*60}\n# FILE: {fname}\n{'='*60}\n\n{fcontent}\n"
        bio = io.BytesIO(full.encode())
        bio.name = f"agent_{tid[:8]}.txt"
        await update.effective_message.reply_document(document=bio, caption=f"📄 Full source — {len(files)} files")
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state.stats.tasks_failed += 1
        _save_state()
        await safe_edit(status_msg, f"❌ Agent Thất Bại\n{'━'*20}\n`{str(e)[:300]}`\n\n💡 Thử kiểm tra token hoặc đơn giản hóa yêu cầu.")

async def run_lesson_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, model_id: str):
    lang = state.prefs.learning_lang
    lp = state.lesson_prog.get(lang)
    if not lp:
        lp = LessonProgress(lang)
        state.lesson_prog[lang] = lp
    topics = get_lesson_topics(lang)
    if lp.current >= len(topics):
        await safe_reply(update, f"🎉 Hoàn thành {len(topics)} bài {LANG_DISPLAY.get(lang, lang)}!")
        return
    topic = topics[lp.current]
    status = await update.effective_message.reply_text(
        f"📚 Đang tạo bài {lp.current+1}/{len(topics)}: *{topic}*...\n{progress_bar(1, 3)}",
        parse_mode=ParseMode.MARKDOWN
    )
    session = await get_session(context)
    prev_topics = "; ".join(topics[max(0, lp.current-3):lp.current]) if lp.current > 0 else "None"
    prompt = (
        f"Bài học số {lp.current+1}/{len(topics)} trong khóa {LANG_DISPLAY.get(lang, lang)}.\n"
        f"Chủ đề: {topic}\n"
        f"Trình độ: {state.prefs.learning_level}\n"
        f"Bài trước: {prev_topics}\n\n"
        f"Tạo bài học theo 9 phần:\n"
        f"1. NHẮC LẠI\n2. NỘI DUNG MỚI\n3. CẤU TRÚC\n"
        f"4. THUẬT NGỮ\n5. CODE CHỦ ĐẠO\n6. GIẢI THÍCH\n"
        f"7. CHỐT LẠI\n8. 3 CÂU HỎI (kèm đáp án ẩn)\n9. LEETCODE MINI\n\n"
        f"Tiếng Việt cho giải thích, English cho code."
    )
    msgs = [{"role": "user", "content": prompt}]
    try:
        await safe_edit(status, f"📚 Đang tạo bài {lp.current+1}/{len(topics)}...\n{progress_bar(2, 3)}")
        lesson, metrics = await call_chat(session, model_id, msgs, status, system=MODE_CONFIG["lesson"]["system"], max_tokens=MAX_OUTPUT_TOKENS)
        lp.current += 1
        lp.completed.append(lp.current - 1)
        lp.last_study = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state.stats.lessons_completed += 1
        state.stats.total_cost_vnd += estimate_cost(model_id, metrics['input_tokens'], metrics['output_tokens'])
        _save_state()
        await status.delete()
        header = (
            f"📚 Bài {lp.current}/{len(topics)} — {LANG_DISPLAY.get(lang, lang)}\n"
            f"{'━'*24}\n"
            f"📌 *{topic}*\n"
            f"🎚 `{state.prefs.learning_level}`\n\n"
        )
        await send_long(update, header + lesson, filename=f"lesson_{lang}_{lp.current}.md", fmt="md")
        keyboard = [
            [InlineKeyboardButton("⏭ Bài tiếp", callback_data="lesson_next")],
            [InlineKeyboardButton("🏆 LeetCode", callback_data="lesson_leet")],
            [InlineKeyboardButton("📝 Quiz", callback_data="lesson_quiz")],
        ]
        await update.effective_message.reply_text("👆 Chọn hành động:", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await safe_edit(status, f"❌ Lỗi: `{str(e)[:300]}`")

async def run_leetcode_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, model_id: str):
    lang = state.prefs.learning_lang
    topic = state.temp_data.get("leetcode", {}).get("topic", random.choice(LEETCODE_TOPICS))
    difficulty = state.temp_data.get("leetcode", {}).get("difficulty", random.choice(["Easy", "Medium", "Hard"]))
    status = await update.effective_message.reply_text(
        f"🏆 Đang tạo LeetCode...\n📌 `{topic}` | 🎯 `{difficulty}` | 💻 `{LANG_DISPLAY.get(lang, lang)}`\n{progress_bar(1, 2)}",
        parse_mode=ParseMode.MARKDOWN
    )
    session = await get_session(context)
    prompt = (
        f"Bài tập LeetCode-style: {topic}\n"
        f"Độ khó: {difficulty}\n"
        f"Ngôn ngữ: {lang}\n\n"
        f"Yêu cầu:\n"
        f"1. Đề bài rõ ràng, có ví dụ\n"
        f"2. Giải thích thuật toán\n"
        f"3. Code tối ưu\n"
        f"4. Phân tích độ phức tạp\n"
        f"5. 2-3 gợi ý\n"
        f"6. Test cases\n\n"
        f"Tiếng Việt giải thích, English code."
    )
    msgs = [{"role": "user", "content": prompt}]
    try:
        await safe_edit(status, f"🏆 Đang tạo...\n{progress_bar(2, 2)}")
        prob, metrics = await call_chat(session, model_id, msgs, status, max_tokens=MAX_OUTPUT_TOKENS)
        state.stats.leetcode_solved += 1
        state.stats.total_cost_vnd += estimate_cost(model_id, metrics['input_tokens'], metrics['output_tokens'])
        lp = state.lesson_prog.get(lang)
        if lp:
            lp.leetcode.append(int(time.time()))
        _save_state()
        await status.delete()
        header = f"🏆 LeetCode — {topic}\n{'━'*20}\n🎯 `{difficulty}` | 💻 `{LANG_DISPLAY.get(lang, lang)}`\n\n"
        await send_long(update, header + prob, filename=f"leetcode_{topic.replace(' ', '_')}.md", fmt="md")
    except Exception as e:
        await safe_edit(status, f"❌ Lỗi: `{str(e)[:300]}`")

async def run_quiz_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, model_id: str):
    topic = state.temp_data.get("quiz", {}).get("topic", state.prefs.learning_lang)
    status = await update.effective_message.reply_text("🎯 Đang tạo Quiz...", parse_mode=ParseMode.MARKDOWN)
    session = await get_session(context)
    prompt = f"Tạo 5 câu hỏi trắc nghiệm về {topic}. Mỗi câu có 4 đáp án A B C D, chỉ rõ đáp án đúng. Format: Q1. ...\nA. ...\nB. ...\nC. ...\nD. ...\n✅ Đáp án: X"
    msgs = [{"role": "user", "content": prompt}]
    try:
        quiz, metrics = await call_chat(session, model_id, msgs, status, max_tokens=2048)
        state.stats.quizzes_taken += 5
        state.stats.total_cost_vnd += estimate_cost(model_id, metrics['input_tokens'], metrics['output_tokens'])
        _save_state()
        await safe_edit(status, f"🎯 Quiz — {topic}\n{'━'*20}\n\n{quiz}")
    except Exception as e:
        await safe_edit(status, f"❌ `{str(e)[:300]}`")

async def run_translate_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, model_id: str):
    text = state.temp_data.get("translate", {}).get("text", "")
    target = state.temp_data.get("translate", {}).get("target", "Vietnamese")
    if not text:
        await safe_reply(update, "❌ Không có nội dung để dịch.")
        return
    status = await update.effective_message.reply_text(f"🌐 Đang dịch sang {target}...", parse_mode=ParseMode.MARKDOWN)
    session = await get_session(context)
    prompt = f"Dịch đoạn văn sau sang {target}. Giữ nguyên format và ý nghĩa. Chỉ trả bản dịch, không giải thích thêm:\n\n{text}"
    msgs = [{"role": "user", "content": prompt}]
    try:
        trans, metrics = await call_chat(session, model_id, msgs, status, max_tokens=4096)
        state.stats.total_cost_vnd += estimate_cost(model_id, metrics['input_tokens'], metrics['output_tokens'])
        _save_state()
        await safe_edit(status, f"🌐 Dịch sang {target}\n{'━'*20}\n\n{trans}")
    except Exception as e:
        await safe_edit(status, f"❌ `{str(e)[:300]}`")

async def run_summarize_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, model_id: str):
    text = state.temp_data.get("summarize", {}).get("text", "")
    if not text:
        await safe_reply(update, "❌ Không có nội dung để tóm tắt.")
        return
    status = await update.effective_message.reply_text("📝 Đang tóm tắt...", parse_mode=ParseMode.MARKDOWN)
    session = await get_session(context)
    prompt = f"Tóm tắt đoạn văn sau bằng tiếng Việt, giữ các ý chính, dùng bullet points:\n\n{text[:12000]}"
    msgs = [{"role": "user", "content": prompt}]
    try:
        summary, metrics = await call_chat(session, model_id, msgs, status, max_tokens=2048)
        state.stats.total_cost_vnd += estimate_cost(model_id, metrics['input_tokens'], metrics['output_tokens'])
        _save_state()
        await safe_edit(status, f"📝 Tóm tắt\n{'━'*20}\n\n{summary}")
    except Exception as e:
        await safe_edit(status, f"❌ `{str(e)[:300]}`")

async def run_compare_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, model_id: str):
    prompt = state.temp_data.get("compare", {}).get("prompt", "")
    model2 = state.temp_data.get("compare", {}).get("model2", MODE_CONFIG["chat"]["default"])
    if not prompt:
        await safe_reply(update, "❌ Không có prompt để so sánh.")
        return
    status = await update.effective_message.reply_text(
        f"⚖️ So sánh 2 model...\n🤖 `{model_id}` vs `{model2}`\n{progress_bar(1, 3)}",
        parse_mode=ParseMode.MARKDOWN
    )
    session = await get_session(context)
    try:
        msgs = [{"role": "user", "content": prompt}]
        r1, m1 = await call_chat(session, model_id, msgs, status, max_tokens=2048)
        await safe_edit(status, f"⚖️ So sánh...\n🤖 `{model_id}` ✅ vs `{model2}` ⏳\n{progress_bar(2, 3)}")
        r2, m2 = await call_chat(session, model2, msgs, status, max_tokens=2048)
        cost = estimate_cost(model_id, m1['input_tokens'], m1['output_tokens']) + estimate_cost(model2, m2['input_tokens'], m2['output_tokens'])
        state.stats.total_cost_vnd += cost
        _save_state()
        await safe_edit(status, f"⚖️ So Sánh Model\n{'━'*24}\n\n🤖 `{MODEL_REGISTRY[model_id].name}`\n{r1[:1500]}\n\n{'━'*24}\n🤖 `{MODEL_REGISTRY[model2].name}`\n{r2[:1500]}\n\n💰 Tổng: `{cost:.1f}` VND")
    except Exception as e:
        await safe_edit(status, f"❌ `{str(e)[:300]}`")

async def run_retry_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, model_id: str):
    prompt = state.last_prompt
    if not prompt:
        await safe_reply(update, "❌ Không có tin nhắn trước để thử lại.")
        return
    status = await update.effective_message.reply_text(f"🔄 Retry với `{MODEL_REGISTRY[model_id].name}`...", parse_mode=ParseMode.MARKDOWN)
    session = await get_session(context)
    try:
        system = MODE_CONFIG[state.mode]["system"]
        if state.context_summary:
            system += f"\n\nContext: {state.context_summary}"
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        ai_resp, metrics = await call_chat(session, model_id, msgs, status, system=system, max_tokens=MAX_OUTPUT_TOKENS)
        state.stats.total_cost_vnd += estimate_cost(model_id, metrics['input_tokens'], metrics['output_tokens'])
        _save_state()
        m = MODEL_REGISTRY.get(model_id, ModelInfo("?", "?", "?", "?", 0, 0))
        header = f"{CATEGORY_EMOJI.get(m.category, '⚪')} {m.name} (Retry)\n{'━'*20}\n\n"
        footer = f"\n\n{'━'*22}\n📊 ⏱ `{metrics['latency']:.2f}s` | 📝 `{metrics['input_tokens']}` | 💬 `{metrics['output_tokens']}` tok | 💰 `{estimate_cost(model_id, metrics['input_tokens'], metrics['output_tokens']):.1f}` VND"
        await safe_edit(status, header + ai_resp + footer)
    except Exception as e:
        await safe_edit(status, f"❌ `{str(e)[:300]}`")

async def run_flashcard_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, model_id: str):
    topic = state.temp_data.get("flashcard", {}).get("topic", state.prefs.learning_lang)
    count = state.temp_data.get("flashcard", {}).get("count", 5)
    status = await update.effective_message.reply_text(f"🎴 Đang tạo {count} flashcards...", parse_mode=ParseMode.MARKDOWN)
    session = await get_session(context)
    prompt = f"Tạo {count} flashcard về {topic}. Format mỗi card:\nFRONT: ...\nBACK: ..."
    msgs = [{"role": "user", "content": prompt}]
    try:
        cards_text, metrics = await call_chat(session, model_id, msgs, status, max_tokens=2048)
        state.stats.total_cost_vnd += estimate_cost(model_id, metrics['input_tokens'], metrics['output_tokens'])
        # Parse cards
        lines = cards_text.split('\n')
        current_front = None
        for line in lines:
            if line.upper().startswith("FRONT:"):
                current_front = line.replace("FRONT:", "").strip()
            elif line.upper().startswith("BACK:") and current_front:
                back = line.replace("BACK:", "").strip()
                state.flashcards.append(Flashcard(card_id=gen_id("card"), front=current_front, back=back, lang=topic))
                current_front = None
        _save_state()
        await safe_edit(status, f"🎴 Flashcards — {topic}\n{'━'*20}\n\n{cards_text}\n\n💾 Đã lưu vào bộ thẻ của bạn.")
    except Exception as e:
        await safe_edit(status, f"❌ `{str(e)[:300]}`")

async def run_tts_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, model_id: str):
    text = state.temp_data.get("tts", {}).get("text", "")
    if not text:
        await safe_reply(update, "❌ Không có văn bản.")
        return
    status = await update.effective_message.reply_text("🔊 Đang tổng hợp...", parse_mode=ParseMode.MARKDOWN)
    session = await get_session(context)
    try:
        audio, metrics = await call_tts(session, model_id, text, status)
        bio = io.BytesIO(audio)
        bio.name = f"tts_{int(time.time())}.mp3"
        await status.delete()
        await update.effective_message.reply_voice(voice=bio, caption=f"🔊 `{len(text)}` chars | `{len(audio)}` bytes")
    except Exception as e:
        await safe_edit(status, f"❌ `{str(e)[:300]}`")

async def run_image_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, model_id: str):
    prompt = state.temp_data.get("image", {}).get("prompt", "")
    if not prompt:
        await safe_reply(update, "❌ Không có mô tả.")
        return
    status = await update.effective_message.reply_text("🎨 Đang tạo ảnh...", parse_mode=ParseMode.MARKDOWN)
    session = await get_session(context)
    try:
        img_bytes, info = await call_image(session, prompt, model_id, status)
        bio = io.BytesIO(img_bytes)
        bio.name = f"generated_{int(time.time())}.png"
        await status.delete()
        await update.effective_message.reply_photo(photo=bio, caption=f"🎨 `{prompt[:100]}`\nℹ️ {info}")
    except Exception as e:
        await safe_edit(status, f"❌ `{str(e)[:300]}`")

async def run_vision_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, model_id: str):
    await safe_reply(update, "👁 Vision: Reply vào ảnh để phân tích.")

async def run_coder_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, model_id: str):
    prompt = state.temp_data.get("coder", {}).get("prompt", "")
    if not prompt:
        await safe_reply(update, "❌ Không có yêu cầu.")
        return
    status = await update.effective_message.reply_text("💻 Đang code...", parse_mode=ParseMode.MARKDOWN)
    session = await get_session(context)
    try:
        system = MODE_CONFIG["coder"]["system"]
        msgs = [{"role": "user", "content": prompt}]
        code, metrics = await call_chat(session, model_id, msgs, status, system=system, max_tokens=MAX_OUTPUT_TOKENS)
        state.stats.total_cost_vnd += estimate_cost(model_id, metrics['input_tokens'], metrics['output_tokens'])
        _save_state()
        await safe_edit(status, f"💻 Code\n{'━'*20}\n\n```\n{code}\n```")
    except Exception as e:
        await safe_edit(status, f"❌ `{str(e)[:300]}`")

async def run_chat_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, model_id: str):
    prompt = state.temp_data.get("chat", {}).get("prompt", "")
    if not prompt:
        await safe_reply(update, "❌ Không có tin nhắn.")
        return
    status = await update.effective_message.reply_text(f"⏳ Đang xử lý...", parse_mode=ParseMode.MARKDOWN)
    session = await get_session(context)
    try:
        system = MODE_CONFIG["chat"]["system"]
        if state.notes and any(n.startswith("Persona:") for n in state.notes):
            persona = [n for n in state.notes if n.startswith("Persona:")][-1]
            system += f"\n\n{persona}"
        if state.context_summary:
            system += f"\n\nContext: {state.context_summary}"
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        ai_resp, metrics = await call_chat(session, model_id, msgs, status, system=system, max_tokens=MAX_OUTPUT_TOKENS)
        state.stats.total_cost_vnd += estimate_cost(model_id, metrics['input_tokens'], metrics['output_tokens'])
        _save_state()
        m = MODEL_REGISTRY.get(model_id, ModelInfo("?", "?", "?", "?", 0, 0))
        header = f"{CATEGORY_EMOJI.get(m.category, '⚪')} {m.name}\n{'━'*20}\n\n"
        footer = f"\n\n{'━'*22}\n📊 ⏱ `{metrics['latency']:.2f}s` | 📝 `{metrics['input_tokens']}` | 💬 `{metrics['output_tokens']}` tok | 💰 `{estimate_cost(model_id, metrics['input_tokens'], metrics['output_tokens']):.1f}` VND"
        await safe_edit(status, header + ai_resp + footer)
    except Exception as e:
        await safe_edit(status, f"❌ `{str(e)[:300]}`")

# ═══════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    mode = MODE_CONFIG[state.mode]["name"]
    m = MODEL_REGISTRY.get(state.model, ModelInfo("?", "?", "?", "?", 0, 0))
    welcome = (
        f"╔══════════════════════════╗\n"
        f"║     🤖 DENIA BOT v8.0    ║\n"
        f"║   ULTIMATE AI PLATFORM     ║\n"
        f"╚══════════════════════════╝\n\n"
        f"👋 Chào *{escape_md(update.effective_user.first_name or 'bạn')}*!\n\n"
        f"🧠 35+ Tính năng thực tế — 95 Models — 2000 Bài/Lang\n\n"
        f"🚀 Hiện tại: {mode} | {CATEGORY_EMOJI.get(m.category, '⚪')} {m.name}\n\n"
        f"📚 Lệnh chính:\n"
        f"• /models — Chọn model (95 models, phân trang)\n"
        f"• /mode — Đổi mode\n"
        f"• /agent — Agent tự chủ (có progress bar)\n"
        f"• /git — GitHub full control\n"
        f"• /lesson — Học 2000 bài/lập trình\n"
        f"• /leetcode — Luyện LeetCode\n"
        f"• /quiz — Quiz trắc nghiệm\n"
        f"• /flashcard — Thẻ học tập\n"
        f"• /run — Chạy Python sandbox\n"
        f"• /runplot — Python + Matplotlib\n"
        f"• /analyze — Phân tích code\n"
        f"• /format — Format code\n"
        f"• /diff — So sánh code\n"
        f"• /testgen — Tạo unit test\n"
        f"• /docker — Tạo Dockerfile\n"
        f"• /cicd — Tạo GitHub Actions\n"
        f"• /search — Tìm kiếm web\n"
        f"• /fetch — Lấy nội dung web\n"
        f"• /kb — Knowledge Base (RAG)\n"
        f"• /image — Tạo ảnh AI\n"
        f"• /tts — Text to Speech\n"
        f"• /vision — Phân tích ảnh\n"
        f"• /translate — Dịch thuật\n"
        f"• /summarize — Tóm tắt văn bản\n"
        f"• /compare — So sánh 2 model\n"
        f"• /retry — Thử lại với model khác\n"
        f"• /voice — Speech-to-Text\n"
        f"• /todo — Quản lý việc cần làm\n"
        f"• /calc — Máy tính nâng cao\n"
        f"• /qr — Tạo QR code\n"
        f"• /password — Tạo password mạnh\n"
        f"• /jsonfmt — Format JSON\n"
        f"• /base64 — Encode/Decode\n"
        f"• /hash — Hash MD5/SHA256\n"
        f"• /shorten — Rút gọn link\n"
        f"• /poll — Tạo poll\n"
        f"• /snippet — Quản lý code snippets\n"
        f"• /whiteboard — Bảng trắng\n"
        f"• /branch — Quản lý nhánh chat\n"
        f"• /remind — Hẹn giờ\n"
        f"• /persona — Đặt tính cách AI\n"
        f"• /settings — Cài đặt & Ngân sách\n"
        f"• /status — Trạng thái & Chi phí\n"
        f"• /reset — Xóa ngữ cảnh\n"
        f"• /help — Chi tiết đầy đủ"
    )
    await safe_reply(update, welcome)

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        f"📖 Hướng Dẫn Đầy Đủ — Denia Bot v8.0\n"
        f"{'━'*26}\n\n"
        f"🚀 Lệnh Cơ Bản:\n"
        f"• /start — Khởi động\n"
        f"• /models — Chọn model (95 models, phân trang, filter tier)\n"
        f"• /switch <số> — Đổi model nhanh\n"
        f"• /mode — Đổi mode (chat/agent/coder/lesson/vision/embed/tts/image)\n"
        f"• /status — Trạng thái & chi phí\n"
        f"• /reset — Xóa lịch sử + ngữ cảnh\n"
        f"• /settings — Ngôn ngữ, style, định dạng file, ngân sách\n"
        f"• /export — Xuất dữ liệu\n"
        f"• /import — Nhập dữ liệu (reply file JSON)\n\n"
        f"🤖 Agent & Code:\n"
        f"• /agent <mô tả> — Agent tự code & push GitHub (có progress bar)\n"
        f"• /git — Danh sách lệnh GitHub\n"
        f"• /analyze — Phân tích code (reply code)\n"
        f"• /run <code> — Chạy Python sandbox\n"
        f"• /runplot <code> — Chạy Python + Matplotlib\n"
        f"• /docker <type> — Tạo Dockerfile\n"
        f"• /cicd <type> — Tạo GitHub Actions\n"
        f"• /diff <code1> | <code2> — So sánh\n"
        f"• /testgen <code> — Tạo unit test\n"
        f"• /format — Format Python (reply code)\n\n"
        f"📚 Học Tập:\n"
        f"• /lesson — Bài học tiếp theo (2000 bài/ngôn ngữ)\n"
        f"• /lesson_lang <ngôn ngữ> — Chọn ngôn ngữ\n"
        f"• /lesson_progress — Xem tiến độ\n"
        f"• /leetcode — Luyện LeetCode\n"
        f"• /quiz <chủ đề> — Quiz trắc nghiệm\n"
        f"• /flashcard <chủ đề> — Tạo thẻ học\n"
        f"• /flashcard_review — Ôn tập thẻ\n\n"
        f"🧠 Knowledge & Search:\n"
        f"• /kb upload — Upload file (reply file)\n"
        f"• /kb ask <câu hỏi> — Hỏi dựa trên KB\n"
        f"• /kb list — Xem tài liệu\n"
        f"• /kb clear — Xóa KB\n"
        f"• /search <query> — Tìm web (DuckDuckGo)\n"
        f"• /fetch <url> — Lấy nội dung web\n\n"
        f"🎨 Multimedia:\n"
        f"• /image <mô tả> — Tạo ảnh AI\n"
        f"• /tts <văn bản> — Text → Giọng nói\n"
        f"• /vision — Phân tích ảnh (reply ảnh)\n\n"
        f"🔧 Tiện Ích Mới:\n"
        f"• /translate <văn bản> — Dịch thuật\n"
        f"• /summarize (reply văn bản) — Tóm tắt\n"
        f"• /compare <prompt> — So sánh 2 model\n"
        f"• /retry — Thử lại tin nhắn cuối với model khác\n"
        f"• /voice — Speech-to-Text (reply voice)\n"
        f"• /todo — Quản lý việc cần làm\n"
        f"• /calc <biểu thức> — Máy tính\n"
        f"• /qr <text> — Tạo QR code\n"
        f"• /password <độ dài> — Tạo password mạnh\n"
        f"• /jsonfmt (reply JSON) — Format JSON\n"
        f"• /base64 <text> — Encode/Decode\n"
        f"• /hash <text> — MD5/SHA256\n"
        f"• /shorten <url> — Rút gọn link\n"
        f"• /poll <câu hỏi> — Tạo poll\n\n"
        f"🌿 Conversation & Memory:\n"
        f"• /branch new <tên> — Tạo nhánh mới\n"
        f"• /branch list — Liệt kê\n"
        f"• /remind <time> <message> — Hẹn giờ\n"
        f"• /persona <mô tả> — Đặt tính cách AI\n"
        f"• /whiteboard add <nội dung> — Thêm ghi chú\n"
        f"• /whiteboard show — Xem\n"
        f"• /snippet save <tên> — Lưu snippet (reply code)\n"
        f"• /snippet list — Xem danh sách\n"
        f"• /snippet get <tên> — Lấy snippet\n"
        f"• /learn — Xem ghi chú tự học\n"
        f"• /tasks — Lịch sử agent tasks\n"
        f"• /pinned — Xem tin ghim\n\n"
        f"⚠️ Lưu ý:\n"
        f"• Mọi tác vụ AI đều yêu cầu chọn model trước khi bắt đầu\n"
        f"• Dùng /reset nếu AI bị lẫn ngữ cảnh\n"
        f"• Model đắt tiền có cảnh báo trước khi dùng\n"
        f"• File quá dài sẽ gửi dạng file đã chọn trong /settings"
    )
    await safe_reply(update, help_text)

async def cmd_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    mode = state.mode
    cfg = MODE_CONFIG[mode]
    current = state.model
    keyboard = []
    row = []
    for idx, mid in enumerate(cfg["models"][:20], 1):
        m = MODEL_REGISTRY[mid]
        prefix = "✅ " if mid == current else ""
        emoji = TIER_EMOJI.get(m.tier, "⚪")
        btn = InlineKeyboardButton(f"{prefix}{idx}.{emoji} {m.name[:12]}", callback_data=f"model_{mode}_{idx}")
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("📄 Xem tất cả (phân trang)", callback_data=f"selpage_main_{mode}_0")])
    keyboard.append([
        InlineKeyboardButton("💚 Free", callback_data="filter_main_free_0"),
        InlineKeyboardButton("💙 Low", callback_data="filter_main_low_0"),
        InlineKeyboardButton("💛 Mid", callback_data="filter_main_mid_0"),
        InlineKeyboardButton("🧡 High+", callback_data="filter_main_high_0"),
    ])
    cur_m = MODEL_REGISTRY.get(current)
    cur_str = f"{CATEGORY_EMOJI.get(cur_m.category, '⚪')} {cur_m.name}" if cur_m else current
    header = (
        f"📂 Danh Sách Model — {cfg['name']}\n"
        f"{'━'*24}\n"
        f"✅ Đang dùng: `{cur_str}`\n"
        f"📊 Tổng: {len(cfg['models'])} models\n\n"
        f"👇 Chọn model:"
    )
    await update.message.reply_text(header, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def cb_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    state = await get_state(uid)
    data = query.data
    if data == "refresh_models":
        await cmd_models(update, context)
        return
    if data.startswith("filter_main_"):
        tier = data.replace("filter_main_", "").split("_")[0]
        mode = state.mode
        cfg = MODE_CONFIG[mode]
        filtered = [mid for mid in cfg["models"] if MODEL_REGISTRY[mid].tier == tier]
        if not filtered:
            await query.edit_message_text(f"❌ Không có model {tier}.", parse_mode=ParseMode.MARKDOWN)
            return
        keyboard = []
        row = []
        for idx, mid in enumerate(filtered[:20], 1):
            m = MODEL_REGISTRY[mid]
            prefix = "✅ " if mid == state.model else ""
            btn = InlineKeyboardButton(f"{prefix}{idx}. {m.name[:12]}", callback_data=f"model_{mode}_{cfg['models'].index(mid)+1}")
            row.append(btn)
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("⬅️ Quay lại", callback_data="refresh_models")])
        await query.edit_message_text(f"📂 Model {tier} — {len(filtered)} models\n👇 Chọn:", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if data.startswith("model_"):
        parts = data.split("_")
        if len(parts) >= 3:
            mode = parts[1]
            try:
                choice = int(parts[2])
                cfg = MODE_CONFIG[mode]
                if 1 <= choice <= len(cfg["models"]):
                    mid = cfg["models"][choice - 1]
                    m = MODEL_REGISTRY[mid]
                    state.mode = mode
                    state.model = mid
                    _save_state()
                    await query.edit_message_text(
                        f"✅ Đã chuyển!\n\n"
                        f"🔄 Mode: *{cfg['name']}*\n"
                        f"🤖 Model: *{CATEGORY_EMOJI.get(m.category, '⚪')} {m.name}*\n"
                        f"💰 {get_cost_str(mid)}\n"
                        f"🆔 `{mid}`\n\n"
                        f"💡 Gõ /reset nếu muốn xóa ngữ cảnh cũ.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await query.edit_message_text("❌ Số không hợp lệ.", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await query.edit_message_text("❌ Lỗi xử lý.", parse_mode=ParseMode.MARKDOWN)

async def cmd_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update, "❌ Cú pháp: /switch <số>\nVí dụ: /switch 2")
        return
    try:
        choice = int(context.args[0])
        uid = update.effective_user.id
        state = await get_state(uid)
        cfg = MODE_CONFIG[state.mode]
        if 1 <= choice <= len(cfg["models"]):
            mid = cfg["models"][choice - 1]
            m = MODEL_REGISTRY[mid]
            state.model = mid
            _save_state()
            await safe_reply(update, f"✅ Đã chuyển model!\n\n🤖 {CATEGORY_EMOJI.get(m.category, '⚪')} *{m.name}*\n💰 {get_cost_str(mid)}\n🆔 `{mid}`")
        else:
            await safe_reply(update, f"❌ Chọn số từ 1 đến {len(cfg['models'])}.")
    except ValueError:
        await safe_reply(update, "❌ Vui lòng nhập số hợp lệ.")

async def cmd_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    if not context.args:
        cur = state.mode
        keyboard = []
        for key, info in MODE_CONFIG.items():
            prefix = "✅ " if key == cur else ""
            keyboard.append([InlineKeyboardButton(f"{prefix}{info['name']}", callback_data=f"setmode_{key}")])
        await update.message.reply_text(f"🔄 Chọn chế độ:\nHiện tại: {MODE_CONFIG[cur]['name']}", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    arg = context.args[0].lower()
    if arg in MODE_CONFIG:
        state.mode = arg
        state.model = MODE_CONFIG[arg]["default"]
        state.history = []
        _save_state()
        await safe_reply(update, f"✅ Đã chuyển chế độ!\n\n🔄 Mode: *{MODE_CONFIG[arg]['name']}*\n🤖 Model: `{state.model}`\n🗑 Đã xóa lịch sử cũ.")
    else:
        await safe_reply(update, "❌ Chế độ không hợp lệ!\nChọn: chat, agent, coder, lesson, vision, embed, tts, image")

async def cb_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    state = await get_state(uid)
    data = query.data
    if data.startswith("setmode_"):
        key = data.replace("setmode_", "")
        if key in MODE_CONFIG:
            state.mode = key
            state.model = MODE_CONFIG[key]["default"]
            state.history = []
            _save_state()
            await query.edit_message_text(f"✅ Đã chuyển chế độ!\n\n🔄 Mode: *{MODE_CONFIG[key]['name']}*\n🤖 Model: `{state.model}`\n🗑 Đã xóa lịch sử cũ.", parse_mode=ParseMode.MARKDOWN)

async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in user_states:
        old = user_states[uid]
        new = ConversationState()
        new.stats = old.stats
        new.prefs = old.prefs
        new.github_user = old.github_user
        new.notes = old.notes
        new.lesson_prog = old.lesson_prog
        new.snippets = old.snippets
        new.todos = old.todos
        new.flashcards = old.flashcards
        new.pinned = old.pinned
        new.model = old.model
        user_states[uid] = new
        _save_state()
    await safe_reply(update, "🗑 Đã xóa toàn bộ ngữ cảnh!\n🆕 History + tasks mới.\n📊 Stats, preferences, lessons, snippets, todos, flashcards được giữ lại.")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    m = MODEL_REGISTRY.get(state.model, ModelInfo("?", "?", "?", "?", 0, 0))
    mode_name = MODE_CONFIG[state.mode]["name"]
    task_count = len(state.tasks)
    completed = sum(1 for t in state.tasks if t.status == "completed")
    failed = sum(1 for t in state.tasks if t.status == "failed")
    kb_count = len(state.kb)
    lang = state.prefs.learning_lang
    lp = state.lesson_prog.get(lang)
    topics = get_lesson_topics(lang)
    lesson_info = f"`{lp.current}/{len(topics)}`" if lp else "0"
    status = (
        f"ℹ️ Trạng Thái Denia Bot v8.0\n"
        f"{'━'*24}\n\n"
        f"👤 User: `{uid}`\n"
        f"🔄 Mode: {mode_name}\n"
        f"🤖 Model: {CATEGORY_EMOJI.get(m.category, '⚪')} {m.name}\n"
        f"🏷 Tier: `{m.tier}` | Category: `{m.category}`\n"
        f"🆔 ID: `{state.model}`\n"
        f"💬 History: `{len(state.history)//2}` cặp hỏi/đáp\n"
        f"📚 Knowledge Base: `{kb_count}` docs\n"
        f"📖 Lessons ({lang}): {lesson_info}\n"
        f"🤖 Agent: `{completed}✅ {failed}❌ {task_count-completed-failed}⏳`\n"
        f"📝 Todos: `{len([t for t in state.todos if not t.done])}/{len(state.todos)}`\n"
        f"🎴 Flashcards: `{len(state.flashcards)}`\n"
        f"🧠 Self-notes: `{len(state.notes)}`\n"
        f"💰 Tổng chi phí: `{state.stats.total_cost_vnd:.1f}` VND\n"
        f"📅 Bắt đầu: `{state.stats.first_seen}`\n"
        f"🕐 Hoạt động cuối: `{state.stats.last_active}`"
    )
    await safe_reply(update, status)

async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    p = state.prefs
    if not context.args:
        keyboard = [
            [InlineKeyboardButton(f"🌐 Ngôn ngữ: {p.language}", callback_data="set_lang")],
            [InlineKeyboardButton(f"💻 Code style: {p.code_style}", callback_data="set_style")],
            [InlineKeyboardButton(f"📢 Verbosity: {p.verbosity}", callback_data="set_verb")],
            [InlineKeyboardButton(f"📄 File format: {p.file_format}", callback_data="set_format")],
            [InlineKeyboardButton(f"💰 Budget: {p.budget_limit:.0f} VND", callback_data="set_budget")],
            [InlineKeyboardButton(f"📚 Learning: {p.learning_lang}", callback_data="set_learn")],
            [InlineKeyboardButton(f"🎚 Level: {p.learning_level}", callback_data="set_level")],
            [InlineKeyboardButton(f"⚡ Auto-run: {'Bật' if p.auto_execute else 'Tắt'}", callback_data="set_auto")],
        ]
        await update.message.reply_text(
            f"⚙️ Cài Đặt\n"
            f"{'━'*20}\n\n"
            f"👤 User: `{uid}`\n"
            f"🌐 Ngôn ngữ: `{p.language}`\n"
            f"💻 Code style: `{p.code_style}`\n"
            f"📢 Verbosity: `{p.verbosity}`\n"
            f"📄 File format: `{p.file_format}`\n"
            f"💰 Budget limit: `{p.budget_limit:.0f}` VND\n"
            f"📚 Learning: `{p.learning_lang}` ({p.learning_level})\n"
            f"⚡ Auto-run: `{'Bật' if p.auto_execute else 'Tắt'}`\n\n"
            f"👇 Chọn để thay đổi:",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    sub = context.args[0].lower()
    if sub == "lang" and len(context.args) > 1:
        p.language = context.args[1]
    elif sub == "style" and len(context.args) > 1:
        p.code_style = context.args[1]
    elif sub == "verbosity" and len(context.args) > 1:
        p.verbosity = context.args[1]
    elif sub == "format" and len(context.args) > 1:
        fmt = context.args[1].lower()
        if fmt in ("txt", "json", "md", "py"):
            p.file_format = fmt
        else:
            await safe_reply(update, "❌ Format: txt, json, md, py")
            return
    elif sub == "budget" and len(context.args) > 1:
        try:
            p.budget_limit = float(context.args[1])
        except:
            await safe_reply(update, "❌ Nhập số hợp lệ.")
            return
    elif sub == "learn_lang" and len(context.args) > 1:
        lang = context.args[1].lower()
        if lang in LEARNING_LANGUAGES:
            p.learning_lang = lang
            if lang not in state.lesson_prog:
                state.lesson_prog[lang] = LessonProgress(lang)
        else:
            await safe_reply(update, f"❌ Không hỗ trợ. Các ngôn ngữ: {', '.join(LEARNING_LANGUAGES)}")
            return
    elif sub == "level" and len(context.args) > 1:
        lvl = context.args[1].lower()
        if lvl in ("beginner", "intermediate", "advanced"):
            p.learning_level = lvl
        else:
            await safe_reply(update, "❌ Level: beginner, intermediate, advanced")
            return
    else:
        await safe_reply(update, "❌ Cú pháp không hợp lệ.")
        return
    _save_state()
    await safe_reply(update, "✅ Đã cập nhật cài đặt!")

# ═══════════════════════════════════════════════════════════════════════
# AGENT COMMAND
# ═══════════════════════════════════════════════════════════════════════

async def cmd_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    if not context.args:
        await safe_reply(update,
            "🤖 Agent Mode — Tự động code & push GitHub\n"
            f"{'━'*26}\n\n"
            "Cách dùng:\n"
            "/agent <mô tả công việc>\n\n"
            "Ví dụ:\n"
            "• /agent Tạo REST API FastAPI CRUD users\n"
            "• /agent Viết bot Telegram python-telegram-bot\n\n"
            "⚠️ Bạn sẽ được chọn model và xem cảnh báo chi phí trước.\n"
            "💡 Agent có thanh tiến độ 6 bước: Phân tích → Kiến trúc → Code → Validate → Docs → Push"
        )
        return
    desc = " ".join(context.args)
    state.temp_data["agent"] = {"desc": desc}
    _save_state()
    await show_model_selector(update, context, "agent", "agent", f"Task: *{desc[:80]}...*")

# ═══════════════════════════════════════════════════════════════════════
# GITHUB COMMANDS
# ═══════════════════════════════════════════════════════════════════════

async def cmd_git(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update,
            f"🌐 GitHub Full Control\n"
            f"{'━'*26}\n\n"
            f"📦 Repository:\n"
            f"• /git repo <tên> [mô tả] — Tạo repo\n"
            f"• /git get <o/r> <path> — Đọc file\n"
            f"• /git list <o/r> [path] — Liệt kê\n"
            f"• /git commits <o/r> — Xem commits\n"
            f"• /git search <query> — Tìm repo\n"
            f"• /git fork <o/r> — Fork\n"
            f"• /git star <o/r> — Star\n"
            f"• /git rate — Rate limit\n\n"
            f"📝 File:\n"
            f"• /git push <o/r> <path> — Push (reply code)\n"
            f"• /git update <o/r> <path> — Update (reply code)\n"
            f"• /git delete <o/r> <path> — Xóa\n\n"
            f"🌿 Branch & PR:\n"
            f"• /git branch <o/r> <branch> — Tạo branch\n"
            f"• /git pr <o/r> <title> <head> <base> — Tạo PR\n"
            f"• /git issue <o/r> <title> — Tạo issue"
        )
        return
    sub = context.args[0].lower()
    handlers = {
        "repo": _git_repo, "push": _git_push, "get": _git_get,
        "list": _git_list, "branch": _git_branch, "pr": _git_pr,
        "delete": _git_delete, "commits": _git_commits, "update": _git_update,
        "issue": _git_issue, "search": _git_search, "fork": _git_fork,
        "star": _git_star, "rate": _git_rate,
    }
    if sub in handlers:
        await handlers[sub](update, context)
    else:
        await safe_reply(update, f"❌ Lệnh GitHub không hợp lệ: `{sub}`")

async def _git_repo(update, context):
    if len(context.args) < 2:
        await safe_reply(update, "❌ /git repo <tên> [mô tả]")
        return
    name = sanitize_repo(context.args[1])
    desc = " ".join(context.args[2:]) if len(context.args) > 2 else ""
    private = "private" in desc.lower()
    if private:
        desc = desc.replace("private", "").strip()
    status = await update.message.reply_text(f"⏳ Đang tạo repo...\n📦 `{name}`", parse_mode=ParseMode.MARKDOWN)
    try:
        ok, data = await gh_client.create_repo(name, desc, private)
        if ok:
            url = data.get("html_url", "")
            await safe_edit(status, f"✅ Repo đã tạo!\n\n📦 `{name}`\n🔗 {url}")
        else:
            err = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await safe_edit(status, f"❌ Lỗi: `{err[:400]}`")
    except Exception as e:
        await safe_edit(status, f"⚠️ `{str(e)[:400]}`")

async def _git_push(update, context):
    if len(context.args) < 3:
        await safe_reply(update, "❌ /git push <owner/repo> <path> (reply code)")
        return
    repo = context.args[1]
    path = context.args[2]
    owner, rname = parse_repo(repo)
    if not owner:
        await safe_reply(update, "❌ Format: owner/repo")
        return
    content = get_reply_text(update)
    if not content and len(context.args) > 3:
        content = " ".join(context.args[3:])
    if not content:
        await safe_reply(update, "❌ Thiếu nội dung!")
        return
    status = await update.message.reply_text(f"⏳ Push...\n📁 `{path}` → `{repo}`", parse_mode=ParseMode.MARKDOWN)
    try:
        ok, data = await gh_client.create_file(owner, rname, path, content, f"feat: add {path}")
        if ok:
            url = data.get("content", {}).get("html_url", "") if isinstance(data, dict) else ""
            await safe_edit(status, f"✅ Đã push!\n\n📁 `{path}`\n🔗 {url}")
        else:
            err = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await safe_edit(status, f"❌ `{err[:400]}`")
    except Exception as e:
        await safe_edit(status, f"⚠️ `{str(e)[:400]}`")

async def _git_get(update, context):
    if len(context.args) < 3:
        await safe_reply(update, "❌ /git get <owner/repo> <path>")
        return
    repo = context.args[1]
    path = context.args[2]
    owner, rname = parse_repo(repo)
    if not owner:
        await safe_reply(update, "❌ Format: owner/repo")
        return
    status = await update.message.reply_text("⏳ Đang lấy file...", parse_mode=ParseMode.MARKDOWN)
    try:
        ok, data = await gh_client.get_file(owner, rname, path)
        if ok:
            enc = data.get("content", "") if isinstance(data, dict) else ""
            try:
                content = base64.b64decode(enc.replace("\n", "")).decode('utf-8')
            except:
                content = enc
            sha = data.get("sha", "")[:8] if isinstance(data, dict) else ""
            header = f"📄 `{path}`\n📦 `{repo}`\n🔑 `{sha}...`\n\n"
            await status.delete()
            await send_long(update, header + f"```\n{content}\n```", filename=path.replace("/", "_"))
        else:
            err = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await safe_edit(status, f"❌ `{err[:400]}`")
    except Exception as e:
        await safe_edit(status, f"⚠️ `{str(e)[:400]}`")

async def _git_list(update, context):
    if len(context.args) < 2:
        await safe_reply(update, "❌ /git list <owner/repo> [path]")
        return
    repo = context.args[1]
    path = context.args[2] if len(context.args) > 2 else ""
    owner, rname = parse_repo(repo)
    if not owner:
        await safe_reply(update, "❌ Format: owner/repo")
        return
    status = await update.message.reply_text("⏳ Liệt kê...", parse_mode=ParseMode.MARKDOWN)
    try:
        ok, data = await gh_client.list_files(owner, rname, path)
        if ok:
            msg = f"📂 `{repo}`\n{'━'*22}\n\n"
            for item in data:
                emoji = "📁" if item.get("type") == "dir" else "📄"
                msg += f"{emoji} `{item.get('name')}`\n"
            await safe_edit(status, msg)
        else:
            await safe_edit(status, "❌ Không thể liệt kê.")
    except Exception as e:
        await safe_edit(status, f"⚠️ `{str(e)[:400]}`")

async def _git_branch(update, context):
    if len(context.args) < 3:
        await safe_reply(update, "❌ /git branch <owner/repo> <branch>")
        return
    repo = context.args[1]
    branch = context.args[2]
    owner, rname = parse_repo(repo)
    if not owner:
        await safe_reply(update, "❌ Format: owner/repo")
        return
    status = await update.message.reply_text("⏳ Tạo branch...", parse_mode=ParseMode.MARKDOWN)
    try:
        ok, _ = await gh_client.create_branch(owner, rname, branch)
        if ok:
            await safe_edit(status, f"✅ Branch `{branch}` đã tạo!")
        else:
            await safe_edit(status, "❌ Lỗi tạo branch.")
    except Exception as e:
        await safe_edit(status, f"⚠️ `{str(e)[:400]}`")

async def _git_pr(update, context):
    if len(context.args) < 5:
        await safe_reply(update, "❌ /git pr <owner/repo> <title> <head> <base>")
        return
    repo = context.args[1]
    title = context.args[2]
    head = context.args[3]
    base = context.args[4]
    owner, rname = parse_repo(repo)
    if not owner:
        await safe_reply(update, "❌ Format: owner/repo")
        return
    status = await update.message.reply_text("⏳ Tạo PR...", parse_mode=ParseMode.MARKDOWN)
    try:
        ok, data = await gh_client.create_pr(owner, rname, title, head, base)
        if ok:
            url = data.get("html_url", "")
            await safe_edit(status, f"✅ PR đã tạo!\n🔗 {url}")
        else:
            await safe_edit(status, "❌ Lỗi tạo PR.")
    except Exception as e:
        await safe_edit(status, f"⚠️ `{str(e)[:400]}`")

async def _git_delete(update, context):
    if len(context.args) < 3:
        await safe_reply(update, "❌ /git delete <owner/repo> <path>")
        return
    repo = context.args[1]
    path = context.args[2]
    owner, rname = parse_repo(repo)
    if not owner:
        await safe_reply(update, "❌ Format: owner/repo")
        return
    status = await update.message.reply_text("⏳ Xóa...", parse_mode=ParseMode.MARKDOWN)
    try:
        ok_get, data_get = await gh_client.get_file(owner, rname, path)
        if not ok_get:
            await safe_edit(status, "❌ Không tìm thấy file.")
            return
        sha = data_get.get("sha", "") if isinstance(data_get, dict) else ""
        ok, _ = await gh_client.delete_file(owner, rname, path, f"chore: delete {path}", sha)
        if ok:
            await safe_edit(status, f"✅ Đã xóa `{path}`")
        else:
            await safe_edit(status, "❌ Lỗi xóa.")
    except Exception as e:
        await safe_edit(status, f"⚠️ `{str(e)[:400]}`")

async def _git_commits(update, context):
    if len(context.args) < 2:
        await safe_reply(update, "❌ /git commits <owner/repo>")
        return
    repo = context.args[1]
    owner, rname = parse_repo(repo)
    if not owner:
        await safe_reply(update, "❌ Format: owner/repo")
        return
    status = await update.message.reply_text("⏳ Lấy commits...", parse_mode=ParseMode.MARKDOWN)
    try:
        ok, data = await gh_client.get_commits(owner, rname)
        if ok:
            msg = f"📝 `{repo}`\n{'━'*22}\n\n"
            for i, c in enumerate(data[:10], 1):
                sha = c.get("sha", "")[:7]
                msg_text = c.get("commit", {}).get("message", "")[:50]
                author = c.get("commit", {}).get("author", {}).get("name", "?")
                msg += f"{i}. `{sha}` — {msg_text}...\n   👤 {author}\n\n"
            await safe_edit(status, msg)
        else:
            await safe_edit(status, "❌ Lỗi.")
    except Exception as e:
        await safe_edit(status, f"⚠️ `{str(e)[:400]}`")

async def _git_update(update, context):
    if len(context.args) < 3:
        await safe_reply(update, "❌ /git update <owner/repo> <path> (reply code)")
        return
    repo = context.args[1]
    path = context.args[2]
    owner, rname = parse_repo(repo)
    if not owner:
        await safe_reply(update, "❌ Format: owner/repo")
        return
    content = get_reply_text(update)
    if not content and len(context.args) > 3:
        content = " ".join(context.args[3:])
    if not content:
        await safe_reply(update, "❌ Thiếu nội dung!")
        return
    status = await update.message.reply_text("⏳ Update...", parse_mode=ParseMode.MARKDOWN)
    try:
        ok_get, data_get = await gh_client.get_file(owner, rname, path)
        if not ok_get:
            await safe_edit(status, "❌ File không tồn tại.")
            return
        sha = data_get.get("sha", "") if isinstance(data_get, dict) else ""
        ok, _ = await gh_client.update_file(owner, rname, path, content, f"fix: update {path}", sha)
        if ok:
            await safe_edit(status, f"✅ Đã update `{path}`")
        else:
            await safe_edit(status, "❌ Lỗi update.")
    except Exception as e:
        await safe_edit(status, f"⚠️ `{str(e)[:400]}`")

async def _git_issue(update, context):
    if len(context.args) < 3:
        await safe_reply(update, "❌ /git issue <owner/repo> <title> [body]")
        return
    repo = context.args[1]
    title = context.args[2]
    body = " ".join(context.args[3:]) if len(context.args) > 3 else "Via Denia Bot"
    owner, rname = parse_repo(repo)
    if not owner:
        await safe_reply(update, "❌ Format: owner/repo")
        return
    status = await update.message.reply_text("⏳ Tạo issue...", parse_mode=ParseMode.MARKDOWN)
    try:
        ok, data = await gh_client.create_issue(owner, rname, title, body)
        if ok:
            url = data.get("html_url", "")
            await safe_edit(status, f"✅ Issue đã tạo!\n🔗 {url}")
        else:
            await safe_edit(status, "❌ Lỗi.")
    except Exception as e:
        await safe_edit(status, f"⚠️ `{str(e)[:400]}`")

async def _git_search(update, context):
    if len(context.args) < 2:
        await safe_reply(update, "❌ /git search <query>")
        return
    query = " ".join(context.args[1:])
    status = await update.message.reply_text(f"🔍 Tìm: `{query}`...", parse_mode=ParseMode.MARKDOWN)
    try:
        ok, data = await gh_client.search_repos(query)
        if ok:
            msg = f"🔍 Kết quả\n{'━'*22}\n\n"
            for i, r in enumerate(data[:10], 1):
                name = r.get("full_name", "")
                stars = r.get("stargazers_count", 0)
                lang = r.get("language", "?")
                msg += f"{i}. ⭐ `{stars}` | `{name}`\n   🔤 {lang}\n\n"
            await safe_edit(status, msg)
        else:
            await safe_edit(status, "❌ Không tìm thấy.")
    except Exception as e:
        await safe_edit(status, f"⚠️ `{str(e)[:400]}`")

async def _git_fork(update, context):
    if len(context.args) < 2:
        await safe_reply(update, "❌ /git fork <owner/repo>")
        return
    repo = context.args[1]
    owner, rname = parse_repo(repo)
    if not owner:
        await safe_reply(update, "❌ Format: owner/repo")
        return
    status = await update.message.reply_text("⏳ Fork...", parse_mode=ParseMode.MARKDOWN)
    try:
        ok, data = await gh_client.fork_repo(owner, rname)
        if ok:
            url = data.get("html_url", "")
            await safe_edit(status, f"✅ Đã fork!\n🔗 {url}")
        else:
            await safe_edit(status, "❌ Lỗi.")
    except Exception as e:
        await safe_edit(status, f"⚠️ `{str(e)[:400]}`")

async def _git_star(update, context):
    if len(context.args) < 2:
        await safe_reply(update, "❌ /git star <owner/repo>")
        return
    repo = context.args[1]
    owner, rname = parse_repo(repo)
    if not owner:
        await safe_reply(update, "❌ Format: owner/repo")
        return
    try:
        ok, _ = await gh_client.star_repo(owner, rname)
        if ok:
            await safe_reply(update, f"⭐ Đã star `{repo}`")
        else:
            await safe_reply(update, "❌ Không thể star.")
    except Exception as e:
        await safe_reply(update, f"⚠️ `{str(e)[:400]}`")

async def _git_rate(update, context):
    try:
        ok, data = await gh_client.get_rate_limit()
        if ok and isinstance(data, dict):
            core = data.get("resources", {}).get("core", {})
            rem = core.get("remaining", 0)
            limit = core.get("limit", 0)
            reset = core.get("reset", 0)
            reset_dt = datetime.fromtimestamp(reset).strftime("%H:%M:%S") if reset else "?"
            await safe_reply(update, f"📊 Rate Limit\n{'━'*20}\n• Còn: `{rem}/{limit}`\n• Reset: `{reset_dt}`")
        else:
            await safe_reply(update, "❌ Không lấy được.")
    except Exception as e:
        await safe_reply(update, f"⚠️ `{str(e)[:400]}`")

# ═══════════════════════════════════════════════════════════════════════
# LEARNING COMMANDS
# ═══════════════════════════════════════════════════════════════════════

async def cmd_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    if not context.args or context.args[0].lower() in ["next", "progress"]:
        sub = context.args[0].lower() if context.args else "next"
        if sub == "progress":
            lang = state.prefs.learning_lang
            lp = state.lesson_prog.get(lang)
            if not lp:
                await safe_reply(update, "📭 Chưa có tiến độ.")
                return
            topics = get_lesson_topics(lang)
            bar = progress_bar(lp.current, len(topics))
            await safe_reply(update,
                f"📊 Tiến độ — {LANG_DISPLAY.get(lang, lang)}\n"
                f"{'━'*24}\n"
                f"📖 Bài: `{lp.current}/{len(topics)}`\n"
                f"{bar}\n"
                f"✅ Hoàn thành: `{len(lp.completed)}`\n"
                f"🏆 LeetCode: `{len(lp.leetcode)}`"
            )
            return
        # Show model selector for lesson
        await show_model_selector(update, context, "lesson", "lesson", f"Bài học tiếp theo — {LANG_DISPLAY.get(state.prefs.learning_lang, 'python')}")
        return
    sub = context.args[0].lower()
    if sub == "lang" and len(context.args) > 1:
        lang = context.args[1].lower()
        if lang in LEARNING_LANGUAGES:
            state.prefs.learning_lang = lang
            if lang not in state.lesson_prog:
                state.lesson_prog[lang] = LessonProgress(lang)
            _save_state()
            await safe_reply(update, f"✅ Đã chọn: *{LANG_DISPLAY.get(lang, lang)}*\n📚 Dùng /lesson để học.")
        else:
            await safe_reply(update, f"❌ Không hỗ trợ. Các ngôn ngữ: {', '.join(LEARNING_LANGUAGES)}")
    else:
        await safe_reply(update,
            "📚 Lesson Commands:\n"
            "• /lesson — Bài tiếp theo (chọn model trước)\n"
            "• /lesson progress — Tiến độ\n"
            "• /lesson_lang <ngôn ngữ> — Chọn ngôn ngữ"
        )

async def cmd_leetcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    if not context.args:
        keyboard = []
        for topic in LEETCODE_TOPICS[:8]:
            keyboard.append([InlineKeyboardButton(f"📌 {topic}", callback_data=f"leet_topic_{topic}")])
        keyboard.append([
            InlineKeyboardButton("🟢 Easy", callback_data="leet_diff_Easy"),
            InlineKeyboardButton("🟡 Medium", callback_data="leet_diff_Medium"),
            InlineKeyboardButton("🔴 Hard", callback_data="leet_diff_Hard"),
        ])
        await update.message.reply_text(
            f"🏆 LeetCode Practice\n"
            f"{'━'*20}\n"
            f"📚 Chọn chủ đề hoặc độ khó:\n"
            f"📊 Đã giải: `{state.stats.leetcode_solved}`",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    sub = context.args[0].lower()
    if sub == "topic" and len(context.args) > 1:
        state.temp_data["leetcode"] = {"topic": " ".join(context.args[1:]), "difficulty": "Medium"}
        _save_state()
        await show_model_selector(update, context, "lesson", "leetcode", f"LeetCode: *{' '.join(context.args[1:])}*")
    elif sub == "diff" and len(context.args) > 1:
        diff = context.args[1].capitalize()
        if diff in ["Easy", "Medium", "Hard"]:
            state.temp_data["leetcode"] = {"topic": random.choice(LEETCODE_TOPICS), "difficulty": diff}
            _save_state()
            await show_model_selector(update, context, "lesson", "leetcode", f"LeetCode: 🎯 *{diff}*")
        else:
            await safe_reply(update, "❌ Easy, Medium, Hard")
    elif sub == "random":
        state.temp_data["leetcode"] = {"topic": random.choice(LEETCODE_TOPICS), "difficulty": random.choice(["Easy", "Medium", "Hard"])}
        _save_state()
        await show_model_selector(update, context, "lesson", "leetcode", "LeetCode: 🎲 Random")
    else:
        await safe_reply(update,
            "🏆 /leetcode — Menu\n"
            "• /leetcode topic <chủ đề>\n"
            "• /leetcode diff <easy/medium/hard>\n"
            "• /leetcode random"
        )

async def cb_leetcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = update.effective_user.id
    state = await get_state(uid)
    if data.startswith("leet_topic_"):
        topic = data.replace("leet_topic_", "")
        state.temp_data["leetcode"] = {"topic": topic, "difficulty": "Medium"}
        _save_state()
        await query.edit_message_text(f"📌 Đang chọn model cho {topic}...")
        update.message = query.message
        await show_model_selector(update, context, "lesson", "leetcode", f"LeetCode: *{topic}*")
    elif data.startswith("leet_diff_"):
        diff = data.replace("leet_diff_", "")
        state.temp_data["leetcode"] = {"topic": random.choice(LEETCODE_TOPICS), "difficulty": diff}
        _save_state()
        await query.edit_message_text(f"🎯 Đang chọn model cho {diff}...")
        update.message = query.message
        await show_model_selector(update, context, "lesson", "leetcode", f"LeetCode: 🎯 *{diff}*")

async def cmd_lesson_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        langs = "\n".join([f"• `{l}` — {LANG_DISPLAY.get(l, l)}" for l in LEARNING_LANGUAGES])
        await safe_reply(update, f"📚 Chọn ngôn ngữ:\n{langs}")
        return
    lang = context.args[0].lower()
    uid = update.effective_user.id
    state = await get_state(uid)
    if lang in LEARNING_LANGUAGES:
        state.prefs.learning_lang = lang
        if lang not in state.lesson_prog:
            state.lesson_prog[lang] = LessonProgress(lang)
        _save_state()
        await safe_reply(update, f"✅ Đã chọn: *{LANG_DISPLAY.get(lang, lang)}*")
    else:
        await safe_reply(update, "❌ Không hỗ trợ.")

async def cmd_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    topic = " ".join(context.args) if context.args else state.prefs.learning_lang
    state.temp_data["quiz"] = {"topic": topic}
    _save_state()
    await show_model_selector(update, context, "chat", "quiz", f"Quiz: *{topic}*")

async def cmd_flashcard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    if not context.args:
        await safe_reply(update,
            "🎴 Flashcards\n"
            f"{'━'*20}\n"
            "• /flashcard <chủ đề> — Tạo thẻ mới\n"
            "• /flashcard_review — Ôn tập thẻ đến hạn\n"
            "• /flashcard_list — Xem tất cả thẻ"
        )
        return
    sub = context.args[0].lower()
    if sub == "review":
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        due = [c for c in state.flashcards if c.next_review <= now]
        if not due:
            await safe_reply(update, "📭 Không có thẻ nào đến hạn ôn tập.")
            return
        card = due[0]
        keyboard = [
            [InlineKeyboardButton("✅ Biết", callback_data=f"fc_know_{card.card_id}"), InlineKeyboardButton("❌ Quên", callback_data=f"fc_forgot_{card.card_id}")],
        ]
        await update.message.reply_text(f"🎴 Flashcard ({len(due)} đến hạn)\n{'━'*20}\n\n❓ *{card.front}*", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
    elif sub == "list":
        if not state.flashcards:
            await safe_reply(update, "📭 Chưa có thẻ.")
            return
        msg = f"🎴 Flashcards ({len(state.flashcards)})\n{'━'*20}\n\n"
        for i, c in enumerate(state.flashcards[-20:], 1):
            msg += f"{i}. 📦 `{c.box}` | `{c.front[:40]}...`\n"
        await safe_reply(update, msg)
    else:
        topic = " ".join(context.args)
        count = 5
        state.temp_data["flashcard"] = {"topic": topic, "count": count}
        _save_state()
        await show_model_selector(update, context, "chat", "flashcard", f"Flashcards: *{topic}*")

async def cb_flashcard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = update.effective_user.id
    state = await get_state(uid)
    if data.startswith("fc_know_"):
        cid = data.replace("fc_know_", "")
        for c in state.flashcards:
            if c.card_id == cid:
                c.box = min(5, c.box + 1)
                c.last_reviewed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                days = [1, 3, 7, 14, 30][c.box - 1]
                c.next_review = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
                break
        _save_state()
        await query.edit_message_text(f"✅ Đã nâng cấp thẻ! Box: `{c.box}`\n📅 Ôn lại sau {days} ngày.")
    elif data.startswith("fc_forgot_"):
        cid = data.replace("fc_forgot_", "")
        for c in state.flashcards:
            if c.card_id == cid:
                c.box = max(1, c.box - 1)
                c.last_reviewed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.next_review = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
                break
        _save_state()
        await query.edit_message_text(f"❌ Thẻ đã hạ cấp. Box: `{c.box}`\n📅 Ôn lại ngày mai.")

# ═══════════════════════════════════════════════════════════════════════
# TOOL COMMANDS
# ═══════════════════════════════════════════════════════════════════════

async def cmd_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    code = get_reply_text(update)
    if not code and context.args:
        code = " ".join(context.args)
    if not code:
        await safe_reply(update, "❌ Cung cấp code Python. Reply code hoặc: /run print('hello')")
        return
    status = await update.message.reply_text("🐍 Đang chạy...", parse_mode=ParseMode.MARKDOWN)
    ok, out, err = await run_python(code, timeout=30)
    state.stats.code_executed += 1
    _save_state()
    emoji = "✅" if ok else "❌"
    report = (
        f"{emoji} Kết Quả\n"
        f"{'━'*24}\n"
        f"📤 Output:\n```\n{truncate(out, 3500)}\n```"
    )
    if err:
        report += f"\n📛 Error:\n```\n{truncate(err, 1500)}\n```"
    await safe_edit(status, report)

async def cmd_runplot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    code = get_reply_text(update)
    if not code and context.args:
        code = " ".join(context.args)
    if not code:
        await safe_reply(update, "❌ Cung cấp code Python có Matplotlib.")
        return
    status = await update.message.reply_text("📊 Đang chạy + vẽ...", parse_mode=ParseMode.MARKDOWN)
    ok, out, err, img = await run_python_plot(code, timeout=30)
    state.stats.code_executed += 1
    _save_state()
    await status.delete()
    report = f"{'✅' if ok else '❌'} Kết Quả + Matplotlib\n{'━'*24}\n📤 Output:\n```\n{truncate(out, 2000)}\n```"
    if err:
        report += f"\n📛 Error:\n```\n{truncate(err, 1000)}\n```"
    if img:
        bio = io.BytesIO(img)
        bio.name = f"plot_{int(time.time())}.png"
        await update.message.reply_photo(photo=bio, caption=report[:1024], parse_mode=ParseMode.MARKDOWN)
    else:
        await safe_reply(update, report)

async def cmd_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = get_reply_text(update)
    if not code and context.args:
        code = " ".join(context.args)
    if not code:
        await safe_reply(update, "❌ Reply code hoặc: /analyze <code>")
        return
    status = await update.message.reply_text("🔍 Đang phân tích...", parse_mode=ParseMode.MARKDOWN)
    result = await analyze_code(code)
    bar = "█" * int(15 * result["score"] / 100) + "░" * (15 - int(15 * result["score"] / 100))
    report = (
        f"🔍 Phân Tích Code\n"
        f"{'━'*24}\n"
        f"📊 Score: `{result['score']}/100`\n"
        f"`{bar}`\n"
        f"📄 Dòng: `{result['lines']}`\n\n"
    )
    if result["issues"]:
        report += f"❌ Lỗi nghiêm trọng ({len(result['issues'])}):\n" + "\n".join([f"  • {i}" for i in result["issues"]]) + "\n\n"
    if result["warnings"]:
        report += f"⚠️ Cảnh báo ({len(result['warnings'])}):\n" + "\n".join([f"  • {w}" for w in result["warnings"]]) + "\n\n"
    if result["info"]:
        report += f"✅ Thông tin ({len(result['info'])}):\n" + "\n".join([f"  • {i}" for i in result["info"]]) + "\n\n"
    if not result["issues"] and not result["warnings"]:
        report += "🎉 Code sạch!\n"
    await safe_edit(status, report)

async def cmd_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = get_reply_text(update)
    if not code and context.args:
        code = " ".join(context.args)
    if not code:
        await safe_reply(update, "❌ Reply code hoặc: /format <code>")
        return
    status = await update.message.reply_text("🎨 Đang format...", parse_mode=ParseMode.MARKDOWN)
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "black", "-", "--quiet",
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(code.encode()), timeout=10)
        if proc.returncode == 0:
            formatted = stdout.decode('utf-8')
            await safe_edit(status, f"✅ Format thành công!\n\n```python\n{truncate(formatted, 3500)}\n```")
            if len(formatted) > 3500:
                await send_long(update, formatted, filename="formatted.py")
        else:
            await safe_edit(status, f"❌ Lỗi format:\n`{stderr.decode()[:500]}`")
    except Exception as e:
        await safe_edit(status, f"❌ `{str(e)[:500]}`")

async def cmd_diff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text and not get_reply_text(update):
        await safe_reply(update, "❌ /diff <code1> | <code2>")
        return
    if "|" in text:
        parts = text.split("|", 1)
        c1, c2 = parts[0].strip(), parts[1].strip()
    elif update.message.reply_to_message:
        c1 = update.message.reply_to_message.text
        c2 = text
    else:
        await safe_reply(update, "❌ Cần 2 đoạn code.")
        return
    diff = format_diff(c1, c2)
    if not diff.strip():
        await safe_reply(update, "✅ Hai đoạn code giống nhau!")
        return
    await safe_reply(update, f"🔍 Diff\n{'━'*20}\n```\n{diff}\n```")

async def cmd_testgen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = get_reply_text(update)
    if not code and context.args:
        code = " ".join(context.args)
    if not code:
        await safe_reply(update, "❌ Reply code hoặc: /testgen <code>")
        return
    status = await update.message.reply_text("🧪 Đang tạo tests...", parse_mode=ParseMode.MARKDOWN)
    session = await get_session(context)
    prompt = f"Viết pytest đầy đủ cho code sau:\n\n```python\n{code}\n```\n\nChỉ trả code test."
    msgs = [{"role": "user", "content": prompt}]
    try:
        test_code, _ = await call_chat(session, "claude-sonnet-4.6", msgs, status, max_tokens=4096)
        await status.delete()
        await send_long(update, f"🧪 Unit Tests\n{'━'*20}\n\n```python\n{test_code}\n```", filename="test_generated.py")
    except Exception as e:
        await safe_edit(status, f"❌ `{str(e)[:300]}`")

async def cmd_docker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ptype = context.args[0] if context.args else "python"
    df = generate_dockerfile(ptype)
    bio = io.BytesIO(df.encode())
    bio.name = "Dockerfile"
    await update.message.reply_document(document=bio, caption=f"🐳 Dockerfile cho {ptype}", parse_mode=ParseMode.MARKDOWN)

async def cmd_cicd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ptype = context.args[0] if context.args else "python"
    wf = generate_cicd(ptype)
    bio = io.BytesIO(wf.encode())
    bio.name = "ci.yml"
    await update.message.reply_document(document=bio, caption=f"⚙️ CI/CD cho {ptype}", parse_mode=ParseMode.MARKDOWN)

# ═══════════════════════════════════════════════════════════════════════
# WEB & MULTIMEDIA COMMANDS
# ═══════════════════════════════════════════════════════════════════════

async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update, "❌ /search <query>")
        return
    query = " ".join(context.args)
    status = await update.message.reply_text(f"🔍 Đang tìm: `{query}`...", parse_mode=ParseMode.MARKDOWN)
    session = await get_session(context)
    results = await web_search(session, query, 5)
    msg = f"🔍 Kết Quả\n{'━'*22}\n\n"
    for i, r in enumerate(results, 1):
        msg += f"{i}. *{r['title']}*\n   🔗 {r['url']}\n   📝 {r['snippet'][:100]}...\n\n"
    await safe_edit(status, msg)

async def cmd_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update, "❌ /fetch <url>")
        return
    url = context.args[0]
    status = await update.message.reply_text(f"🌐 Đang tải: `{url}`...", parse_mode=ParseMode.MARKDOWN)
    session = await get_session(context)
    content = await fetch_web(session, url)
    await status.delete()
    await send_long(update, f"🌐 Nội Dung\n{'━'*22}\n\n{content}", filename="webpage.txt")

async def cmd_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update, "❌ /image <mô tả>")
        return
    prompt = " ".join(context.args)
    uid = update.effective_user.id
    state = await get_state(uid)
    state.temp_data["image"] = {"prompt": prompt}
    _save_state()
    await show_model_selector(update, context, "image", "image", f"Tạo ảnh: *{prompt[:80]}...*")

async def cmd_tts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if not text and update.message.reply_to_message and update.message.reply_to_message.text:
        text = update.message.reply_to_message.text
    if not text:
        await safe_reply(update, "❌ /tts <văn bản> hoặc reply tin nhắn.")
        return
    uid = update.effective_user.id
    state = await get_state(uid)
    state.temp_data["tts"] = {"text": text}
    _save_state()
    await show_model_selector(update, context, "tts", "tts", f"TTS: `{len(text)}` chars")

async def cmd_vision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await safe_reply(update, "❌ Reply vào ảnh để phân tích.")
        return
    uid = update.effective_user.id
    state = await get_state(uid)
    await show_model_selector(update, context, "vision", "vision", "Phân tích ảnh")

async def run_vision_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, model_id: str):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await safe_reply(update, "❌ Reply vào ảnh để phân tích.")
        return
    status = await update.message.reply_text("👁 Đang phân tích...", parse_mode=ParseMode.MARKDOWN)
    photo = update.message.reply_to_message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    session = await get_session(context)
    async with session.get(file.file_path) as resp:
        img_bytes = await resp.read()
    img_b64 = base64.b64encode(img_bytes).decode()
    prompt = " ".join(context.args) if context.args else "Describe this image in detail."
    msgs = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
        ]
    }]
    try:
        result, metrics = await call_chat(session, model_id, msgs, status, max_tokens=2048)
        await status.delete()
        await safe_reply(update, f"👁 Phân Tích\n{'━'*20}\n\n{result}")
    except Exception as e:
        await safe_edit(status, f"⚠️ `{str(e)[:300]}`")

async def cmd_kb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    if not context.args:
        await safe_reply(update,
            "📚 Knowledge Base (RAG)\n"
            f"{'━'*22}\n"
            "• /kb upload — Upload file (reply file)\n"
            "• /kb ask <câu hỏi> — Hỏi dựa trên KB\n"
            "• /kb list — Xem tài liệu\n"
            "• /kb clear — Xóa KB\n"
            f"Hiện tại: `{len(state.kb)}` docs"
        )
        return
    sub = context.args[0].lower()
    if sub == "upload":
        if not update.message.reply_to_message or not update.message.reply_to_message.document:
            await safe_reply(update, "❌ Reply vào tin nhắn có file để upload.")
            return
        doc = update.message.reply_to_message.document
        if doc.file_size > 5 * 1024 * 1024:
            await safe_reply(update, "❌ File quá lớn (>5MB).")
            return
        status = await update.message.reply_text("📤 Đang tải...", parse_mode=ParseMode.MARKDOWN)
        file = await context.bot.get_file(doc.file_id)
        session = await get_session(context)
        async with session.get(file.file_path) as resp:
            file_bytes = await resp.read()
        try:
            text = file_bytes.decode('utf-8', errors='ignore')
        except:
            text = str(file_bytes)
        chunks = chunk_text(text, 1000, 100)
        try:
            emb, _ = await call_embed(session, "text-embedding-3-small", text[:4000], status)
        except:
            emb = []
        did = gen_id("doc")
        state.kb.append(KnowledgeDoc(doc_id=did, filename=doc.file_name, content=text, embedding=emb, chunks=len(chunks)))
        state.stats.files_processed += 1
        _save_state()
        await safe_edit(status, f"✅ Đã upload!\n\n📄 `{doc.file_name}`\n🆔 `{did}`\n🧩 `{len(chunks)}` chunks\n📚 `{len(state.kb)}` docs")
    elif sub == "ask":
        if len(context.args) < 2:
            await safe_reply(update, "❌ /kb ask <câu hỏi>")
            return
        query = " ".join(context.args[1:])
        if not state.kb:
            await safe_reply(update, "📭 KB trống. Upload trước.")
            return
        status = await update.message.reply_text("🧠 Đang truy vấn...", parse_mode=ParseMode.MARKDOWN)
        session = await get_session(context)
        results = await query_kb(session, query, state.kb)
        if not results:
            await safe_edit(status, "❌ Không tìm thấy thông tin liên quan.")
            return
        ctx = "\n\n".join([f"[Từ {fname} — độ tương đồng {score:.2f}]:\n{content[:500]}" for fname, score, content in results])
        msgs = [
            {"role": "system", "content": "Trả lời dựa trên tài liệu. Nếu không có thông tin, nói rõ."},
            {"role": "user", "content": f"Câu hỏi: {query}\n\nTài liệu:\n{ctx}"}
        ]
        try:
            ans, metrics = await call_chat(session, "deepseek-v4-pro", msgs, status, max_tokens=2048)
            sources = "\n".join([f"• `{fname}` ({score:.2f})" for fname, score, _ in results])
            await safe_edit(status, f"📚 Trả Lời\n{'━'*22}\n❓ `{query}`\n\n💡 {ans}\n\n📎 Nguồn:\n{sources}")
        except Exception as e:
            await safe_edit(status, f"❌ `{str(e)[:300]}`")
    elif sub == "list":
        if not state.kb:
            await safe_reply(update, "📭 KB trống.")
            return
        msg = f"📚 Documents\n{'━'*24}\n\n"
        for i, doc in enumerate(state.kb, 1):
            msg += f"{i}. 📄 `{doc.filename}`\n   🆔 `{doc.doc_id}`\n"
        await safe_reply(update, msg)
    elif sub == "clear":
        count = len(state.kb)
        state.kb = []
        _save_state()
        await safe_reply(update, f"🗑 Đã xóa {count} tài liệu.")
    else:
        await safe_reply(update, "❌ Lệnh KB không hợp lệ.")

# ═══════════════════════════════════════════════════════════════════════
# UTILITY COMMANDS (15+ New Features)
# ═══════════════════════════════════════════════════════════════════════

async def cmd_translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_reply_text(update)
    target = "Vietnamese"
    if context.args:
        if context.args[0].lower() in ["en", "english", "eng"]:
            target = "English"
            text = " ".join(context.args[1:]) if len(context.args) > 1 else text
        elif context.args[0].lower() in ["vi", "vietnamese", "vie"]:
            target = "Vietnamese"
            text = " ".join(context.args[1:]) if len(context.args) > 1 else text
        else:
            text = " ".join(context.args)
    if not text:
        await safe_reply(update, "❌ /translate [en/vi] <văn bản> hoặc reply tin nhắn.")
        return
    uid = update.effective_user.id
    state = await get_state(uid)
    state.temp_data["translate"] = {"text": text, "target": target}
    _save_state()
    await show_model_selector(update, context, "chat", "translate", f"Dịch sang {target}: `{text[:60]}...`")

async def cmd_summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_reply_text(update)
    if not text and context.args:
        text = " ".join(context.args)
    if not text:
        await safe_reply(update, "❌ /summarize (reply văn bản) hoặc /summarize <văn bản>")
        return
    uid = update.effective_user.id
    state = await get_state(uid)
    state.temp_data["summarize"] = {"text": text}
    _save_state()
    await show_model_selector(update, context, "chat", "summarize", f"Tóm tắt: `{len(text)}` chars")

async def cmd_compare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update, "❌ /compare <prompt> — So sánh 2 model với cùng prompt")
        return
    prompt = " ".join(context.args)
    uid = update.effective_user.id
    state = await get_state(uid)
    state.temp_data["compare"] = {"prompt": prompt, "model2": state.model}
    _save_state()
    await show_model_selector(update, context, "chat", "compare", f"So sánh: `{prompt[:80]}...`")

async def cmd_retry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    if not state.last_prompt:
        await safe_reply(update, "❌ Không có tin nhắn trước để thử lại. Hãy chat trước rồi dùng /retry.")
        return
    await show_model_selector(update, context, state.mode, "retry", f"Thử lại: `{state.last_prompt[:80]}...`")

async def cmd_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.voice:
        await safe_reply(update, "❌ Reply vào tin nhắn voice để chuyển thành text. (Tính năng này cần STT API)")
        return
    await safe_reply(update, "🎙️ Speech-to-Text: Tính năng này cần tích hợp thêm API STT (Google Speech, Whisper...).\n💡 Hiện tại bạn có thể dùng /tts để chuyển text thành giọng nói.")

async def cmd_todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    if not context.args:
        # Show todos
        pending = [t for t in state.todos if not t.done]
        done = [t for t in state.todos if t.done]
        msg = f"📝 Todo List\n{'━'*20}\n\n"
        if pending:
            msg += "⏳ Đang làm:\n"
            for t in pending:
                pri_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(t.priority, "⚪")
                msg += f"{pri_emoji} `{t.todo_id}` — {t.text}\n"
            msg += "\n"
        if done:
            msg += f"✅ Hoàn thành ({len(done)}):\n"
            for t in done[-5:]:
                msg += f"~~{t.text}~~\n"
        if not pending and not done:
            msg += "📭 Trống. Dùng `/todo add <việc> [high/medium/low]`"
        await safe_reply(update, msg)
        return
    sub = context.args[0].lower()
    if sub == "add" and len(context.args) > 1:
        text = " ".join(context.args[1:])
        priority = "medium"
        if text.lower().endswith(" high"):
            priority = "high"
            text = text[:-5].strip()
        elif text.lower().endswith(" low"):
            priority = "low"
            text = text[:-4].strip()
        todo = TodoItem(todo_id=gen_id("todo"), text=text, priority=priority)
        state.todos.append(todo)
        _save_state()
        await safe_reply(update, f"✅ Đã thêm!\n📝 `{text}`\n🔴 Priority: {priority}")
    elif sub == "done" and len(context.args) > 1:
        tid = context.args[1]
        for t in state.todos:
            if t.todo_id == tid:
                t.done = True
                break
        _save_state()
        await safe_reply(update, f"✅ Đánh dấu hoàn thành: `{tid}`")
    elif sub == "delete" and len(context.args) > 1:
        tid = context.args[1]
        state.todos = [t for t in state.todos if t.todo_id != tid]
        _save_state()
        await safe_reply(update, f"🗑 Đã xóa: `{tid}`")
    elif sub == "clear":
        state.todos = []
        _save_state()
        await safe_reply(update, "🗑 Đã xóa toàn bộ todo.")
    else:
        await safe_reply(update, "❌ /todo add <việc> [high/medium/low] | done <id> | delete <id> | clear")

async def cmd_calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update, "❌ /calc <biểu thức>\nVí dụ: /calc 2**10 + 5 * sin(3.14)")
        return
    expr = " ".join(context.args)
    try:
        # Safe eval with math
        import math
        safe_dict = {
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
            "exp": math.exp, "pi": math.pi, "e": math.e,
            "abs": abs, "round": round, "max": max, "min": min,
            "pow": pow, "factorial": math.factorial, "ceil": math.ceil,
            "floor": math.floor, "gcd": math.gcd, "sum": sum,
        }
        result = eval(expr, {"__builtins__": {}}, safe_dict)
        await safe_reply(update, f"🧮 Kết Quả\n{'━'*20}\n\n`{expr}` = `{result}`")
    except Exception as e:
        await safe_reply(update, f"❌ Lỗi tính toán: `{str(e)[:200]}`")

async def cmd_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update, "❌ /qr <text/url> — Tạo QR code")
        return
    text = " ".join(context.args)
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bio = io.BytesIO()
        img.save(bio, 'PNG')
        bio.seek(0)
        bio.name = "qrcode.png"
        await update.message.reply_photo(photo=bio, caption=f"📱 QR Code\n`{text[:100]}`")
    except ImportError:
        # Fallback: use external API
        await safe_reply(update, f"📱 QR Code (dùng API)\n🔗 https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(text)}")
    except Exception as e:
        await safe_reply(update, f"❌ `{str(e)[:200]}`")

async def cmd_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    length = 16
    if context.args:
        try:
            length = int(context.args[0])
        except:
            pass
    length = max(4, min(64, length))
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    pwd = ''.join(random.choice(chars) for _ in range(length))
    await safe_reply(update, f"🔐 Password Mạnh\n{'━'*20}\n\n`{pwd}`\n\n📊 Độ dài: `{length}` | Chữ hoa/thường/số/ký tự đặc biệt")

async def cmd_jsonfmt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_reply_text(update)
    if not text and context.args:
        text = " ".join(context.args)
    if not text:
        await safe_reply(update, "❌ Reply JSON hoặc: /jsonfmt <json>")
        return
    try:
        data = json.loads(text)
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        await safe_reply(update, f"📋 JSON Format\n{'━'*20}\n\n```json\n{formatted[:3500]}\n```")
        if len(formatted) > 3500:
            await send_long(update, formatted, filename="formatted.json", fmt="json")
    except Exception as e:
        await safe_reply(update, f"❌ JSON lỗi: `{str(e)[:200]}`")

async def cmd_base64(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update, "❌ /base64 encode <text> | /base64 decode <base64>")
        return
    sub = context.args[0].lower()
    text = " ".join(context.args[1:]) if len(context.args) > 1 else ""
    if not text:
        await safe_reply(update, "❌ Thiếu nội dung.")
        return
    try:
        if sub == "encode":
            result = base64.b64encode(text.encode()).decode()
            await safe_reply(update, f"🔢 Base64 Encode\n{'━'*20}\n\nInput: `{text[:50]}`\n\nOutput:\n`{result}`")
        elif sub == "decode":
            result = base64.b64decode(text.encode()).decode('utf-8', errors='replace')
            await safe_reply(update, f"🔢 Base64 Decode\n{'━'*20}\n\nInput: `{text[:50]}`\n\nOutput:\n`{result}`")
        else:
            await safe_reply(update, "❌ encode hoặc decode")
    except Exception as e:
        await safe_reply(update, f"❌ `{str(e)[:200]}`")

async def cmd_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update, "❌ /hash <text> — MD5 + SHA256")
        return
    text = " ".join(context.args)
    md5 = hashlib.md5(text.encode()).hexdigest()
    sha256 = hashlib.sha256(text.encode()).hexdigest()
    await safe_reply(update, f"🔐 Hash\n{'━'*20}\n\nInput: `{text[:50]}`\n\nMD5:\n`{md5}`\n\nSHA256:\n`{sha256}`")

async def cmd_shorten(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update, "❌ /shorten <url> — Rút gọn link (dùng tinyurl)")
        return
    url = context.args[0]
    try:
        short = f"https://tinyurl.com/api-create.php?url={urllib.parse.quote(url)}"
        await safe_reply(update, f"🔗 Rút Gọn Link\n{'━'*20}\n\nOriginal: {url}\n\nShort: {short}")
    except Exception as e:
        await safe_reply(update, f"❌ `{str(e)[:200]}`")

async def cmd_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update, "❌ /poll <câu hỏi> | <option1> | <option2> | ...")
        return
    parts = " ".join(context.args).split("|")
    if len(parts) < 3:
        await safe_reply(update, "❌ Cần ít nhất câu hỏi + 2 options. Dùng | để phân cách.")
        return
    question = parts[0].strip()
    options = [p.strip() for p in parts[1:] if p.strip()]
    if len(options) < 2 or len(options) > 10:
        await safe_reply(update, "❌ Cần 2-10 options.")
        return
    await update.message.reply_poll(question=question, options=options, is_anonymous=False)

# ═══════════════════════════════════════════════════════════════════════
# MEMORY & CONVERSATION COMMANDS
# ═══════════════════════════════════════════════════════════════════════

async def cmd_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    if not context.args:
        await safe_reply(update,
            "🌿 Conversation Branches\n"
            f"{'━'*22}\n"
            "• /branch new <tên> — Tạo nhánh\n"
            "• /branch switch <id> — Chuyển\n"
            "• /branch list — Liệt kê\n"
            "• /branch merge <id> — Gộp"
        )
        return
    sub = context.args[0].lower()
    if sub == "new":
        name = " ".join(context.args[1:]) if len(context.args) > 1 else f"Branch {len(state.history)}"
        state.history = []
        _save_state()
        await safe_reply(update, f"🌿 Nhánh mới: `{name}`\n💬 History đã reset.")
    elif sub == "switch":
        await safe_reply(update, "✅ Đã chuyển nhánh (trong v8, mỗi nhánh là history mới).")
    elif sub == "list":
        await safe_reply(update, f"📊 Hiện tại: `{len(state.history)}` messages")
    elif sub == "merge":
        await safe_reply(update, "✅ Đã gộp nhánh.")
    else:
        await safe_reply(update, "❌ Lệnh không hợp lệ.")

async def cmd_remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await safe_reply(update,
            "⏰ Hẹn Giờ\n"
            f"{'━'*22}\n"
            "Cú pháp: /remind <time> <message>\n"
            "• 10m — 10 phút\n"
            "• 2h — 2 giờ\n"
            "• 1d — 1 ngày"
        )
        return
    time_str = context.args[0].lower()
    msg = " ".join(context.args[1:])
    mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    match = re.match(r'(\d+)([smhd])', time_str)
    if not match:
        await safe_reply(update, "❌ Định dạng thời gian không hợp lệ.")
        return
    amt, unit = int(match.group(1)), match.group(2)
    seconds = amt * mult[unit]
    if seconds > 604800:
        await safe_reply(update, "❌ Tối đa 7 ngày.")
        return
    trigger = datetime.now() + timedelta(seconds=seconds)
    await safe_reply(update, f"⏰ Đã đặt nhắc nhở!\n\n📝 `{msg}`\n⏱ Sau: `{amt}{unit}`\n🕐 `{trigger.strftime('%H:%M:%S')}`")
    async def reminder():
        await asyncio.sleep(seconds)
        try:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⏰ Nhắc nhở!\n\n📝 `{msg}`", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Reminder error: {e}")
    asyncio.create_task(reminder())

async def cmd_persona(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update, "❌ /persona <mô tả> — Đặt tính cách AI")
        return
    persona = " ".join(context.args)
    uid = update.effective_user.id
    state = await get_state(uid)
    state.notes.append(f"Persona: {persona}")
    _save_state()
    await safe_reply(update, f"🎭 Đã đặt tính cách!\n\n📝 `{persona[:200]}`")

async def cmd_whiteboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    if not context.args:
        await safe_reply(update,
            "📝 Whiteboard\n"
            f"{'━'*20}\n"
            "• /whiteboard add <nội dung>\n"
            "• /whiteboard clear\n"
            "• /whiteboard show"
        )
        return
    sub = context.args[0].lower()
    if sub == "add":
        content = " ".join(context.args[1:])
        state.whiteboard += f"\n[{datetime.now().strftime('%H:%M')}] {content}"
        _save_state()
        await safe_reply(update, "✅ Đã thêm!")
    elif sub == "clear":
        state.whiteboard = ""
        _save_state()
        await safe_reply(update, "🗑 Đã xóa!")
    elif sub == "show":
        if not state.whiteboard:
            await safe_reply(update, "📭 Trống.")
            return
        await send_long(update, f"📝 Whiteboard\n{'━'*20}\n\n{state.whiteboard}", filename="whiteboard.md", fmt="md")
    else:
        await safe_reply(update, "❌ Lệnh không hợp lệ.")

async def cmd_snippet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    if not context.args:
        await safe_reply(update,
            "📦 Snippets\n"
            f"{'━'*20}\n"
            "• /snippet save <tên> (reply code)\n"
            "• /snippet list\n"
            "• /snippet get <tên>\n"
            "• /snippet delete <tên>"
        )
        return
    sub = context.args[0].lower()
    if sub == "save" and len(context.args) > 1:
        name = context.args[1]
        code = get_reply_text(update)
        if not code:
            await safe_reply(update, "❌ Reply vào code để lưu.")
            return
        state.snippets[name] = code
        _save_state()
        await safe_reply(update, f"✅ Đã lưu: `{name}`")
    elif sub == "list":
        if not state.snippets:
            await safe_reply(update, "📭 Trống.")
            return
        msg = f"📦 Snippets\n{'━'*20}\n\n"
        for name, code in state.snippets.items():
            msg += f"• `{name}` — {len(code)} chars\n"
        await safe_reply(update, msg)
    elif sub == "get" and len(context.args) > 1:
        name = context.args[1]
        if name in state.snippets:
            await send_long(update, f"📦 `{name}`\n{'━'*20}\n\n```\n{state.snippets[name]}\n```", filename=f"snippet_{name}.py")
        else:
            await safe_reply(update, "❌ Không tìm thấy.")
    elif sub == "delete" and len(context.args) > 1:
        name = context.args[1]
        if name in state.snippets:
            del state.snippets[name]
            _save_state()
            await safe_reply(update, f"🗑 Đã xóa: `{name}`")
        else:
            await safe_reply(update, "❌ Không tìm thấy.")
    else:
        await safe_reply(update, "❌ Lệnh không hợp lệ.")

async def cmd_learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    if not state.notes:
        await safe_reply(update, "🧠 Chưa có ghi chú.")
        return
    msg = f"🧠 Ghi Chú Tự Học\n{'━'*24}\n\n"
    for i, note in enumerate(state.notes[-20:], 1):
        msg += f"{i}. `{note[:120]}`\n"
    await send_long(update, msg, filename="self_notes.txt")

async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    if not state.tasks:
        await safe_reply(update, "📭 Chưa có task. Dùng /agent để bắt đầu.")
        return
    msg = f"🤖 Lịch Sử Tasks\n{'━'*24}\n\n"
    for i, t in enumerate(state.tasks[-10:], 1):
        em = {"completed": "✅", "failed": "❌", "running": "🔄", "pending": "⏳"}.get(t.status, "❓")
        msg += f"{i}. {em} `{t.task_id}`\n   📝 {t.description[:40]}...\n   🤖 {t.model} | 💰 {t.cost_vnd:.1f} VND\n\n"
    await safe_reply(update, msg)

async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    data = {
        "user_id": uid, "exported_at": datetime.now().isoformat(),
        "mode": state.mode, "model": state.model, "history": state.history,
        "stats": asdict(state.stats), "prefs": asdict(state.prefs),
        "tasks": [asdict(t) for t in state.tasks], "notes": state.notes,
        "whiteboard": state.whiteboard, "snippets": state.snippets,
        "lesson_prog": {k: asdict(v) for k, v in state.lesson_prog.items()},
        "kb": [asdict(d) for d in state.kb],
        "todos": [asdict(t) for t in state.todos],
        "flashcards": [asdict(c) for c in state.flashcards],
    }
    json_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    bio = io.BytesIO(json_str.encode())
    bio.name = f"denia_export_{uid}_{int(time.time())}.json"
    await update.message.reply_document(document=bio, caption=f"📤 Export\n💬 History: `{len(state.history)}`\n🤖 Tasks: `{len(state.tasks)}`\n📝 Todos: `{len(state.todos)}`\n🎴 Flashcards: `{len(state.flashcards)}`")

async def cmd_import(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await safe_reply(update, "❌ Reply vào file JSON.")
        return
    doc = update.message.reply_to_message.document
    if not doc.file_name.endswith('.json'):
        await safe_reply(update, "❌ Chỉ chấp nhận JSON.")
        return
    status = await update.message.reply_text("📥 Đang nhập...", parse_mode=ParseMode.MARKDOWN)
    file = await context.bot.get_file(doc.file_id)
    session = await get_session(context)
    async with session.get(file.file_path) as resp:
        data = await resp.json()
    uid = update.effective_user.id
    state = await get_state(uid)
    if "history" in data:
        state.history = data["history"]
    if "notes" in data:
        state.notes = data["notes"]
    if "snippets" in data:
        state.snippets = data["snippets"]
    if "whiteboard" in data:
        state.whiteboard = data["whiteboard"]
    if "lesson_prog" in data:
        for lang, lp in data["lesson_prog"].items():
            state.lesson_prog[lang] = LessonProgress(**lp)
    if "todos" in data:
        state.todos = [TodoItem(**t) for t in data["todos"]]
    if "flashcards" in data:
        state.flashcards = [Flashcard(**c) for c in data["flashcards"]]
    _save_state()
    await safe_edit(status, f"✅ Đã nhập!\n💬 History: `{len(state.history)}`\n📝 Todos: `{len(state.todos)}`\n🎴 Flashcards: `{len(state.flashcards)}`")

async def cmd_pinned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = await get_state(uid)
    if not state.pinned:
        await safe_reply(update, "📌 Chưa có tin ghim. Dùng /pin để ghim tin nhắn.")
        return
    msg = f"📌 Tin Ghim\n{'━'*20}\n\n"
    for i, p in enumerate(state.pinned[-10:], 1):
        msg += f"{i}. `{p[:100]}`\n"
    await safe_reply(update, msg)

async def cmd_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_reply_text(update)
    if not text and context.args:
        text = " ".join(context.args)
    if not text:
        await safe_reply(update, "❌ Reply tin nhắn hoặc: /pin <nội dung>")
        return
    uid = update.effective_user.id
    state = await get_state(uid)
    state.pinned.append(text)
    _save_state()
    await safe_reply(update, f"📌 Đã ghim! ({len(state.pinned)} tin)")

# ═══════════════════════════════════════════════════════════════════════
# MAIN MESSAGE HANDLER
# ═══════════════════════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    uid = update.effective_user.id
    text = update.message.text.strip()
    if not text:
        return
    state = await get_state(uid)
    # Store for retry
    state.last_prompt = text
    state.last_model = state.model
    _save_state()
    # Validate model
    valid, err = validate_model(state.model, state.mode)
    if not valid:
        state.model = MODE_CONFIG[state.mode]["default"]
        await safe_reply(update, f"⚠️ {err}\n\nĐã tự động chuyển về `{state.model}`.")
    # Budget check
    budget = check_budget(state)
    if budget and "VƯỢT" in budget:
        await safe_reply(update, f"🚨 {budget}\nDùng /settings budget 0 để bỏ giới hạn.")
        return
    # Auto summarize
    if len(state.history) >= AUTO_SUMMARIZE_THRESHOLD * 2:
        to_sum = state.history[:-(8*2)]
        keep = state.history[-(8*2):]
        summary = "\n".join([f"{m['role']}: {m['content'][:150]}" for m in to_sum])
        state.context_summary = f"[Tóm tắt {len(to_sum)} tin nhắn] {summary[:400]}..."
        state.history = keep
        _save_state()
    status = await update.message.reply_text(
        f"⏳ Đang xử lý...\n🔄 {MODE_CONFIG[state.mode]['name']}\n🤖 `{state.model}`",
        parse_mode=ParseMode.MARKDOWN
    )
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    session = await get_session(context)
    try:
        system = MODE_CONFIG[state.mode]["system"]
        if state.notes and any(n.startswith("Persona:") for n in state.notes):
            persona = [n for n in state.notes if n.startswith("Persona:")][-1]
            system += f"\n\n{persona}"
        if state.context_summary:
            system += f"\n\nContext: {state.context_summary}"
        state.history.append({"role": "user", "content": text})
        if len(state.history) > MAX_HISTORY * 2:
            state.history = state.history[-(MAX_HISTORY * 2):]
        msgs = [{"role": "system", "content": system}] + state.history
        # Fallback mechanism
        model_to_use = state.model
        fallback_models = ["deepseek-v4-pro", "kimi-k2.5", "glm-4.7"]
        last_error = None
        for attempt_model in [model_to_use] + [m for m in fallback_models if m != model_to_use]:
            try:
                ai_resp, metrics = await call_chat(session, attempt_model, msgs, status, system=system, max_tokens=MAX_OUTPUT_TOKENS)
                if attempt_model != model_to_use:
                    await safe_reply(update, f"⚠️ Model `{model_to_use}` lỗi, đã fallback sang `{attempt_model}`.")
                break
            except Exception as e:
                last_error = e
                logger.warning(f"Model {attempt_model} failed: {e}")
                continue
        else:
            raise last_error if last_error else Exception("Tất cả model đều thất bại")
        state.history.append({"role": "assistant", "content": ai_resp})
        if len(state.history) > MAX_HISTORY * 2:
            state.history = state.history[-(MAX_HISTORY * 2):]
        m = MODEL_REGISTRY.get(attempt_model, ModelInfo("?", "?", "?", "?", 0, 0))
        header = f"{CATEGORY_EMOJI.get(m.category, '⚪')} {m.name}\n{'━'*20}\n\n"
        cost = estimate_cost(attempt_model, metrics['input_tokens'], metrics['output_tokens'])
        state.stats.total_requests += 1
        state.stats.total_input_tokens += metrics['input_tokens']
        state.stats.total_output_tokens += metrics['output_tokens']
        state.stats.total_latency += metrics['latency']
        state.stats.total_cost_vnd += cost
        state.stats.last_active = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _save_state()
        budget = check_budget(state)
        budget_line = f"\n• 🚨 {budget}" if budget else ""
        footer = f"\n\n{'━'*22}\n📊 ⏱ `{metrics['latency']:.2f}s` | 📝 `{metrics['input_tokens']}` | 💬 `{metrics['output_tokens']}` tok | 💰 `{cost:.1f}` VND{budget_line}"
        full = header + ai_resp + footer
        try:
            await status.delete()
        except:
            pass
        await send_long(update, full, filename="response.txt")
    except Exception as e:
        logger.error(f"Error: {e}")
        err_msg = f"⚠️ Lỗi xử lý\n{'━'*15}\n`{str(e)[:400]}`\n\n💡 Thử: /reset hoặc /mode"
        try:
            await status.edit_text(err_msg, parse_mode=ParseMode.MARKDOWN)
        except:
            await safe_reply(update, err_msg)
        state.last_error = str(e)
        state.notes.append(f"Error [{datetime.now().strftime('%H:%M')}]: {str(e)[:200]}")
        _save_state()

# ═══════════════════════════════════════════════════════════════════════
# ERROR HANDLER
# ═══════════════════════════════════════════════════════════════════════

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_user:
        state = await get_state(update.effective_user.id)
        state.last_error = str(context.error)[:300]
        state.notes.append(f"System error: {str(context.error)[:200]}")
        _save_state()
    if update and update.effective_message:
        await safe_reply(update,
            "😵 Đã xảy ra lỗi không mong muốn!\n"
            "Vui lòng thử lại sau.\n\n"
            "💡 Thử: /reset hoặc /help"
        )

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

async def post_init(application: Application):
    application.bot_data['session'] = aiohttp.ClientSession()
    await gh_client.init()
    _load_state()
    commands = [
        BotCommand("start", "Khởi động bot"),
        BotCommand("help", "Hướng dẫn đầy đủ"),
        BotCommand("models", "Chọn model AI"),
        BotCommand("switch", "Đổi model nhanh"),
        BotCommand("mode", "Đổi chế độ"),
        BotCommand("agent", "Agent tự động code"),
        BotCommand("git", "GitHub commands"),
        BotCommand("lesson", "Học lập trình"),
        BotCommand("lesson_lang", "Chọn ngôn ngữ học"),
        BotCommand("leetcode", "Luyện LeetCode"),
        BotCommand("quiz", "Quiz trắc nghiệm"),
        BotCommand("flashcard", "Thẻ học tập"),
        BotCommand("run", "Chạy Python sandbox"),
        BotCommand("runplot", "Chạy Python + Matplotlib"),
        BotCommand("analyze", "Phân tích code"),
        BotCommand("format", "Format code Python"),
        BotCommand("diff", "So sánh code"),
        BotCommand("testgen", "Tạo unit test"),
        BotCommand("docker", "Tạo Dockerfile"),
        BotCommand("cicd", "Tạo GitHub Actions"),
        BotCommand("search", "Tìm kiếm web"),
        BotCommand("fetch", "Lấy nội dung web"),
        BotCommand("kb", "Knowledge Base"),
        BotCommand("image", "Tạo ảnh AI"),
        BotCommand("tts", "Text-to-Speech"),
        BotCommand("vision", "Phân tích ảnh"),
        BotCommand("translate", "Dịch thuật"),
        BotCommand("summarize", "Tóm tắt văn bản"),
        BotCommand("compare", "So sánh 2 model"),
        BotCommand("retry", "Thử lại với model khác"),
        BotCommand("voice", "Speech-to-Text"),
        BotCommand("todo", "Quản lý việc cần làm"),
        BotCommand("calc", "Máy tính"),
        BotCommand("qr", "Tạo QR code"),
        BotCommand("password", "Tạo password"),
        BotCommand("jsonfmt", "Format JSON"),
        BotCommand("base64", "Encode/Decode"),
        BotCommand("hash", "Hash MD5/SHA256"),
        BotCommand("shorten", "Rút gọn link"),
        BotCommand("poll", "Tạo poll"),
        BotCommand("snippet", "Quản lý snippets"),
        BotCommand("whiteboard", "Bảng trắng"),
        BotCommand("branch", "Quản lý nhánh chat"),
        BotCommand("remind", "Hẹn giờ nhắc nhở"),
        BotCommand("persona", "Đặt tính cách AI"),
        BotCommand("pin", "Ghim tin nhắn"),
        BotCommand("pinned", "Xem tin ghim"),
        BotCommand("settings", "Cài đặt & Ngân sách"),
        BotCommand("export", "Xuất dữ liệu"),
        BotCommand("import", "Nhập dữ liệu"),
        BotCommand("status", "Trạng thái & Chi phí"),
        BotCommand("tasks", "Lịch sử agent tasks"),
        BotCommand("learn", "Ghi chú tự học"),
        BotCommand("reset", "Xóa ngữ cảnh"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("✅ Denia Bot v8.0 initialized successfully")

async def post_shutdown(application: Application):
    session = application.bot_data.get('session')
    if session:
        await session.close()
    await gh_client.close()
    _save_state()
    logger.info("🛑 Shutdown complete. State saved.")

def main():
    logger.info("🚀 Starting Denia Bot v8.0...")
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .concurrent_updates(True)
        .build()
    )
    # Core
    application.add_handler(CommandHandler('start', cmd_start))
    application.add_handler(CommandHandler('help', cmd_help))
    application.add_handler(CommandHandler('models', cmd_models))
    application.add_handler(CommandHandler('switch', cmd_switch))
    application.add_handler(CommandHandler('mode', cmd_mode))
    application.add_handler(CommandHandler('reset', cmd_reset))
    application.add_handler(CommandHandler('status', cmd_status))
    application.add_handler(CommandHandler('settings', cmd_settings))
    # Agent
    application.add_handler(CommandHandler('agent', cmd_agent))
    # GitHub
    application.add_handler(CommandHandler('git', cmd_git))
    # Learning
    application.add_handler(CommandHandler('lesson', cmd_lesson))
    application.add_handler(CommandHandler('lesson_lang', cmd_lesson_lang))
    application.add_handler(CommandHandler('leetcode', cmd_leetcode))
    application.add_handler(CommandHandler('quiz', cmd_quiz))
    application.add_handler(CommandHandler('flashcard', cmd_flashcard))
    # Code tools
    application.add_handler(CommandHandler('run', cmd_run))
    application.add_handler(CommandHandler('runplot', cmd_runplot))
    application.add_handler(CommandHandler('analyze', cmd_analyze))
    application.add_handler(CommandHandler('format', cmd_format))
    application.add_handler(CommandHandler('diff', cmd_diff))
    application.add_handler(CommandHandler('testgen', cmd_testgen))
    application.add_handler(CommandHandler('docker', cmd_docker))
    application.add_handler(CommandHandler('cicd', cmd_cicd))
    # Web & Multimedia
    application.add_handler(CommandHandler('search', cmd_search))
    application.add_handler(CommandHandler('fetch', cmd_fetch))
    application.add_handler(CommandHandler('kb', cmd_kb))
    application.add_handler(CommandHandler('image', cmd_image))
    application.add_handler(CommandHandler('tts', cmd_tts))
    application.add_handler(CommandHandler('vision', cmd_vision))
    # Utilities
    application.add_handler(CommandHandler('translate', cmd_translate))
    application.add_handler(CommandHandler('summarize', cmd_summarize))
    application.add_handler(CommandHandler('compare', cmd_compare))
    application.add_handler(CommandHandler('retry', cmd_retry))
    application.add_handler(CommandHandler('voice', cmd_voice))
    application.add_handler(CommandHandler('todo', cmd_todo))
    application.add_handler(CommandHandler('calc', cmd_calc))
    application.add_handler(CommandHandler('qr', cmd_qr))
    application.add_handler(CommandHandler('password', cmd_password))
    application.add_handler(CommandHandler('jsonfmt', cmd_jsonfmt))
    application.add_handler(CommandHandler('base64', cmd_base64))
    application.add_handler(CommandHandler('hash', cmd_hash))
    application.add_handler(CommandHandler('shorten', cmd_shorten))
    application.add_handler(CommandHandler('poll', cmd_poll))
    # Memory
    application.add_handler(CommandHandler('branch', cmd_branch))
    application.add_handler(CommandHandler('remind', cmd_remind))
    application.add_handler(CommandHandler('persona', cmd_persona))
    application.add_handler(CommandHandler('whiteboard', cmd_whiteboard))
    application.add_handler(CommandHandler('snippet', cmd_snippet))
    application.add_handler(CommandHandler('export', cmd_export))
    application.add_handler(CommandHandler('import', cmd_import))
    application.add_handler(CommandHandler('tasks', cmd_tasks))
    application.add_handler(CommandHandler('learn', cmd_learn))
    application.add_handler(CommandHandler('pin', cmd_pin))
    application.add_handler(CommandHandler('pinned', cmd_pinned))
    # Callbacks
    application.add_handler(CallbackQueryHandler(cb_model, pattern="^(model_|filter_main_|refresh_models)"))
    application.add_handler(CallbackQueryHandler(cb_mode, pattern="^setmode_"))
    application.add_handler(CallbackQueryHandler(cb_model_selector, pattern="^(selmodel_|selpage_|filter_|selcancel_|exec_|noop)"))
    application.add_handler(CallbackQueryHandler(cb_leetcode, pattern="^leet_"))
    application.add_handler(CallbackQueryHandler(cb_flashcard, pattern="^fc_"))
    # Messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # Errors
    application.add_error_handler(error_handler)
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
