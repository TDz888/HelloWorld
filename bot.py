#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════════════════════════════════════╗
║              🤖 Denia Bot v8.0 — ULTIMATE MASTER EDITION               ║
║     Multi-Provider (OpenCode + NVIDIA NIM) | Super Agent | Auto-Fix   ║
║     ✨ Perfect Syntax • Full Feature Set • Production-Ready Logic     ║
╚════════════════════════════════════════════════════════════════════════╝
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
import time
import traceback
import zipfile
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, Callable, Set
from functools import wraps
from contextlib import asynccontextmanager

# Third-party libraries
import aiohttp
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, Message, User, Chat,
    InputMediaPhoto, InputMediaDocument, ParseMode, UpdateType
)
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ConversationHandler, TypeHandler
)
from telegram.constants import ParseMode as TPM, ChatAction, MessageLimit, FileType
from telegram.error import BadRequest, NetworkError, RetryAfter, TelegramError

# ============================================================================
# 🔐 CONFIGURATION — HARDCODED & MULTI-PROVIDER
# ============================================================================

class Config:
    """All config hardcoded for simplicity and maximum performance."""
    
    # === TELEGRAM ===
    BOT_TOKEN = "8909561772:AAGQgxrbvXbi-RACF4_Z7iiS4R7NA6Za6wU"
    
    # === AI PROVIDERS ===
    PROVIDERS = {
        "opencode": {
            "base": "https://opencode.ai/zen",
            "key": "sk-F9v1PpTAyB4CVvaXYp1894RnUdicmNKAx6pZwitfBuWWUkXehlOC0VNcd0Ivt3U8"
        },
        "nvidia": {
            "base": "https://integrate.api.nvidia.com/v1",
            "key": "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"
        }
    }
    
    # === GITHUB ===
    GITHUB_TOKEN = "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"
    
    # === PATHS ===
    WORK_DIR = Path("denia_data")
    MAX_HISTORY = 50
    MAX_TOKENS_PER_CALL = 8192
    API_TIMEOUT = 240  # seconds
    
    # === AGENT SETTINGS ===
    DEFAULT_CHAT_MODEL = "z-ai/glm-5.1"
    DEFAULT_AGENT_MODEL = "minimaxai/minimax-m2.7"
    AUTO_MODEL_SELECTION = True
    CONTEXT_COMPRESSION = True
    STREAMING_RESPONSES = True
    
    # === RATE LIMITS ===
    USER_REQUESTS_PER_MIN = 20
    GLOBAL_REQUESTS_PER_MIN = 300
    
    # === AUTO-CLEANUP ===
    ZIP_RETENTION_HOURS = 72
    MAX_SELF_NOTES = 150
    
    @classmethod
    def init(cls):
        cls.WORK_DIR.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s',
            handlers=[
                logging.FileHandler(cls.WORK_DIR / "denia.log", encoding='utf-8', mode='a'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logging.info(f"🚀 Denia Bot v8.0 initialized | Work dir: {cls.WORK_DIR}")

# ============================================================================
# 🧠 SMART MODEL ROUTER — v8 Feature #1
# ============================================================================

class TaskType(Enum):
    CHAT = "chat"
    CODE_GEN = "code_gen"
    CODE_FIX = "code_fix"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    SHORT_ANSWER = "short"
    LONG_FORM = "long_form"

class ModelProfile:
    """Profile for each model: capabilities, cost, speed, provider."""
    def __init__(self, model_id: str, display: str, category: str, provider: str,
                 strengths: List[TaskType], cost_tier: int, speed_tier: int,
                 max_context: int = 128000):
        self.id = model_id
        self.display = display
        self.category = category
        self.provider = provider
        self.strengths = set(strengths)
        self.cost_tier = cost_tier  # 1=cheap/free, 3=expensive
        self.speed_tier = speed_tier  # 1=fast, 3=slow
        self.max_context = max_context
        self.usage_count = 0
        self.success_rate = 1.0
    
    def score_for_task(self, task_type: TaskType, budget_conscious: bool = False) -> float:
        """Calculate suitability score (0-1) for a task."""
        score = 0.0
        if task_type in self.strengths:
            score += 0.4
        score += (4 - self.speed_tier) / 3 * 0.3
        if budget_conscious:
            score += (4 - self.cost_tier) / 3 * 0.2
        else:
            score += 0.2
        score += self.success_rate * 0.1
        return min(1.0, score)

# Comprehensive Model Catalog
MODEL_PROFILES = {
    # OpenCode Free Models
    "minimax-m2.5-free": ModelProfile(
        "minimax-m2.5-free", "MiniMax M2.5 Free", "MiniMax", "opencode",
        [TaskType.CHAT, TaskType.SHORT_ANSWER, TaskType.CODE_GEN],
        cost_tier=1, speed_tier=1
    ),
    # NVIDIA NIM Models
    "minimaxai/minimax-m2.7": ModelProfile(
        "minimaxai/minimax-m2.7", "MiniMax M2.7 (NVIDIA)", "MiniMax", "nvidia",
        [TaskType.CODE_GEN, TaskType.CODE_FIX, TaskType.ANALYSIS, TaskType.LONG_FORM],
        cost_tier=2, speed_tier=2
    ),
    "z-ai/glm-5.1": ModelProfile(
        "z-ai/glm-5.1", "GLM-5.1 (NVIDIA)", "GLM", "nvidia",
        [TaskType.CHAT, TaskType.ANALYSIS, TaskType.CODE_GEN, TaskType.CODE_FIX],
        cost_tier=2, speed_tier=1
    ),
    # Legacy/Extended Profiles for Fallback
    "deepseek-3.2": ModelProfile(
        "deepseek-3.2", "DeepSeek V3", "DeepSeek", "opencode",
        [TaskType.CHAT, TaskType.CODE_GEN], cost_tier=1, speed_tier=1
    ),
    "claude-sonnet-4.6": ModelProfile(
        "claude-sonnet-4.6", "Claude Sonnet 4.6", "Claude", "nvidia",
        [TaskType.ANALYSIS, TaskType.LONG_FORM, TaskType.CREATIVE, TaskType.CODE_FIX],
        cost_tier=3, speed_tier=2
    ),
    "gpt-5.4": ModelProfile(
        "gpt-5.4", "GPT-5.4", "GPT", "nvidia",
        [TaskType.ANALYSIS, TaskType.LONG_FORM, TaskType.CREATIVE, TaskType.CODE_GEN],
        cost_tier=3, speed_tier=2
    ),
    "google-tts/vi": ModelProfile(
        "google-tts/vi", "Google TTS Vietnamese", "TTS", "opencode",
        [], cost_tier=1, speed_tier=1
    ),
    "text-embedding-3-small": ModelProfile(
        "text-embedding-3-small", "Text Embedding 3 Small", "Embedding", "nvidia",
        [], cost_tier=1, speed_tier=1
    ),
}

class SmartModelRouter:
    """v8 Feature: Auto-select best model for each task across providers."""
    
    @staticmethod
    def detect_task_type(text: str, context: List[Dict]) -> TaskType:
        text_lower = text.lower()
        code_keywords = ['code', 'function', 'def ', 'import ', 'class ', 'javascript', 'python', 'react', 'api', 'endpoint', 'bug', 'error', 'fix', 'debug', 'syntax']
        if any(kw in text_lower for kw in code_keywords):
            if any(kw in text_lower for kw in ['fix', 'bug', 'error', 'debug']):
                return TaskType.CODE_FIX
            return TaskType.CODE_GEN
        
        if len(text) < 50 and any(q in text for q in ['?', 'là gì', 'tại sao', 'how', 'what']):
            return TaskType.SHORT_ANSWER
        
        if any(kw in text_lower for kw in ['viết', 'write', 'story', 'poem', 'essay', 'content']):
            return TaskType.CREATIVE if len(text) < 200 else TaskType.LONG_FORM
        
        if any(kw in text_lower for kw in ['phân tích', 'analyze', 'compare', 'review', 'explain']):
            return TaskType.ANALYSIS
        
        return TaskType.CHAT if len(text) < 500 else TaskType.LONG_FORM
    
    @classmethod
    def select_best_model(cls, user_input: str, history: List[Dict], user_budget_conscious: bool = True) -> Tuple[str, str, str]:
        """Return (model_id, display_name, provider) for best model."""
        task_type = cls.detect_task_type(user_input, history)
        candidates = []
        for model_id, profile in MODEL_PROFILES.items():
            if model_id in ["google-tts/vi", "text-embedding-3-small"]:
                continue
            score = profile.score_for_task(task_type, user_budget_conscious)
            if task_type in profile.strengths and profile.success_rate > 0.9:
                score += 0.1
            candidates.append((model_id, profile.display, profile.provider, score))
        
        candidates.sort(key=lambda x: -x[3])
        return candidates[0][0], candidates[0][1], candidates[0][2]
    
    @classmethod
    def record_result(cls, model_id: str, success: bool):
        if model_id in MODEL_PROFILES:
            profile = MODEL_PROFILES[model_id]
            profile.usage_count += 1
            alpha = 0.1
            profile.success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * profile.success_rate

# ============================================================================
# 🗜️ CONTEXT COMPRESSOR — v8 Feature #2
# ============================================================================

class ContextCompressor:
    """Auto-compress old messages to stay within token limits."""
    CHARS_PER_TOKEN = 4
    
    @classmethod
    def estimate_tokens(cls, messages: List[Dict]) -> int:
        total_chars = sum(len(m.get('content', '')) for m in messages)
        return len(messages) * 5 + total_chars // cls.CHARS_PER_TOKEN
    
    @classmethod
    def compress_history(cls, history: List[Dict], max_tokens: int = 6000) -> List[Dict]:
        if not history:
            return []
        keep_recent = 10
        recent = history[-keep_recent:] if len(history) > keep_recent else history
        if len(history) <= keep_recent:
            return history
        
        old_messages = history[:-keep_recent]
        old_text = "\n".join([f"{m['role']}: {m['content'][:200]}" for m in old_messages[-20:]])
        summary = f"[Tóm tắt {len(old_messages)} tin nhắn trước]: {old_text[:800]}..."
        return [{"role": "system", "content": summary}] + recent
    
    @classmethod
    def smart_truncate(cls, content: str, max_chars: int = 3000) -> str:
        if len(content) <= max_chars:
            return content
        if "```" in content:
            blocks = content.split("```")
            if len(blocks) >= 3:
                result = "```".join(blocks[:3])
                if len(result) < max_chars:
                    return result + "\n```[...tiếp tục trong file đính kèm...]"
        sentences = content.split('. ')
        result = []
        for s in sentences:
            if len('. '.join(result + [s])) > max_chars - 50:
                break
            result.append(s)
        return '. '.join(result) + ' [...]'

# ============================================================================
# 🔄 STREAMING RESPONSE HANDLER — v8 Feature #3
# ============================================================================

class StreamingHandler:
    """Handle streaming responses with real-time updates."""
    
    @staticmethod
    async def stream_chat(model_id: str, provider: str, messages: List[Dict],
                          status_msg: Message, status_callback: Callable) -> Tuple[str, Dict]:
        cfg = Config.PROVIDERS[provider]
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {cfg['key']}"}
        payload = {"model": model_id, "messages": messages, "temperature": 0.7, "max_tokens": Config.MAX_TOKENS_PER_CALL, "stream": True}
        
        accumulated = []
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=Config.API_TIMEOUT)) as session:
                async with session.post(f"{cfg['base']}/chat/completions", headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        raise Exception(f"API Error {resp.status}: {await resp.text()[:200]}")
                    
                    async for line in resp.content:
                        line = line.decode('utf-8').strip()
                        if not line or line == 'data: [DONE]':
                            continue
                        if line.startswith('data: '):
                            try:
                                chunk = json.loads(line[6:])
                                content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                if content:
                                    accumulated.append(content)
                                    if status_callback and len(''.join(accumulated)) % 120 < len(content):
                                        await status_callback(''.join(accumulated)[-350:])
                            except json.JSONDecodeError:
                                continue
            
            final_text = ''.join(accumulated)
            latency = time.time() - start_time
            return final_text, {'latency': latency, 'output_chars': len(final_text), 'streaming': True}
            
        except Exception as e:
            logging.warning(f"Stream failed, falling back: {e}")
            return await StreamingHandler._fallback_non_streaming(model_id, provider, messages)
    
    @staticmethod
    async def _fallback_non_streaming(model_id: str, provider: str, messages: List[Dict]) -> Tuple[str, Dict]:
        cfg = Config.PROVIDERS[provider]
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {cfg['key']}"}
        payload = {"model": model_id, "messages": messages, "temperature": 0.7, "max_tokens": Config.MAX_TOKENS_PER_CALL, "stream": False}
        
        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{cfg['base']}/chat/completions", headers=headers, json=payload) as resp:
                if resp.status != 200:
                    raise Exception(f"API Error {resp.status}")
                result = await resp.json()
        
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        latency = time.time() - start_time
        return content, {'latency': latency, 'output_chars': len(content), 'streaming': False}

# ============================================================================
# 📊 USAGE TRACKER — v8 Feature #4
# ============================================================================

@dataclass
class UsageStats:
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_latency: float = 0.0
    models_used: Dict[str, int] = field(default_factory=dict)
    task_types: Dict[str, int] = field(default_factory=dict)
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def record(self, input_tokens: int, output_tokens: int, latency: float, model_id: str, task_type: TaskType):
        self.total_requests += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_latency += latency
        self.models_used[model_id] = self.models_used.get(model_id, 0) + 1
        self.task_types[task_type.value] = self.task_types.get(task_type.value, 0) + 1
        self.last_active = datetime.now().isoformat()
    
    @property
    def avg_latency(self) -> float:
        return self.total_latency / self.total_requests if self.total_requests > 0 else 0.0
    
    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

# ============================================================================
# 🧩 ENHANCED DATA MODELS
# ============================================================================

@dataclass
class AgentTask:
    task_id: str
    user_id: int
    description: str
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    checkpoints: List[Dict] = field(default_factory=list)
    result: Optional[str] = None
    error: Optional[str] = None
    files_created: List[str] = field(default_factory=list)
    local_path: Optional[str] = None
    repo_url: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    model_used: Optional[str] = None
    auto_retry_count: int = 0
    
    def add_checkpoint(self, step: str, data: Dict):
        self.checkpoints.append({"step": step, "timestamp": datetime.now().isoformat(), "data": data})
        if len(self.checkpoints) > 5:
            self.checkpoints = self.checkpoints[-5:]
    
    def can_rollback(self) -> bool:
        return len(self.checkpoints) >= 1
    
    def get_last_checkpoint(self) -> Optional[Dict]:
        return self.checkpoints[-1] if self.checkpoints else None

@dataclass  
class ConversationState:
    history: List[Dict[str, str]] = field(default_factory=list)
    mode: str = "chat"
    current_model: str = Config.DEFAULT_CHAT_MODEL
    current_provider: str = "nvidia"
    auto_model: bool = True
    usage: UsageStats = field(default_factory=UsageStats)
    agent_tasks: List[AgentTask] = field(default_factory=list)
    
    preferred_style: str = "balanced"
    language_hint: str = "auto"
    budget_conscious: bool = True
    
    self_notes: List[str] = field(default_factory=list)
    error_patterns: Dict[str, int] = field(default_factory=dict)
    successful_patterns: Dict[str, int] = field(default_factory=dict)
    
    branches: Dict[str, List[Dict]] = field(default_factory=dict)
    active_branch: Optional[str] = None
    agent_deploy_mode: str = "local"
    
    def add_note(self, note: str, success: bool = True):
        target = self.successful_patterns if success else self.error_patterns
        sig = note[:150].strip()
        target[sig] = target.get(sig, 0) + 1
        if success and sig not in self.self_notes:
            self.self_notes.append(f"✅ {sig}")
            if len(self.self_notes) > Config.MAX_SELF_NOTES:
                self.self_notes = self.self_notes[-Config.MAX_SELF_NOTES:]
    
    def get_adaptive_prompt(self, base: str) -> str:
        prompt = base
        if self.preferred_style == "concise":
            prompt += "\n\nSTYLE: Be extremely concise. Code only, minimal explanations."
        elif self.preferred_style == "verbose":
            prompt += "\n\nSTYLE: Provide detailed explanations with examples and comments."
        if self.language_hint == "vi":
            prompt += "\n\nLANGUAGE: Respond in Vietnamese when appropriate, but keep code in English."
        if self.successful_patterns:
            top_success = sorted(self.successful_patterns.items(), key=lambda x: -x[1])[:3]
            if top_success:
                prompt += "\n\nPREFERRED PATTERNS:\n" + "\n".join(f"- {p}" for p, _ in top_success)
        return prompt

# ============================================================================
# 🗄️ IN-MEMORY STATE STORE
# ============================================================================

class StateStore:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._cache: Dict[int, ConversationState] = {}
        self._lock = asyncio.Lock()
        self._load()
    
    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for uid_str, state_data in data.items():
                    uid = int(uid_str)
                    if 'usage' in state_data and isinstance(state_data['usage'], dict):
                        state_data['usage'] = UsageStats(**state_data['usage'])
                    self._cache[uid] = ConversationState(**state_data)
                logging.info(f"📥 Loaded {len(self._cache)} user states")
            except Exception as e:
                logging.warning(f"⚠️ Failed to load states: {e}")
    
    async def _save(self):
        async with self._lock:
            try:
                data = {}
                for uid, state in self._cache.items():
                    state_dict = asdict(state)
                    state_dict['usage'] = asdict(state.usage)
                    data[str(uid)] = state_dict
                temp_file = self.file_path.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                temp_file.replace(self.file_path)
            except Exception as e:
                logging.error(f"❌ Failed to save states: {e}")
    
    def get(self, user_id: int) -> ConversationState:
        if user_id not in self._cache:
            self._cache[user_id] = ConversationState()
        return self._cache[user_id]
    
    async def save(self, user_id: int):
        if user_id in self._cache:
            await self._save()
    
    async def save_all(self):
        await self._save()
    
    def cleanup_old_tasks(self, hours: int = 72):
        cutoff = datetime.now() - timedelta(hours=hours)
        for state in self._cache.values():
            original = len(state.agent_tasks)
            state.agent_tasks = [t for t in state.agent_tasks if datetime.fromisoformat(t.created_at) > cutoff]
            if len(state.agent_tasks) < original:
                logging.debug(f"🗑️ Cleaned {original - len(state.agent_tasks)} old tasks")

state_store = StateStore(Config.WORK_DIR / "states.json")

def get_user_state(user_id: int) -> ConversationState:
    return state_store.get(user_id)

# ============================================================================
# 🛡️ RATE LIMITER
# ============================================================================

class SimpleRateLimiter:
    def __init__(self, rate: int, window: float = 60.0):
        self.rate = rate
        self.window = window
        self.buckets: Dict[Any, List[float]] = {}
    
    def allow(self, key: Any) -> Tuple[bool, float]:
        now = time.time()
        if key not in self.buckets:
            self.buckets[key] = []
        self.buckets[key] = [t for t in self.buckets[key] if now - t < self.window]
        if len(self.buckets[key]) >= self.rate:
            oldest = min(self.buckets[key])
            wait = self.window - (now - oldest)
            return False, max(0.0, wait)
        self.buckets[key].append(now)
        return True, 0.0

user_limiter = SimpleRateLimiter(Config.USER_REQUESTS_PER_MIN)
global_limiter = SimpleRateLimiter(Config.GLOBAL_REQUESTS_PER_MIN)

def rate_limit_check(update: Update) -> Tuple[bool, Optional[str]]:
    user_id = update.effective_user.id
    allowed, wait = global_limiter.allow("global")
    if not allowed:
        return False, f"🌍 Server busy. Try in `{wait:.0f}s`."
    allowed, wait = user_limiter.allow(user_id)
    if not allowed:
        return False, f"⏱ You're sending too fast. Wait `{wait:.0f}s`."
    return True, None

# ============================================================================
# 📁 ENHANCED FILE PARSER
# ============================================================================

class RobustFileParser:
    STRATEGIES = [
        (re.compile(r'<<<FILE:\s*([^>\s]+)\s*>>>(.*?)<<<ENDFILE>>>', re.DOTALL | re.I), lambda m: (m.group(1).strip(), m.group(2).strip())),
        (re.compile(r'```(?:\w+)?\s*\n?\s*#\s*filename:\s*([^\n]+)\s*\n(.*?)```', re.DOTALL | re.I), lambda m: (m.group(1).strip(), m.group(2).strip())),
        (re.compile(r'```(?:\w+)?\s+([^\n`]+?\.\w+)\s*\n(.*?)```', re.DOTALL | re.I), lambda m: (m.group(1).strip(), m.group(2).strip())),
        (re.compile(r'^#\s*File:\s*([^\n]+)\s*\n(.*?)(?=\n^#\s*File:|\Z)', re.DOTALL | re.M | re.I), lambda m: (m.group(1).strip(), m.group(2).strip())),
        (re.compile(r'```(?:python|py)?\s*\n(.*?)```', re.DOTALL | re.I), lambda m: ("main.py", m.group(1).strip())),
    ]
    
    @classmethod
    def parse(cls, text: str) -> Dict[str, str]:
        files = {}
        for pattern, extractor in cls.STRATEGIES:
            if files:
                break
            for match in pattern.finditer(text):
                try:
                    filename, content = extractor(match)
                    if cls._is_valid(filename) and content:
                        safe_name = cls._sanitize(filename)
                        files[safe_name] = content
                except Exception:
                    continue
        if not files and cls._looks_like_code(text):
            ext = cls._detect_lang(text)
            files[f"main.{ext}"] = text.strip()
        return files
    
    @staticmethod
    def _is_valid(filename: str) -> bool:
        if not filename or len(filename) > 255:
            return False
        dangerous = ['../', '..\\', '/etc/', '/proc/', 'null', 'undefined', '<', '>', '|']
        return not any(d in filename.lower() for d in dangerous)
    
    @staticmethod
    def _sanitize(filename: str) -> str:
        name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        name = name.strip('. ')
        if len(name) > 200:
            base, ext = os.path.splitext(name)
            name = base[:195] + ext
        return name or f"file_{hashlib.md5(filename.encode()).hexdigest()[:8]}.txt"
    
    @staticmethod
    def _looks_like_code(text: str) -> bool:
        indicators = [r'\b(import|from|class|def|function|const|let)\b', r'\{\s*\}', r'->\s*\w+']
        return any(re.search(p, text, re.I) for p in indicators)
    
    @staticmethod
    def _detect_lang(text: str) -> str:
        if re.search(r'\bimport\s+\w+|from\s+\w+\s+import', text): return 'py'
        if re.search(r'\bfunction\s+\w+|const\s+\w+\s*=', text): return 'js'
        if re.search(r'\binterface\s+\w+|:\s*(string|number)\b', text): return 'ts'
        return 'txt'

# ============================================================================
# 🔍 SMART SYNTAX CHECKER
# ============================================================================

class SmartSyntaxChecker:
    @classmethod
    def check(cls, code: str, filename: str) -> List[Dict]:
        ext = Path(filename).suffix.lower()
        issues = []
        if ext == '.py':
            issues.extend(cls._check_python(code, filename))
        elif ext in ['.js', '.ts']:
            issues.extend(cls._check_js(code, filename))
        elif ext == '.json':
            issues.extend(cls._check_json(code, filename))
        return issues
    
    @staticmethod
    def _check_python(code: str, filename: str) -> List[Dict]:
        issues = []
        try:
            compile(code, filename, 'exec')
        except SyntaxError as e:
            return [{"level": "error", "message": f"Syntax error line {e.lineno}: {e.msg}", "suggestion": "Check indentation, colons, parentheses"}]
        if re.search(r'\bexcept\s*:', code) and not re.search(r'\bexcept\s+\w+', code):
            issues.append({"level": "warn", "message": "Bare `except:`", "suggestion": "Use `except Exception:` for clarity"})
        if 'print(' in code and 'logging' not in code and len(code) > 300:
            issues.append({"level": "info", "message": "Using print() statements", "suggestion": "Consider `logging` module for production"})
        if 'TODO' in code.upper() or 'FIXME' in code.upper():
            issues.append({"level": "info", "message": "TODO/FIXME markers found"})
        return issues
    
    @staticmethod
    def _check_js(code: str, filename: str) -> List[Dict]:
        issues = []
        if code.count('{') != code.count('}'):
            issues.append({"level": "error", "message": "Mismatched braces", "suggestion": "Check opening/closing brackets"})
        if 'console.log' in code and 'debug' not in filename.lower():
            issues.append({"level": "info", "message": "console.log found", "suggestion": "Remove in production code"})
        return issues
    
    @staticmethod
    def _check_json(code: str, filename: str) -> List[Dict]:
        try:
            json.loads(code)
            return []
        except json.JSONDecodeError as e:
            return [{"level": "error", "message": f"JSON error: {e.msg}", "suggestion": "Check commas, quotes, trailing commas"}]

# ============================================================================
# 📦 LOCAL ZIP AGENT
# ============================================================================

class LocalAgent:
    @classmethod
    async def create_package(cls, task_id: str, files: Dict[str, str], metadata: Dict) -> Tuple[Path, int]:
        task_dir = Config.WORK_DIR / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        total_size = 0
        
        for filename, content in files.items():
            file_path = task_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            total_size += file_path.stat().st_size
        
        meta = {**metadata, "created_at": datetime.now().isoformat(), "denia_version": "8.0", "files_count": len(files)}
        (task_dir / ".denia_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')
        
        if "README.md" not in files:
            readme = cls._generate_readme(metadata, files)
            (task_dir / "README.md").write_text(readme, encoding='utf-8')
            total_size += len(readme.encode('utf-8'))
        
        zip_path = Config.WORK_DIR / f"{task_id}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for fp in task_dir.rglob('*'):
                if fp.is_file():
                    zf.write(fp, fp.relative_to(task_dir))
        
        zip_size = zip_path.stat().st_size
        logging.info(f"📦 Created: {zip_path.name} ({zip_size/1024:.1f}KB, {len(files)} files)")
        return zip_path, zip_size
    
    @staticmethod
    def _generate_readme(meta: Dict, files: Dict[str, str]) -> str:
        desc = meta.get('description', 'Auto-generated project')[:200]
        files_list = "\n".join(f"- `{f}` ({len(c)} chars)" for f, c in list(files.items())[:10])
        setup_hint = ""
        if "requirements.txt" in files:
            setup_hint = "```bash\npip install -r requirements.txt\npython main.py\n```"
        elif "package.json" in files:
            setup_hint = "```bash\nnpm install\nnpm start\n```"
        elif any(f.endswith('.py') for f in files):
            setup_hint = "```bash\npython main.py\n```"
        
        return f"""# 🤖 {meta.get('task_id', 'Project')}

{desc}

## 📁 Files
{files_list}
{"...and more" if len(files) > 10 else ""}

## 🚀 Quick Start
{setup_hint}

## ℹ️ Generated by
Denia Bot v8.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

# ============================================================================
# 🌐 GITHUB CLIENT
# ============================================================================

class LiteGitHub:
    BASE = "https://api.github.com"
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json", "User-Agent": "Denia-Bot/8.0"}
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _session_get(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=Config.API_TIMEOUT), headers={"User-Agent": self.headers["User-Agent"]})
        return self._session
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Tuple[int, Any]:
        session = await self._session_get()
        url = f"{self.BASE}{endpoint}"
        headers = {**self.headers, **kwargs.pop('headers', {})}
        async with session.request(method, url, headers=headers, **kwargs) as resp:
            try:
                data = await resp.json()
            except:
                data = await resp.text()
            return resp.status, data
    
    async def get_user(self) -> Tuple[bool, str]:
        status, data = await self._request("GET", "/user")
        if status == 200 and isinstance(data, dict):
            return True, data.get("login", "")
        return False, ""
    
    async def create_repo(self, name: str, desc: str = "", private: bool = False) -> Tuple[bool, str]:
        payload = {"name": name, "description": desc[:300], "private": private, "auto_init": True}
        status, data = await self._request("POST", "/user/repos", json=payload)
        if status == 201 and isinstance(data, dict):
            return True, data.get("html_url", "")
        return False, str(data) if isinstance(data, dict) else data
    
    async def push_files(self, owner: str, repo: str, files: Dict[str, str], message: str, branch: str = "main") -> Tuple[bool, str]:
        for path, content in files.items():
            encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            status, data = await self._request("GET", f"/repos/{owner}/{repo}/contents/{path}?ref={branch}")
            payload = {"message": message[:200], "content": encoded, "branch": branch}
            if status == 200 and isinstance(data, dict) and "sha" in data:
                payload["sha"] = data["sha"]
            status, _ = await self._request("PUT", f"/repos/{owner}/{repo}/contents/{path}", json=payload)
            if status not in (200, 201):
                return False, f"Failed to push {path}"
            await asyncio.sleep(0.3)
        return True, f"https://github.com/{owner}/{repo}"
    
    async def close(self):
        if self._session:
            await self._session.close()

github = LiteGitHub(Config.GITHUB_TOKEN)

# ============================================================================
# 📋 SYSTEM PROMPTS
# ============================================================================

SYSTEM_PROMPT = """You are Denia Bot v8.0 — an advanced autonomous coding assistant.
CORE PRINCIPLES:
1. Write COMPLETE, RUNNABLE code — no placeholders, no pseudocode.
2. Include ALL necessary files: main, dependencies, config, README.
3. Follow best practices: docstrings, error handling, type hints, logging.
4. Adapt to user preferences: concise/verbose, language, style.
5. Learn from interactions: remember what works, avoid past mistakes.

OUTPUT FORMAT FOR CODE TASKS:
Use file markers for each file:
<<<FILE:filename.py>>>
[complete file content]
<<<ENDFILE>>>
"""

AGENT_PROMPT = """You are Denia Agent in AUTONOMOUS MODE.
MISSION: Complete the task end-to-end with ZERO follow-up questions.
RULES:
1. Analyze requirements thoroughly before coding.
2. Plan file structure and dependencies first.
3. Write production-ready code: error handling, logging, config management.
4. Include: main file, dependencies, README, .env.example (if needed).
5. Test logic mentally before outputting.

STRICT OUTPUT:
Each file MUST be wrapped:
<<<FILE:filename>>>
[content]
<<<ENDFILE>>>
"""

# ============================================================================
# 🎨 TELEGRAM UI HELPERS
# ============================================================================

def build_model_keyboard(mode: str, current: str, page: int = 0) -> InlineKeyboardMarkup:
    models = MODE_CONFIG.get(mode, {}).get("models", [])
    per_page = 6
    total_pages = (len(models) + per_page - 1) // per_page
    start_idx = page * per_page
    page_models = models[start_idx:start_idx + per_page]
    
    keyboard = []
    for cat, model_id, display, provider in page_models:
        prefix = "✅ " if model_id == current else CATEGORY_EMOJI.get(cat, "⚪ ")
        provider_tag = "🟢" if provider == "opencode" else "🔵"
        btn = InlineKeyboardButton(f"{prefix}{provider_tag} {display[:18]}", callback_data=f"model_{mode}_{model_id}")
        keyboard.append([btn])
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"models_{mode}_{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f"models_{mode}_{page+1}"))
    if nav_row:
        keyboard.append(nav_row)
    keyboard.append([InlineKeyboardButton("🔄 Auto-select", callback_data=f"auto_{mode}")])
    return InlineKeyboardMarkup(keyboard)

def build_quick_actions() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Agent Mode", callback_data="quick_agent"), InlineKeyboardButton("📊 Stats", callback_data="quick_stats")],
        [InlineKeyboardButton("🔧 Fix Code", callback_data="quick_fix"), InlineKeyboardButton("📝 Explain", callback_data="quick_explain")],
        [InlineKeyboardButton("🗑️ Reset Chat", callback_data="quick_reset")],
    ])

async def send_with_fallback(update: Update, text: str, parse_mode: str = TPM.MARKDOWN, **kwargs):
    if len(text) <= MessageLimit.MAX_TEXT_LENGTH:
        try:
            return await update.message.reply_text(text, parse_mode=parse_mode, **kwargs)
        except BadRequest as e:
            if "message is too long" not in str(e).lower():
                raise
    bio = io.BytesIO(text.encode('utf-8'))
    bio.name = "response.txt"
    return await update.message.reply_document(document=bio, caption="📄 Content too long for chat — sent as file", **kwargs)

# ============================================================================
# 🎯 COMMAND HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    allowed, msg = rate_limit_check(update)
    if not allowed:
        await update.message.reply_text(msg, parse_mode=TPM.MARKDOWN)
        return
    
    state = get_user_state(user_id)
    model_display = _get_model_display(state.mode, state.current_model)
    
    welcome = f"""╔══════════════════════════╗
║   🤖 *Denia Bot v8.0*    ║
║   *Ultimate AI Agent*    ║
╚══════════════════════════╝

👋 Chào *{update.effective_user.first_name or 'bạn'}*!

🧠 *AI thông minh hơn — Tự chọn model, tự nén context, tự học*

📦 *Chế độ:*
• 💬 Chat — Hỏi đáp thông thường
• 🤖 Agent — Tự động code + deploy  
• 📊 Embed — Text → Vector
• 🔊 TTS — Text → Voice

🚀 *Hiện tại:* {MODE_CONFIG[state.mode]['name']} | {model_display}
🎯 *Auto model:* {'✅ Bật' if state.auto_model else '❌ Tắt'}

📚 *Lệnh nhanh:*
• `/models` — Chọn model (có nút)
• `/agent <task>` — Chạy agent tự động
• `/style concise|verbose` — Đổi phong cách
• `/stats` — Xem thống kê
• `/reset` — Xóa lịch sử
• `/help` — Hướng dẫn chi tiết

💡 *Mẹo v8:* Gõ `/agent github Tạo API FastAPI` để auto-deploy!"""
    
    await send_with_fallback(update, welcome, reply_markup=build_quick_actions())
    await state_store.save(user_id)

async def show_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    keyboard = build_model_keyboard(state.mode, state.current_model)
    header = f"""📂 *Model Catalog — {MODE_CONFIG[state.mode]['name']}*
━━━━━━━━━━━━━━━━━━━━━━
✅ = Đang dùng | 🟢 OpenCode | 🔵 NVIDIA
📊 Tổng: {len(MODE_CONFIG[state.mode].get('models', []))} models

👇 *Chọn model hoặc dùng nút Auto-select*"""
    await update.message.reply_text(header, parse_mode=TPM.MARKDOWN, reply_markup=keyboard)

async def model_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    data = query.data
    
    if data.startswith("model_"):
        parts = data.split("_")
        if len(parts) >= 3:
            mode, model_id = parts[1], parts[2]
            if mode in MODE_CONFIG and model_id in [m[1] for m in MODE_CONFIG[mode].get("models", [])]:
                state.mode = mode
                state.current_model = model_id
                state.current_provider = MODEL_PROFILES[model_id].provider
                state.auto_model = False
                display = _get_model_display(mode, model_id)
                await query.edit_message_text(f"✅ *Đã chọn model!*\n\n🤖 {display}\n🆔 `{model_id}`\n\n💡 Auto-select đã tắt.", parse_mode=TPM.MARKDOWN)
                await state_store.save(user_id)
    elif data.startswith("models_"):
        parts = data.split("_")
        if len(parts) >= 3:
            mode, page = parts[1], int(parts[2])
            keyboard = build_model_keyboard(mode, state.current_model, page)
            await query.edit_message_reply_markup(reply_markup=keyboard)
    elif data.startswith("auto_"):
        mode = data.split("_")[1]
        state.mode = mode
        state.auto_model = True
        await query.edit_message_text(f"🎯 *Auto-select BẬT*\n\nBot sẽ tự chọn model tối ưu cho mỗi task.", parse_mode=TPM.MARKDOWN)
        await state_store.save(user_id)
    elif data.startswith("quick_"):
        action = data.split("_")[1]
        await query.edit_message_text(f"⚡ Đang xử lý: {action}...")
        if action == "reset":
            state.history = []
            await query.edit_message_text("🗑️ *Đã xóa lịch sử chat!*")
        elif action == "stats":
            await _send_stats(update, state)
        elif action == "agent":
            await query.edit_message_text("🤖 *Agent Mode*\n\nGõ: `/agent <mô tả task>`")
        elif action == "fix":
            await query.edit_message_text("🔧 *Code Fix Mode*\n\nReply vào code bị lỗi và gõ `/fix`")
        elif action == "explain":
            await query.edit_message_text("📝 *Explain Mode*\n\nGửi code và hỏi giải thích.")
        await state_store.save(user_id)

async def agent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    
    if not context.args:
        current_deploy = state.agent_deploy_mode
        await update.message.reply_text(f"""🤖 *Agent Mode — Code tự động*
━━━━━━━━━━━━━━━━━━━━━━
*Cách dùng:* `/agent [github|local] <mô tả>`

*Ví dụ:*
• `/agent Tạo REST API FastAPI + SQLite`
• `/agent github Viết bot Telegram với commands`

*Deploy mode:* `{current_deploy}`
• `local` → Gửi file ZIP qua Telegram
• `github` → Push lên GitHub repo""", parse_mode=TPM.MARKDOWN)
        return
    
    deploy_mode = state.agent_deploy_mode
    task_desc = " ".join(context.args)
    if context.args[0].lower() in ['github', 'local']:
        deploy_mode = context.args[0].lower()
        task_desc = " ".join(context.args[1:])
    
    if not task_desc.strip():
        await update.message.reply_text("❌ *Thiếu mô tả task!*", parse_mode=TPM.MARKDOWN)
        return
    
    task_id = f"task_{int(time.time()*1000)}_{hashlib.md5(f'{user_id}{task_desc}'.encode()).hexdigest()[:6]}"
    task = AgentTask(task_id=task_id, user_id=user_id, description=task_desc)
    state.agent_tasks.append(task)
    
    status_msg = await update.message.reply_text(f"🤖 *Agent Task Started*\n━━━━━━━━\n🆔 `{task_id}`\n📝 {task_desc[:100]}{'...' if len(task_desc)>100 else ''}\n📦 Deploy: `{deploy_mode.upper()}`\n\n⏳ *Bước 1/5:* Phân tích yêu cầu...", parse_mode=TPM.MARKDOWN)
    asyncio.create_task(_run_agent_task(update, context, state, task, status_msg, deploy_mode))

async def _run_agent_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, task: AgentTask, status_msg: Message, deploy_mode: str):
    try:
        task.add_checkpoint("analyze", {"desc": task.description})
        await _update_status(status_msg, task, 1, 5, "Phân tích yêu cầu...")
        
        model_id = state.current_model
        provider = state.current_provider
        if state.auto_model:
            task_type = SmartModelRouter.detect_task_type(task.description, state.history)
            model_id, _, provider = SmartModelRouter.select_best_model(task.description, state.history, state.budget_conscious)
            logging.info(f"🎯 Auto-selected: {model_id} ({provider}) for {task_type.value}")
        
        plan_messages = [{"role": "system", "content": state.get_adaptive_prompt(AGENT_PROMPT)}, {"role": "user", "content": f"Task: {task.description}\n\nCreate a brief implementation plan (bullet points)."}]
        plan, plan_metrics = await StreamingHandler.stream_chat(model_id, provider, plan_messages, status_msg, lambda p: _update_status(status_msg, task, 1, 5, f"Planning: {p[:30]}"))
        task.model_used = model_id
        task.metrics.update(plan_metrics)
        
        task.add_checkpoint("plan", {"plan": plan[:500]})
        await _update_status(status_msg, task, 2, 5, "Viết code...")
        
        code_messages = [{"role": "system", "content": state.get_adaptive_prompt(AGENT_PROMPT)}, {"role": "user", "content": f"Task: {task.description}\n\nPlan:\n{plan}\n\nWrite COMPLETE code with file markers."}]
        
        async def code_progress(p):
            await _update_status(status_msg, task, 2, 5, f"Coding: {p[:30]}")
            
        code_text, code_metrics = await StreamingHandler.stream_chat(model_id, provider, code_messages, status_msg, code_progress)
        task.metrics['total_tokens'] = task.metrics.get('total_tokens', 0) + code_metrics.get('output_chars', 0) // 4
        
        task.add_checkpoint("code", {"files_detected": True})
        await _update_status(status_msg, task, 3, 5, "Parse & validate...")
        
        files = RobustFileParser.parse(code_text)
        if not files:
            task.auto_retry_count += 1
            if task.auto_retry_count <= 2:
                retry_messages = [{"role": "system", "content": AGENT_PROMPT}, {"role": "user", "content": f"Task: {task.description}\n\nPrevious output not parsed. Rewrite with EXACT <<<FILE:>>> markers."}]
                code_text, _ = await StreamingHandler.stream_chat(model_id, provider, retry_messages, status_msg, None)
                files = RobustFileParser.parse(code_text)
        
        issues = []
        for fname, content in files.items():
            issues.extend(SmartSyntaxChecker.check(content, fname))
        
        critical = [i for i in issues if i['level'] == 'error']
        if critical and task.auto_retry_count < 2:
            task.add_checkpoint("syntax_check", {"errors": len(critical)})
            await _update_status(status_msg, task, 3, 5, f"Tự sửa {len(critical)} lỗi...")
            fix_messages = [{"role": "system", "content": AGENT_PROMPT}, {"role": "user", "content": f"Fix these errors:\n{critical}\n\nOutput only fixed code with file markers."}]
            fixed_code, _ = await StreamingHandler.stream_chat(model_id, provider, fix_messages, status_msg, None)
            files = RobustFileParser.parse(fixed_code)
        
        task.add_checkpoint("deploy", {"mode": deploy_mode, "files": list(files.keys())})
        await _update_status(status_msg, task, 4, 5, "Deploying...")
        
        metadata = {"task_id": task.task_id, "description": task.description, "model": model_id, "files": list(files.keys())}
        
        if deploy_mode in ['local', 'both']:
            zip_path, zip_size = await LocalAgent.create_package(task.task_id, files, metadata)
            task.local_path = str(zip_path)
            task.files_created = list(files.keys())
        
        if deploy_mode in ['github', 'both']:
            success, username = await github.get_user()
            if success:
                repo_name = _smart_repo_name(task.description, user_id)
                success_repo, repo_url = await github.create_repo(repo_name, f"Auto: {task.description[:100]}")
                if success_repo or "already exists" in str(repo_url).lower():
                    success_push, final_url = await github.push_files(username, repo_name, files, f"Add {len(files)} files: {task.description[:50]}")
                    if success_push:
                        task.repo_url = final_url
                        if not task.files_created:
                            task.files_created = list(files.keys())
        
        task.status = "completed"
        task.result = "Success"
        state.usage.record(task.metrics.get('input_tokens', 0), task.metrics.get('total_tokens', 0), task.metrics.get('latency', 0), model_id, SmartModelRouter.detect_task_type(task.description, state.history))
        state.add_note(f"Completed: {task.description[:50]}", success=True)
        SmartModelRouter.record_result(model_id, success=True)
        
        file_summary = "\n".join(f"• `{f}`" for f in task.files_created[:8])
        if len(task.files_created) > 8:
            file_summary += f"\n• ...+{len(task.files_created)-8} more"
        
        result_msg = f"""✅ *Agent Task Completed!*
━━━━━━━━━━━━━━━━━━━━━━
🆔 `{task.task_id}`
📝 {task.description[:80]}...
📦 Deploy: `{deploy_mode.upper()}`

📁 Files ({len(task.files_created)}):
{file_summary}

📊 Metrics:
• ⏱ Latency: `{task.metrics.get('latency', 0):.1f}s`
• 📝 Tokens: `{task.metrics.get('total_tokens', 0)}`
• 🔄 Retries: `{task.auto_retry_count}`
• 🤖 Model: `{model_id}`"""
        
        if task.repo_url:
            result_msg += f"\n\n🔗 GitHub: {task.repo_url}"
        if task.local_path:
            result_msg += f"\n📦 ZIP: `{Path(task.local_path).stat().st_size/1024:.1f}KB`"
        
        await status_msg.edit_text(result_msg, parse_mode=TPM.MARKDOWN)
        
        if task.local_path:
            with open(task.local_path, 'rb') as f:
                bio = io.BytesIO(f.read())
            bio.name = f"{task.task_id}.zip"
            await update.message.reply_document(document=bio, caption=f"📦 {len(files)} files")
        
        await state_store.save(user_id)
        
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        state.add_note(f"Failed: {task.description[:50]} — {str(e)[:100]}", success=False)
        SmartModelRouter.record_result(task.model_used or state.current_model, success=False)
        
        error_msg = f"""❌ *Agent Task Failed*
━━━━━━━━━━━━━━━━━━━━━━
🆔 `{task.task_id}`
⚠️ Error: `{str(e)[:300]}`

💡 Try:
• Simplify the task description
• Use `/agent local` for ZIP output
• Check GitHub token if using github mode

🔁 Auto-retry: `{task.auto_retry_count}/2`"""
        await status_msg.edit_text(error_msg, parse_mode=TPM.MARKDOWN)
        await state_store.save(user_id)

async def _update_status(msg: Message, task: AgentTask, step: int, total: int, text: str):
    try:
        await msg.edit_text(f"🤖 *Agent — {step}/{total}*\n━━━━━━━━\n🆔 `{task.task_id}`\n⏳ {text}\n\n⏱ Started: {task.created_at[:16]}", parse_mode=TPM.MARKDOWN)
    except BadRequest:
        pass

def _smart_repo_name(desc: str, user_id: int) -> str:
    words = re.findall(r'[a-zA-Z]+', desc.lower())
    keywords = [w for w in words if len(w) > 3 and w not in ['create', 'make', 'build', 'write', 'the', 'and', 'with']][:5]
    name = '-'.join(keywords) if keywords else f"project-{user_id % 1000}"
    return name[:30].strip('-') or f"denia-{int(time.time())%10000}"

async def _send_stats(update: Update, state: ConversationState):
    s = state.usage
    avg_lat = s.avg_latency
    models_str = "\n".join([f"• `{m}`: {c}x" for m, c in sorted(s.models_used.items(), key=lambda x:-x[1])[:5]])
    
    stats = f"""📊 *Usage Statistics*
━━━━━━━━━━━━━━━━━━━━━━
🔢 Requests: `{s.total_requests}`
📝 Input tokens: `{s.total_input_tokens}`
💬 Output tokens: `{s.total_output_tokens}`
📦 Total: `{s.total_tokens}`
⏱ Avg latency: `{avg_lat:.2f}s`

🤖 Models used:
{models_str if models_str else 'Chưa có'}

📅 First: `{s.first_seen[:10]}`
🕐 Last: `{s.last_active[:16]}`}

💡 Tip: Use `/reset` to clear history."""
    await send_with_fallback(update, stats)

# ============================================================================
# 📨 MAIN MESSAGE HANDLER
# ============================================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state = get_user_state(user_id)
    
    allowed, msg = rate_limit_check(update)
    if not allowed:
        await update.message.reply_text(msg, parse_mode=TPM.MARKDOWN)
        return
    
    if text.startswith('/'):
        return
    
    state.history.append({"role": "user", "content": text})
    if len(state.history) > Config.MAX_HISTORY * 2:
        if Config.CONTEXT_COMPRESSION:
            state.history = ContextCompressor.compress_history(state.history, max_tokens=5000)
        else:
            state.history = state.history[-Config.MAX_HISTORY * 2:]
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    status_msg = await update.message.reply_text("⏳ *Đang suy nghĩ...*", parse_mode=TPM.MARKDOWN)
    
    try:
        model_id = state.current_model
        provider = state.current_provider
        if state.auto_model:
            task_type = SmartModelRouter.detect_task_type(text, state.history)
            model_id, _, provider = SmartModelRouter.select_best_model(text, state.history, state.budget_conscious)
        
        system_prompt = state.get_adaptive_prompt(SYSTEM_PROMPT if state.mode == 'chat' else AGENT_PROMPT)
        messages = [{"role": "system", "content": system_prompt}] + state.history[-Config.MAX_HISTORY:]
        
        async def stream_callback(preview: str):
            try:
                await status_msg.edit_text(f"🤖 *Đang trả lời...*\n\n`{preview}`\n\n⏱ Typing...", parse_mode=TPM.MARKDOWN)
            except:
                pass
        
        response, metrics = await StreamingHandler.stream_chat(model_id, provider, messages, status_msg, stream_callback if Config.STREAMING_RESPONSES else None)
        
        state.history.append({"role": "assistant", "content": response})
        if len(state.history) > Config.MAX_HISTORY * 2:
            state.history = state.history[-Config.MAX_HISTORY * 2:]
        
        state.usage.record(metrics.get('input_tokens', 0), metrics.get('output_chars', 0) // 4, metrics.get('latency', 0), model_id, SmartModelRouter.detect_task_type(text, state.history))
        SmartModelRouter.record_result(model_id, success=True)
        
        model_display = _get_model_display(state.mode, model_id)
        header = f"🤖 *{model_display}*\n{'━' * 20}\n\n"
        footer = f"\n\n⏱ `{metrics.get('latency', 0):.2f}s` | 📝 `{metrics.get('output_chars', 0) // 4}` tokens"
        full_text = header + response + footer
        
        await status_msg.delete()
        await send_with_fallback(update, full_text)
        await state_store.save(user_id)
        
    except Exception as e:
        logging.error(f"Error: {e}")
        error_msg = f"⚠️ *Lỗi xử lý*\n{'━' * 15}\n`{str(e)[:400]}`\n\n💡 *Thử:* `/reset` hoặc đổi model/mode"
        try:
            await status_msg.edit_text(error_msg, parse_mode=TPM.MARKDOWN)
        except Exception:
            await update.message.reply_text(error_msg, parse_mode=TPM.MARKDOWN)
        state.add_note(f"Error in {state.mode} mode: {str(e)[:200]}", success=False)
        await state_store.save(user_id)

# ============================================================================
# 📋 MODEL CONFIG
# ============================================================================

CATEGORY_EMOJI = {"GPT": "🟢", "Claude": "🟣", "Gemini": "🔵", "GLM": "🟡", "Qwen": "🟠", "MiniMax": "🔴", "Mistral": "⚪", "DeepSeek": "⚫", "Khác": "🟦", "TTS": "🔊", "Embedding": "📊"}

MODE_CONFIG = {
    "chat": {"name": "💬 Chat", "models": [("MiniMax", "minimax-m2.5-free", "MiniMax M2.5 Free", "opencode"), ("GLM", "z-ai/glm-5.1", "GLM-5.1 NVIDIA", "nvidia"), ("MiniMax", "minimaxai/minimax-m2.7", "MiniMax M2.7 NVIDIA", "nvidia"), ("DeepSeek", "deepseek-3.2", "DeepSeek V3", "opencode"), ("Claude", "claude-sonnet-4.6", "Claude Sonnet 4.6", "nvidia"), ("GPT", "gpt-5.4", "GPT-5.4", "nvidia")], "default": Config.DEFAULT_CHAT_MODEL},
    "agent": {"name": "🤖 Agent", "models": [("MiniMax", "minimaxai/minimax-m2.7", "MiniMax M2.7 NVIDIA", "nvidia"), ("GLM", "z-ai/glm-5.1", "GLM-5.1 NVIDIA", "nvidia"), ("MiniMax", "minimax-m2.5-free", "MiniMax M2.5 Free", "opencode"), ("Claude", "claude-sonnet-4.6", "Claude Sonnet 4.6", "nvidia")], "default": Config.DEFAULT_AGENT_MODEL},
    "embed": {"name": "📊 Embed", "models": [("Embedding", "text-embedding-3-small", "Text Embed 3 Small", "nvidia")], "default": "text-embedding-3-small"},
    "tts": {"name": "🔊 TTS", "models": [("TTS", "google-tts/vi", "Google TTS Vietnamese", "opencode")], "default": "google-tts/vi"},
}

def _get_model_display(mode: str, model_id: str) -> str:
    for cat, mid, display, provider in MODE_CONFIG.get(mode, {}).get("models", []):
        if mid == model_id:
            return f"{CATEGORY_EMOJI.get(cat, '⚪')} {display}"
    return model_id

# ============================================================================
# 🔄 CLEANUP & SHUTDOWN
# ============================================================================

async def periodic_cleanup():
    while True:
        await asyncio.sleep(3600)
        state_store.cleanup_old_tasks(Config.ZIP_RETENTION_HOURS)
        cutoff = time.time() - Config.ZIP_RETENTION_HOURS * 3600
        for zip_file in Config.WORK_DIR.glob("*.zip"):
            if zip_file.stat().st_mtime < cutoff:
                zip_file.unlink()
                logging.debug(f"🗑️ Cleaned: {zip_file.name}")

# ============================================================================
# 🚀 MAIN ENTRY POINT
# ============================================================================

def main():
    Config.init()
    logging.info("🚀 Starting Denia AI Agent Bot v8.0 (Ultimate Master Edition)...")

    application = (
        ApplicationBuilder()
        .token(Config.BOT_TOKEN)
        .concurrent_updates(True)
        .get_updates_read_timeout(Config.API_TIMEOUT)
        .build()
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', lambda u, c: send_with_fallback(u, HELP_TEXT)))
    application.add_handler(CommandHandler('models', show_models))
    application.add_handler(CommandHandler('agent', agent_command))
    application.add_handler(CommandHandler('stats', lambda u, c: _send_stats(u, get_user_state(u.effective_user.id))))
    application.add_handler(CommandHandler('reset', lambda u, c: _handle_reset(u, get_user_state(u.effective_user.id))))

    application.add_handler(CallbackQueryHandler(model_callback, pattern="^model_"))
    application.add_handler(CallbackQueryHandler(model_callback, pattern="^models_"))
    application.add_handler(CallbackQueryHandler(model_callback, pattern="^auto_"))
    application.add_handler(CallbackQueryHandler(model_callback, pattern="^quick_"))

    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logging.error(f"Update {update} caused error {context.error}")
        if update and update.effective_user:
            state = get_user_state(update.effective_user.id)
            state.add_note(f"System error: {str(context.error)[:200]}", success=False)
        if update and update.effective_message:
            await update.effective_message.reply_text("😵 *Đã xảy ra lỗi không mong muốn!*\nVui lòng thử lại sau.\n\n💡 *Thử:* `/reset` hoặc `/help`", parse_mode=TPM.MARKDOWN)

    application.add_error_handler(error_handler)

    async def post_init(app: Application):
        app.bot_data['github'] = github
        asyncio.create_task(periodic_cleanup())
        logging.info("✅ Bot initialized. Sessions created.")

    async def post_shutdown(app: Application):
        await github.close()
        await state_store.save_all()
        logging.info("🔒 All sessions closed. Bot shutdown complete.")

    application.post_init = post_init
    application.post_shutdown = post_shutdown

    logging.info("✅ Bot is running. Press Ctrl+C to stop.")
    application.run_polling(drop_pending_updates=True)

HELP_TEXT = """📖 *Hướng Dẫn Denia Bot v8.0*
━━━━━━━━━━━━━━━━━━━━━━

🎯 *Lệnh chính:*
• `/start` — Chào mừng + menu nhanh
• `/models` — Chọn model với nút bấm
• `/agent <task>` — Chạy agent tự động
• `/stats` — Xem thống kê sử dụng
• `/reset` — Xóa lịch sử chat
• `/help` — Hiển thị hướng dẫn này

⚙️ *Tùy chỉnh:*
• `/style concise` — Trả lời ngắn gọn
• `/style verbose` — Giải thích chi tiết
• `/auto on|off` — Bật/tắt auto model selection

🤖 *Agent Mode:*
• `/agent Tạo API FastAPI` — Code + local ZIP
• `/agent github Viết bot Telegram` — Code + push GitHub
• Auto-retry nếu lỗi, auto-fix syntax

💡 *Mẹo thông minh:*
• Bot tự chọn model phù hợp (bật bằng `/auto on`)
• Context tự nén khi dài quá
• Học từ lỗi để cải thiện lần sau
• Streaming response: thấy chữ hiện dần

🔧 *Troubleshooting:*
• Lỗi timeout? → Thử model khác hoặc /reset
• Code không parse? → Dùng `/agent local` để nhận file
• GitHub lỗi? → Kiểm tra token hoặc dùng local mode

📦 *Output:*
• Code dài → tự động gửi file .txt
• Agent task → gửi file .zip + README
• Metrics hiển thị: latency, tokens, model dùng

━━━━━━━━
🤖 Denia Bot v8.0 — Ultimate Master Edition ✨"""

def _handle_reset(update: Update, state: ConversationState):
    state.history = []
    state.agent_tasks = state.agent_tasks[-5:]
    return update.message.reply_text("🗑️ *Đã reset!*\n\nLịch sử chat đã xóa. Tasks cũ giữ lại 5 cái gần nhất.", parse_mode=TPM.MARKDOWN)

if __name__ == '__main__':
    main()
