#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════════════════════════════════════╗
║              🤖 FizzPop AI Agent Bot v7.0 — SINGLE FILE POWER          ║
║     All-in-One: Chat | Agent | RAG | Multi-Model | Auto-Optimize      ║
║     ✨ No external config • Hardcoded tokens • Telegram-native UX     ║
╚════════════════════════════════════════════════════════════════════════╝
"""

import asyncio, base64, hashlib, io, json, logging, os, re, shutil, sys, tempfile, time, traceback, zipfile
from dataclasses import dataclass, field, asdict, replace
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, Callable, Set
from functools import wraps, lru_cache
from contextlib import asynccontextmanager, contextmanager

# Third-party (install: pip install python-telegram-bot aiohttp)
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
# 🔐 CONFIGURATION — HARDCODED (As Requested)
# ============================================================================

class Config:
    """All config hardcoded for simplicity. Edit directly."""
    
    # === TELEGRAM ===
    BOT_TOKEN = "8909561772:AAGQgxrbvXbi-RACF4_Z7iiS4R7NA6Za6wU"
    
    # === AI PROVIDER (ckey.vn) ===
    API_KEY = "sk-e317a237354192e26f99951f06e4882779e8a0e08e86d2f71242e8ff770bdf24"
    API_BASE = "https://ckey.vn/v1"
    
    # === GITHUB ===
    GITHUB_TOKEN = "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"
    
    # === PATHS ===
    WORK_DIR = Path("/tmp/fizzpop_agent")  # Auto-created
    MAX_HISTORY = 40  # Messages to keep in context
    MAX_TOKENS_PER_CALL = 8192
    API_TIMEOUT = 180  # seconds
    
    # === AGENT SETTINGS ===
    DEFAULT_CHAT_MODEL = "deepseek-3.2"
    DEFAULT_AGENT_MODEL = "mistral-medium-3.5-128b"
    AUTO_MODEL_SELECTION = True  # v7 feature: smart routing
    CONTEXT_COMPRESSION = True  # Auto-summarize old messages
    STREAMING_RESPONSES = True  # Show tokens as they arrive
    
    # === RATE LIMITS ===
    USER_REQUESTS_PER_MIN = 15
    GLOBAL_REQUESTS_PER_MIN = 200
    
    # === AUTO-CLEANUP ===
    ZIP_RETENTION_HOURS = 48
    MAX_SELF_NOTES = 100
    
    @classmethod
    def init(cls):
        cls.WORK_DIR.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)-7s | %(message)s',
            handlers=[
                logging.FileHandler(cls.WORK_DIR / "bot.log", encoding='utf-8', mode='a'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logging.info(f"🚀 FizzPop v7.0 initialized | Work dir: {cls.WORK_DIR}")

# ============================================================================
# 🧠 SMART MODEL ROUTER — v7 Feature #1
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
    """Profile for each model: capabilities, cost, speed."""
    def __init__(self, model_id: str, display: str, category: str,
                 strengths: List[TaskType], cost_tier: int, speed_tier: int,
                 max_context: int = 128000):
        self.id = model_id
        self.display = display
        self.category = category
        self.strengths = set(strengths)
        self.cost_tier = cost_tier  # 1=cheap, 3=expensive
        self.speed_tier = speed_tier  # 1=fast, 3=slow
        self.max_context = max_context
        self.usage_count = 0
        self.success_rate = 1.0
    
    def score_for_task(self, task_type: TaskType, budget_conscious: bool = False) -> float:
        """Calculate suitability score (0-1) for a task."""
        score = 0.0
        # Capability match (40%)
        if task_type in self.strengths:
            score += 0.4
        # Speed (30%)
        score += (4 - self.speed_tier) / 3 * 0.3
        # Cost (20%) — lower tier = better if budget conscious
        if budget_conscious:
            score += (4 - self.cost_tier) / 3 * 0.2
        else:
            score += 0.2  # Cost doesn't matter
        # Reliability (10%)
        score += self.success_rate * 0.1
        return min(1.0, score)

# Model catalog with profiles
MODEL_PROFILES = {
    # Fast & cheap for simple tasks
    "deepseek-3.2": ModelProfile(
        "deepseek-3.2", "DeepSeek V3", "DeepSeek",
        [TaskType.CHAT, TaskType.SHORT_ANSWER, TaskType.CODE_GEN],
        cost_tier=1, speed_tier=1
    ),
    "glm4.7": ModelProfile(
        "glm4.7", "GLM-4.7", "GLM",
        [TaskType.CHAT, TaskType.ANALYSIS, TaskType.CODE_GEN],
        cost_tier=1, speed_tier=1
    ),
    # Balanced for general coding
    "mistral-medium-3.5-128b": ModelProfile(
        "mistral-medium-3.5-128b", "Mistral Medium 3.5", "Mistral",
        [TaskType.CODE_GEN, TaskType.CODE_FIX, TaskType.ANALYSIS, TaskType.LONG_FORM],
        cost_tier=2, speed_tier=2
    ),
    "qwen3-coder-480b-a35b-instruct": ModelProfile(
        "qwen3-coder-480b-a35b-instruct", "Qwen3 Coder 480B", "Qwen",
        [TaskType.CODE_GEN, TaskType.CODE_FIX, TaskType.ANALYSIS],
        cost_tier=2, speed_tier=2
    ),
    # Premium for complex reasoning
    "claude-sonnet-4.6": ModelProfile(
        "claude-sonnet-4.6", "Claude Sonnet 4.6", "Claude",
        [TaskType.ANALYSIS, TaskType.LONG_FORM, TaskType.CREATIVE, TaskType.CODE_FIX],
        cost_tier=3, speed_tier=2
    ),
    "gpt-5.4": ModelProfile(
        "gpt-5.4", "GPT-5.4", "GPT",
        [TaskType.ANALYSIS, TaskType.LONG_FORM, TaskType.CREATIVE, TaskType.CODE_GEN],
        cost_tier=3, speed_tier=2
    ),
    # Specialized
    "google-tts/vi": ModelProfile(
        "google-tts/vi", "Google TTS Vietnamese", "TTS",
        [], cost_tier=1, speed_tier=1
    ),
    "text-embedding-3-small": ModelProfile(
        "text-embedding-3-small", "Text Embedding 3 Small", "Embedding",
        [], cost_tier=1, speed_tier=1
    ),
}

class SmartModelRouter:
    """v7 Feature: Auto-select best model for each task."""
    
    @staticmethod
    def detect_task_type(text: str, context: List[Dict]) -> TaskType:
        """Heuristically detect task type from input."""
        text_lower = text.lower()
        
        # Code-related keywords
        code_keywords = ['code', 'function', 'def ', 'import ', 'class ', 
                        'javascript', 'python', 'react', 'api', 'endpoint',
                        'bug', 'error', 'fix', 'debug', 'syntax']
        if any(kw in text_lower for kw in code_keywords):
            if any(kw in text_lower for kw in ['fix', 'bug', 'error', 'debug']):
                return TaskType.CODE_FIX
            return TaskType.CODE_GEN
        
        # Short answer indicators
        if len(text) < 50 and any(q in text for q in ['?', 'là gì', 'tại sao', 'how', 'what']):
            return TaskType.SHORT_ANSWER
        
        # Creative/long form
        if any(kw in text_lower for kw in ['viết', 'write', 'story', 'poem', 'essay', 'content']):
            return TaskType.CREATIVE if len(text) < 200 else TaskType.LONG_FORM
        
        # Analysis
        if any(kw in text_lower for kw in ['phân tích', 'analyze', 'compare', 'review', 'explain']):
            return TaskType.ANALYSIS
        
        # Default
        return TaskType.CHAT if len(text) < 500 else TaskType.LONG_FORM
    
    @classmethod
    def select_best_model(cls, user_input: str, history: List[Dict], 
                          user_budget_conscious: bool = True) -> Tuple[str, str]:
        """Return (model_id, display_name) for best model."""
        task_type = cls.detect_task_type(user_input, history)
        
        candidates = []
        for model_id, profile in MODEL_PROFILES.items():
            if model_id in ["google-tts/vi", "text-embedding-3-small"]:
                continue  # Skip specialized models
            score = profile.score_for_task(task_type, user_budget_conscious)
            # Bonus for models with good history with this task type
            if task_type in profile.strengths and profile.success_rate > 0.9:
                score += 0.1
            candidates.append((model_id, profile.display, score))
        
        # Sort by score descending
        candidates.sort(key=lambda x: -x[2])
        
        # Return top choice
        best_id, best_display, _ = candidates[0]
        return best_id, best_display
    
    @classmethod
    def record_result(cls, model_id: str, success: bool):
        """Update model stats based on outcome."""
        if model_id in MODEL_PROFILES:
            profile = MODEL_PROFILES[model_id]
            profile.usage_count += 1
            # Exponential moving average for success rate
            alpha = 0.1
            profile.success_rate = alpha * (1.0 if success else 0.0) + (1-alpha) * profile.success_rate

# ============================================================================
# 🗜️ CONTEXT COMPRESSOR — v7 Feature #2
# ============================================================================

class ContextCompressor:
    """Auto-compress old messages to stay within token limits."""
    
    # Approximate tokens per char (conservative)
    CHARS_PER_TOKEN = 4
    
    @classmethod
    def estimate_tokens(cls, messages: List[Dict]) -> int:
        """Rough token estimate."""
        total_chars = sum(len(m.get('content', '')) for m in messages)
        # Add overhead for role labels
        return len(messages) * 5 + total_chars // cls.CHARS_PER_TOKEN
    
    @classmethod
    def compress_history(cls, history: List[Dict], max_tokens: int = 6000) -> List[Dict]:
        """Compress history by summarizing old messages."""
        if not history:
            return []
        
        # Keep last N messages intact
        keep_recent = 8
        recent = history[-keep_recent:] if len(history) > keep_recent else history
        
        if len(history) <= keep_recent:
            return history
        
        # Summarize older messages
        old_messages = history[:-keep_recent]
        old_text = "\n".join([
            f"{m['role']}: {m['content'][:200]}" for m in old_messages[-20:]  # Last 20 old
        ])
        
        summary = f"[Tóm tắt {len(old_messages)} tin nhắn trước]: {old_text[:800]}..."
        
        return [{"role": "system", "content": summary}] + recent
    
    @classmethod
    def smart_truncate(cls, content: str, max_chars: int = 3000) -> str:
        """Truncate content while preserving code blocks."""
        if len(content) <= max_chars:
            return content
        
        # Try to cut at logical boundaries
        # 1. End of code block
        if "```" in content:
            blocks = content.split("```")
            if len(blocks) >= 3:
                # Keep first code block + some context
                result = "```".join(blocks[:3])
                if len(result) < max_chars:
                    return result + "\n```[...tiếp tục trong file đính kèm...]"
        
        # 2. End of sentence
        sentences = content.split('. ')
        result = []
        for s in sentences:
            if len('. '.join(result + [s])) > max_chars - 50:
                break
            result.append(s)
        
        return '. '.join(result) + ' [...]'

# ============================================================================
# 🔄 STREAMING RESPONSE HANDLER — v7 Feature #3
# ============================================================================

class StreamingHandler:
    """Handle streaming responses with real-time updates."""
    
    @staticmethod
    async def stream_chat(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          model_id: str, messages: List[Dict],
                          status_msg: Message, api_key: str, api_base: str):
        """Stream AI response token by token with progress updates."""
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": Config.MAX_TOKENS_PER_CALL,
            "stream": True  # Enable streaming
        }
        
        # Initial status
        accumulated = []
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=Config.API_TIMEOUT)) as session:
                async with session.post(f"{api_base}/chat/completions", 
                                       headers=headers, json=payload) as resp:
                    
                    if resp.status != 200:
                        error = await resp.text()
                        raise Exception(f"API Error {resp.status}: {error[:200]}")
                    
                    # Process streaming response
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
                                    # Update every ~100 chars or 2 seconds
                                    if len(''.join(accumulated)) % 100 < len(content) or time.time() - start_time > 2:
                                        full_text = ''.join(accumulated)
                                        preview = full_text[-300:] if len(full_text) > 300 else full_text
                                        await status_msg.edit_text(
                                            f"🤖 *Đang trả lời...*\n\n`{preview}`\n\n⏱ {time.time()-start_time:.1f}s",
                                            parse_mode=TPM.MARKDOWN
                                        )
                            except json.JSONDecodeError:
                                continue
            
            final_text = ''.join(accumulated)
            latency = time.time() - start_time
            
            return final_text, {
                'latency': latency,
                'output_chars': len(final_text),
                'streaming': True
            }
            
        except asyncio.TimeoutError:
            # Fallback to non-streaming if streaming fails
            return await StreamingHandler._fallback_non_streaming(
                model_id, messages, api_key, api_base
            )
    
    @staticmethod
    async def _fallback_non_streaming(model_id: str, messages: List[Dict],
                                      api_key: str, api_base: str) -> Tuple[str, Dict]:
        """Fallback: regular non-streaming API call."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": Config.MAX_TOKENS_PER_CALL,
            "stream": False
        }
        
        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{api_base}/chat/completions",
                                   headers=headers, json=payload) as resp:
                result = await resp.json()
        
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        latency = time.time() - start_time
        
        return content, {'latency': latency, 'output_chars': len(content), 'streaming': False}

# ============================================================================
# 📊 USAGE TRACKER — v7 Feature #4
# ============================================================================

@dataclass
class UsageStats:
    """Track per-user and global usage."""
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_latency: float = 0.0
    models_used: Dict[str, int] = field(default_factory=dict)
    task_types: Dict[str, int] = field(default_factory=dict)
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def record(self, input_tokens: int, output_tokens: int, 
               latency: float, model_id: str, task_type: TaskType):
        self.total_requests += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_latency += latency
        self.models_used[model_id] = self.models_used.get(model_id, 0) + 1
        self.task_types[task_type.value] = self.task_types.get(task_type.value, 0) + 1
        self.last_active = datetime.now().isoformat()
    
    @property
    def avg_latency(self) -> float:
        return self.total_latency / self.total_requests if self.total_requests > 0 else 0
    
    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

# ============================================================================
# 🧩 ENHANCED DATA MODELS
# ============================================================================

@dataclass
class AgentTask:
    """Enhanced agent task with checkpoints and rollback."""
    task_id: str
    user_id: int
    description: str
    status: str = "pending"  # pending/running/checkpoint/completed/failed/rolled_back
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    checkpoints: List[Dict] = field(default_factory=list)  # Save points for rollback
    result: Optional[str] = None
    error: Optional[str] = None
    files_created: List[str] = field(default_factory=list)
    local_path: Optional[str] = None
    repo_url: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    model_used: Optional[str] = None
    auto_retry_count: int = 0
    
    def add_checkpoint(self, step: str, data: Dict):
        """Save progress checkpoint."""
        self.checkpoints.append({
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "data": data
        })
        # Keep only last 5 checkpoints
        if len(self.checkpoints) > 5:
            self.checkpoints = self.checkpoints[-5:]
    
    def can_rollback(self) -> bool:
        return len(self.checkpoints) >= 1
    
    def get_last_checkpoint(self) -> Optional[Dict]:
        return self.checkpoints[-1] if self.checkpoints else None

@dataclass  
class ConversationState:
    """User state with enhanced features."""
    history: List[Dict[str, str]] = field(default_factory=list)
    mode: str = "chat"  # chat/agent/embed/tts
    current_model: str = Config.DEFAULT_CHAT_MODEL
    auto_model: bool = True  # v7: enable smart routing
    usage: UsageStats = field(default_factory=UsageStats)
    agent_tasks: List[AgentTask] = field(default_factory=list)
    
    # User preferences
    preferred_style: str = "balanced"  # concise/balanced/verbose
    language_hint: str = "auto"  # auto/vi/en
    budget_conscious: bool = True  # Prefer cheaper models
    
    # Memory & learning
    self_notes: List[str] = field(default_factory=list)
    error_patterns: Dict[str, int] = field(default_factory=dict)
    successful_patterns: Dict[str, int] = field(default_factory=dict)
    
    # Branching conversations (v7 feature)
    branches: Dict[str, List[Dict]] = field(default_factory=dict)  # name -> history
    active_branch: Optional[str] = None
    
    def add_note(self, note: str, success: bool = True):
        """Record learning with deduplication."""
        target = self.successful_patterns if success else self.error_patterns
        sig = note[:150].strip()
        target[sig] = target.get(sig, 0) + 1
        
        if success and sig not in self.self_notes:
            self.self_notes.append(f"✅ {sig}")
            if len(self.self_notes) > Config.MAX_SELF_NOTES:
                self.self_notes = self.self_notes[-Config.MAX_SELF_NOTES:]
    
    def get_adaptive_prompt(self, base: str) -> str:
        """Build system prompt adapted to user preferences."""
        prompt = base
        
        # Style adaptation
        if self.preferred_style == "concise":
            prompt += "\n\nSTYLE: Be extremely concise. Code only, minimal explanations."
        elif self.preferred_style == "verbose":
            prompt += "\n\nSTYLE: Provide detailed explanations with examples and comments."
        
        # Language adaptation
        if self.language_hint == "vi":
            prompt += "\n\nLANGUAGE: Respond in Vietnamese when appropriate, but keep code in English."
        
        # Add learned patterns
        if self.successful_patterns:
            top_success = sorted(self.successful_patterns.items(), key=lambda x: -x[1])[:3]
            if top_success:
                prompt += "\n\nPREFERRED PATTERNS:\n" + "\n".join(f"- {p}" for p, _ in top_success)
        
        return prompt

# ============================================================================
# 🗄️ IN-MEMORY STATE STORE (Single-file persistence)
# ============================================================================

class StateStore:
    """Simple JSON-based state persistence in single file."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._cache: Dict[int, ConversationState] = {}
        self._lock = asyncio.Lock()
        self._load()
    
    def _load(self):
        """Load states from JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for uid_str, state_data in data.items():
                    uid = int(uid_str)
                    # Reconstruct UsageStats
                    if 'usage' in state_data and isinstance(state_data['usage'], dict):
                        state_data['usage'] = UsageStats(**state_data['usage'])
                    self._cache[uid] = ConversationState(**state_data)
                logging.info(f"📥 Loaded {len(self._cache)} user states")
            except Exception as e:
                logging.warning(f"⚠️ Failed to load states: {e}")
    
    async def _save(self):
        """Save states to JSON file."""
        async with self._lock:
            try:
                data = {}
                for uid, state in self._cache.items():
                    # Convert UsageStats to dict for JSON
                    state_dict = asdict(state)
                    state_dict['usage'] = asdict(state.usage)
                    data[str(uid)] = state_dict
                
                # Atomic write
                temp_file = self.file_path.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                temp_file.replace(self.file_path)
            except Exception as e:
                logging.error(f"❌ Failed to save states: {e}")
    
    def get(self, user_id: int) -> ConversationState:
        """Get or create user state."""
        if user_id not in self._cache:
            self._cache[user_id] = ConversationState()
            logging.info(f"🆕 New state for user {user_id}")
        return self._cache[user_id]
    
    async def save(self, user_id: int):
        """Save specific user state."""
        if user_id in self._cache:
            await self._save()
    
    async def save_all(self):
        """Save all states."""
        await self._save()
    
    def cleanup_old_tasks(self, hours: int = 48):
        """Remove old agent tasks to save memory."""
        cutoff = datetime.now() - timedelta(hours=hours)
        for state in self._cache.values():
            original = len(state.agent_tasks)
            state.agent_tasks = [
                t for t in state.agent_tasks 
                if datetime.fromisoformat(t.created_at) > cutoff
            ]
            if len(state.agent_tasks) < original:
                logging.debug(f"🗑️ Cleaned {original - len(state.agent_tasks)} old tasks")

# Global state store
state_store = StateStore(Config.WORK_DIR / "states.json")

def get_user_state(user_id: int) -> ConversationState:
    return state_store.get(user_id)

# ============================================================================
# 🛡️ RATE LIMITER (In-memory, single-file friendly)
# ============================================================================

class SimpleRateLimiter:
    """Token bucket rate limiter for single-file deployment."""
    
    def __init__(self, rate: int, window: float = 60.0):
        self.rate = rate
        self.window = window
        self.buckets: Dict[Any, List[float]] = {}
    
    def allow(self, key: Any) -> Tuple[bool, float]:
        """Check if request allowed. Returns (allowed, wait_seconds)."""
        now = time.time()
        
        if key not in self.buckets:
            self.buckets[key] = []
        
        # Remove expired
        self.buckets[key] = [t for t in self.buckets[key] if now - t < self.window]
        
        if len(self.buckets[key]) >= self.rate:
            oldest = min(self.buckets[key])
            wait = self.window - (now - oldest)
            return False, max(0, wait)
        
        self.buckets[key].append(now)
        return True, 0

user_limiter = SimpleRateLimiter(Config.USER_REQUESTS_PER_MIN)
global_limiter = SimpleRateLimiter(Config.GLOBAL_REQUESTS_PER_MIN)

def rate_limit_check(update: Update) -> Tuple[bool, Optional[str]]:
    """Check rate limits. Returns (allowed, error_message)."""
    user_id = update.effective_user.id
    
    # Global check
    allowed, wait = global_limiter.allow("global")
    if not allowed:
        return False, f"🌍 Server busy. Try in `{wait:.0f}s`."
    
    # User check
    allowed, wait = user_limiter.allow(user_id)
    if not allowed:
        return False, f"⏱ You're sending too fast. Wait `{wait:.0f}s`."
    
    return True, None

# ============================================================================
# 📁 ENHANCED FILE PARSER (Multi-strategy, robust)
# ============================================================================

class RobustFileParser:
    """Parse AI output into files with 5 fallback strategies."""
    
    STRATEGIES = [
        # Strategy 1: Primary markers
        (re.compile(r'<<<FILE:\s*([^>\s]+)\s*>>>(.*?)<<<ENDFILE>>>', re.DOTALL | re.I),
         lambda m: (m.group(1).strip(), m.group(2).strip())),
        
        # Strategy 2: Code blocks with filename comment
        (re.compile(r'```(?:\w+)?\s*\n?\s*#\s*filename:\s*([^\n]+)\s*\n(.*?)```', re.DOTALL | re.I),
         lambda m: (m.group(1).strip(), m.group(2).strip())),
        
        # Strategy 3: Code blocks with filename in first line
        (re.compile(r'```(?:\w+)?\s+([^\n`]+?\.\w+)\s*\n(.*?)```', re.DOTALL | re.I),
         lambda m: (m.group(1).strip(), m.group(2).strip())),
        
        # Strategy 4: Comment header pattern
        (re.compile(r'^#\s*File:\s*([^\n]+)\s*\n(.*?)(?=\n^#\s*File:|\Z)', re.DOTALL | re.M | re.I),
         lambda m: (m.group(1).strip(), m.group(2).strip())),
        
        # Strategy 5: Simple code block (fallback to main.py)
        (re.compile(r'```(?:python|py)?\s*\n(.*?)```', re.DOTALL | re.I),
         lambda m: ("main.py", m.group(1).strip())),
    ]
    
    @classmethod
    def parse(cls, text: str) -> Dict[str, str]:
        """Parse text into {filename: content} dict."""
        files = {}
        
        for pattern, extractor in cls.STRATEGIES:
            if files:  # Stop if we found files with earlier strategy
                break
            for match in pattern.finditer(text):
                try:
                    filename, content = extractor(match)
                    if cls._is_valid(filename) and content:
                        safe_name = cls._sanitize(filename)
                        files[safe_name] = content
                except Exception:
                    continue
        
        # Last resort: if text looks like single file code
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
    """Multi-language syntax validation with auto-fix hints."""
    
    @classmethod
    def check(cls, code: str, filename: str) -> List[Dict]:
        """Return list of {level, message, suggestion}."""
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
        
        # Syntax check
        try:
            compile(code, filename, 'exec')
        except SyntaxError as e:
            return [{"level": "error", "message": f"Syntax error line {e.lineno}: {e.msg}", 
                    "suggestion": "Check indentation, colons, parentheses"}]
        
        # Warnings
        if re.search(r'\bexcept\s*:', code) and not re.search(r'\bexcept\s+\w+', code):
            issues.append({"level": "warn", "message": "Bare `except:`", 
                          "suggestion": "Use `except Exception:` for clarity"})
        
        if 'print(' in code and 'logging' not in code and len(code) > 300:
            issues.append({"level": "info", "message": "Using print() statements", 
                          "suggestion": "Consider `logging` module for production"})
        
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
            return [{"level": "error", "message": f"JSON error: {e.msg}", 
                    "suggestion": "Check commas, quotes, trailing commas"}]

# ============================================================================
# 📦 LOCAL ZIP AGENT (Enhanced with metadata)
# ============================================================================

class LocalAgent:
    """Create ZIP packages with rich metadata."""
    
    @classmethod
    async def create_package(cls, task_id: str, files: Dict[str, str], 
                            metadata: Dict) -> Tuple[Path, int]:
        """Create ZIP with files + metadata + README."""
        task_dir = Config.WORK_DIR / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        total_size = 0
        
        # Write files
        for filename, content in files.items():
            file_path = task_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            total_size += file_path.stat().st_size
        
        # Add metadata
        meta = {
            **metadata,
            "created_at": datetime.now().isoformat(),
            "fizzpop_version": "7.0",
            "files_count": len(files)
        }
        (task_dir / ".fizzpop.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')
        
        # Auto-generate README if not present
        if "README.md" not in files:
            readme = cls._generate_readme(metadata, files)
            (task_dir / "README.md").write_text(readme, encoding='utf-8')
            total_size += len(readme.encode('utf-8'))
        
        # Create ZIP
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
        """Auto-generate helpful README."""
        desc = meta.get('description', 'Auto-generated project')[:200]
        files_list = "\n".join(f"- `{f}` ({len(c)} chars)" for f, c in list(files.items())[:10])
        
        # Detect project type for setup hints
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
FizzPop AI Agent v7.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')}

> 💡 Tip: Check `.fizzpop.json` for full metadata
"""

# ============================================================================
# 🌐 GITHUB CLIENT (Lightweight, single-file)
# ============================================================================

class LiteGitHub:
    """Minimal GitHub API client for single-file deployment."""
    
    BASE = "https://api.github.com"
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "FizzPop-Bot/7.0"
        }
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _session_get(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=Config.API_TIMEOUT),
                headers={"User-Agent": self.headers["User-Agent"]}
            )
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
        """Get GitHub username."""
        status, data = await self._request("GET", "/user")
        if status == 200 and isinstance(data, dict):
            return True, data.get("login", "")
        return False, ""
    
    async def create_repo(self, name: str, desc: str = "", private: bool = False) -> Tuple[bool, str]:
        """Create repo, return (success, url)."""
        payload = {"name": name, "description": desc[:300], "private": private, "auto_init": True}
        status, data = await self._request("POST", "/user/repos", json=payload)
        if status == 201 and isinstance(data, dict):
            return True, data.get("html_url", "")
        return False, str(data) if isinstance(data, dict) else data
    
    async def push_files(self, owner: str, repo: str, files: Dict[str, str], 
                        message: str, branch: str = "main") -> Tuple[bool, str]:
        """Push multiple files in sequence."""
        for path, content in files.items():
            encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            # Check if file exists
            status, data = await self._request("GET", f"/repos/{owner}/{repo}/contents/{path}?ref={branch}")
            
            payload = {
                "message": message[:200],
                "content": encoded,
                "branch": branch
            }
            if status == 200 and isinstance(data, dict) and "sha" in data:
                payload["sha"] = data["sha"]  # Update existing
                method = "PUT"
            else:
                method = "PUT"  # Create new
            
            status, _ = await self._request(method, f"/repos/{owner}/{repo}/contents/{path}", json=payload)
            if status not in (200, 201):
                return False, f"Failed to push {path}"
            await asyncio.sleep(0.3)  # Rate limit friendly
        
        return True, f"https://github.com/{owner}/{repo}"
    
    async def close(self):
        if self._session:
            await self._session.close()

github = LiteGitHub(Config.GITHUB_TOKEN)

# ============================================================================
# 🤖 AI CLIENT (With smart retry & fallback)
# ============================================================================

class SmartAIClient:
    """AI client with auto-retry, model fallback, and streaming."""
    
    def __init__(self, base: str, key: str):
        self.base = base
        self.key = key
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=Config.API_TIMEOUT)
            )
        return self._session
    
    async def chat(self, model: str, messages: List[Dict], 
                   stream: bool = Config.STREAMING_RESPONSES,
                   status_callback: Optional[Callable] = None) -> Tuple[str, Dict]:
        """Smart chat with retry/fallback."""
        session = await self._get_session()
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.key}"}
        
        # Add system prompt if missing
        if not any(m.get('role') == 'system' for m in messages):
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": Config.MAX_TOKENS_PER_CALL,
            "stream": stream
        }
        
        # Try primary model, fallback on error
        for attempt, try_model in enumerate([model] + self._get_fallbacks(model)):
            if attempt > 0:
                logging.warning(f"🔄 Retrying with fallback model: {try_model}")
            
            try:
                if stream and Config.STREAMING_RESPONSES:
                    return await self._stream_chat(session, try_model, payload, headers, status_callback)
                else:
                    return await self._regular_chat(session, try_model, payload, headers)
                    
            except Exception as e:
                if attempt == 2:  # After 3 tries (1 primary + 2 fallbacks)
                    raise
                logging.warning(f"⚠️ Attempt {attempt+1} failed: {e}")
                await asyncio.sleep(1 * attempt)  # Exponential backoff
        
        raise Exception("All model attempts failed")
    
    async def _regular_chat(self, session: aiohttp.ClientSession, model: str, 
                           payload: Dict, headers: Dict) -> Tuple[str, Dict]:
        """Non-streaming API call."""
        payload["stream"] = False
        start = time.time()
        
        async with session.post(f"{self.base}/chat/completions", headers=headers, json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"API {resp.status}: {await resp.text()[:200]}")
            result = await resp.json()
        
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        usage = result.get('usage', {})
        
        return content, {
            'latency': time.time() - start,
            'input_tokens': usage.get('prompt_tokens', 0),
            'output_tokens': usage.get('completion_tokens', 0),
            'model_used': model
        }
    
    async def _stream_chat(self, session: aiohttp.ClientSession, model: str,
                          payload: Dict, headers: Dict,
                          callback: Optional[Callable]) -> Tuple[str, Dict]:
        """Streaming API call with real-time updates."""
        payload["stream"] = True
        start = time.time()
        accumulated = []
        
        async with session.post(f"{self.base}/chat/completions", headers=headers, json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"API {resp.status}: {await resp.text()[:200]}")
            
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
                            # Update callback every ~150 chars
                            if callback and len(''.join(accumulated)) % 150 < len(content):
                                await callback(''.join(accumulated)[-400:])
                    except:
                        continue
        
        return ''.join(accumulated), {
            'latency': time.time() - start,
            'output_chars': len(accumulated),
            'model_used': model,
            'streaming': True
        }
    
    def _get_fallbacks(self, primary: str) -> List[str]:
        """Get fallback models in order of preference."""
        # Simple fallback strategy: similar capability, cheaper first
        fallbacks = []
        primary_profile = MODEL_PROFILES.get(primary)
        if not primary_profile:
            return list(MODEL_PROFILES.keys())[:2]
        
        # Same category, lower cost tier
        for mid, profile in MODEL_PROFILES.items():
            if mid == primary:
                continue
            if profile.category == primary_profile.category and profile.cost_tier < primary_profile.cost_tier:
                fallbacks.append(mid)
        
        # Any model with same strengths
        for mid, profile in MODEL_PROFILES.items():
            if mid in fallbacks or mid == primary:
                continue
            if primary_profile.strengths & profile.strengths:
                fallbacks.append(mid)
        
        return fallbacks[:2]  # Max 2 fallbacks
    
    async def close(self):
        if self._session:
            await self._session.close()

ai_client = SmartAIClient(Config.API_BASE, Config.API_KEY)

# ============================================================================
# 📋 SYSTEM PROMPTS (Enhanced for v7)
# ============================================================================

SYSTEM_PROMPT = """You are FizzPop AI Agent v7.0 — an advanced autonomous coding assistant.

CORE PRINCIPLES:
1. Write COMPLETE, RUNNABLE code — no placeholders, no pseudocode
2. Include ALL necessary files: main, dependencies, config, README
3. Follow best practices: docstrings, error handling, type hints, logging
4. Adapt to user preferences: concise/verbose, language, style
5. Learn from interactions: remember what works, avoid past mistakes

OUTPUT FORMAT FOR CODE TASKS:
Use file markers for each file:
<<<FILE:filename.py>>>
[complete file content]
<<<ENDFILE>>>

Example:
<<<FILE:main.py>>>
import asyncio
async def main():
    print("Hello from FizzPop!")
if __name__ == "__main__":
    asyncio.run(main())
<<<ENDFILE>>>

<<<FILE:requirements.txt>>>
asyncio>=3.4.3
<<<ENDFILE>>>

RESPONSE STYLE:
- If user prefers concise: code only, minimal text
- If user prefers verbose: explanations + comments + examples
- Default: balanced — code with brief context

SELF-IMPROVEMENT:
After each task, note: what worked well, what could be better.
Use these notes to improve future responses.
"""

AGENT_PROMPT = """You are FizzPop Agent in AUTONOMOUS MODE.

MISSION: Complete the task end-to-end with ZERO follow-up questions.

RULES:
1. Analyze requirements thoroughly before coding
2. Plan file structure and dependencies first
3. Write production-ready code: error handling, logging, config management
4. Include: main file, dependencies, README, .env.example (if needed)
5. Test logic mentally before outputting
6. If uncertain, make reasonable assumption and proceed

STRICT OUTPUT:
Each file MUST be wrapped:
<<<FILE:filename>>>
[content]
<<<ENDFILE>>>

REQUIRED FILES:
• Entry point (main.py, index.js, etc.)
• Dependencies (requirements.txt, package.json)
• README.md with setup/run instructions
• .env.example if using environment variables

QUALITY CHECKLIST:
☑ No hardcoded secrets — use env vars
☑ Proper error handling (try/except, error messages)
☑ Logging instead of print() for production
☑ Docstrings for functions/classes
☑ Type hints where helpful

THINKING PROCESS:
1. Understand task → 2. Plan architecture → 3. Write file-by-file 
→ 4. Review completeness → 5. Output with markers

If task is ambiguous, choose the most common interpretation and proceed.
"""

# ============================================================================
# 🎨 TELEGRAM UI HELPERS
# ============================================================================

def build_model_keyboard(mode: str, current: str, page: int = 0) -> InlineKeyboardMarkup:
    """Build inline keyboard for model selection."""
    models = MODE_CONFIG.get(mode, {}).get("models", [])
    per_page = 6  # Show 6 models per page
    total_pages = (len(models) + per_page - 1) // per_page
    
    start_idx = page * per_page
    page_models = models[start_idx:start_idx + per_page]
    
    keyboard = []
    for cat, model_id, display in page_models:
        prefix = "✅ " if model_id == current else CATEGORY_EMOJI.get(cat, "⚪ ")
        btn = InlineKeyboardButton(f"{prefix}{display[:20]}", callback_data=f"model_{mode}_{model_id}")
        keyboard.append([btn])
    
    # Navigation
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
    """Build quick action buttons for common tasks."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤖 Agent Mode", callback_data="quick_agent"),
            InlineKeyboardButton("📊 Stats", callback_data="quick_stats"),
        ],
        [
            InlineKeyboardButton("🔧 Fix Code", callback_data="quick_fix"),
            InlineKeyboardButton("📝 Explain", callback_data="quick_explain"),
        ],
        [
            InlineKeyboardButton("🗑️ Reset Chat", callback_data="quick_reset"),
        ],
    ])

async def send_with_fallback(update: Update, text: str, 
                            parse_mode: str = TPM.MARKDOWN, **kwargs):
    """Send message with automatic fallback for long content."""
    if len(text) <= MessageLimit.MAX_TEXT_LENGTH:
        try:
            return await update.message.reply_text(text, parse_mode=parse_mode, **kwargs)
        except BadRequest as e:
            if "message is too long" not in str(e).lower():
                raise
    
    # Fallback: send as document
    bio = io.BytesIO(text.encode('utf-8'))
    bio.name = "response.txt"
    return await update.message.reply_document(
        document=bio, 
        caption="📄 Content too long for chat — sent as file",
        **kwargs
    )

# ============================================================================
# 🎯 COMMAND HANDLERS (Enhanced for v7)
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome command with smart UI."""
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    
    # Check rate limit
    allowed, msg = rate_limit_check(update)
    if not allowed:
        await update.message.reply_text(msg, parse_mode=TPM.MARKDOWN)
        return
    
    # Detect user language preference
    if not state.language_hint or state.language_hint == "auto":
        first_msg = update.message.text or ""
        if re.search(r'[\u0400-\u04FF\u4e00-\u9fff]', first_msg):  # Cyrillic or CJK
            state.language_hint = "en"  # Default to English for non-Latin
        elif any(viet in first_msg.lower() for viet in ['xin chào', 'cảm ơn', 'tôi']):
            state.language_hint = "vi"
    
    model_display = _get_model_display(state.mode, state.current_model)
    
    welcome = f"""╔══════════════════════════╗
║   🤖 *FizzPop v7.0*      ║
║   *Single-File Power*    ║
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
• /models — Chọn model (có nút)
• /switch <tên> — Đổi model nhanh
• /agent <task> — Chạy agent tự động
• /style concise|verbose — Đổi phong cách
• /stats — Xem thống kê
• /reset — Xóa lịch sử
• /help — Hướng dẫn chi tiết

💡 *Mẹo v7:* Gõ `/agent github Tạo API FastAPI` để auto-deploy!"""
    
    await send_with_fallback(update, welcome, reply_markup=build_quick_actions())
    await state_store.save(user_id)

async def show_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show models with inline keyboard."""
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    
    keyboard = build_model_keyboard(state.mode, state.current_model)
    
    header = f"""📂 *Model Catalog — {MODE_CONFIG[state.mode]['name']}*
━━━━━━━━━━━━━━━━━━━━━━
✅ = Đang dùng | 🎯 = Auto-select bật
📊 Tổng: {len(MODE_CONFIG[state.mode].get('models', []))} models

👇 *Chọn model hoặc dùng nút Auto-select*"""
    
    await update.message.reply_text(header, parse_mode=TPM.MARKDOWN, reply_markup=keyboard)

async def model_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle model selection callbacks."""
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
                state.auto_model = False  # Disable auto when manually selected
                
                display = _get_model_display(mode, model_id)
                await query.edit_message_text(
                    f"✅ *Đã chọn model!*\n\n🤖 {display}\n🆔 `{model_id}`\n\n💡 Auto-select đã tắt. Dùng `/auto on` để bật lại.",
                    parse_mode=TPM.MARKDOWN
                )
                await state_store.save(user_id)
    
    elif data.startswith("models_"):
        # Pagination
        parts = data.split("_")
        if len(parts) >= 3:
            mode, page = parts[1], int(parts[2])
            keyboard = build_model_keyboard(mode, state.current_model, page)
            await query.edit_message_reply_markup(reply_markup=keyboard)
    
    elif data.startswith("auto_"):
        mode = data.split("_")[1]
        state.mode = mode
        state.auto_model = True
        await query.edit_message_text(
            f"🎯 *Auto-select BẬT*\n\nBot sẽ tự chọn model tối ưu cho mỗi task dựa trên:\n• Loại công việc\n• Độ phức tạp\n• Ngân sách token\n\n💡 Gõ `/auto off` để tắt.",
            parse_mode=TPM.MARKDOWN
        )
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
            await query.edit_message_text("🤖 *Agent Mode*\n\nGõ: `/agent <mô tả task>`\n\nVí dụ:\n• `/agent Tạo API user với JWT`\n• `/agent github Viết bot Telegram đơn giản`")
        elif action == "fix":
            await query.edit_message_text("🔧 *Code Fix Mode*\n\nReply vào code bị lỗi và gõ `/fix` hoặc mô tả lỗi:\n\n`/fix Lỗi syntax ở line 15`")
        elif action == "explain":
            await query.edit_message_text("📝 *Explain Mode*\n\nGửi code và hỏi:\n\n`Giải thích hàm này làm gì?`\n`Tại sao code này chạy chậm?`")
        
        await state_store.save(user_id)

async def agent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced agent command with smart workflow."""
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    
    if not context.args:
        # Show help with deploy mode options
        current_deploy = state.agent_deploy_mode if hasattr(state, 'agent_deploy_mode') else 'local'
        await update.message.reply_text(
            f"""🤖 *Agent Mode — Code tự động*
━━━━━━━━━━━━━━━━━━━━━━
*Cách dùng:* `/agent [github|local] <mô tả>`

*Ví dụ:*
• `/agent Tạo REST API FastAPI + SQLite`
• `/agent github Viết bot Telegram với commands`
• `/agent local Tạo script crawl web đơn giản`

*Deploy mode:* `{current_deploy}`
• `local` → Gửi file ZIP qua Telegram
• `github` → Push lên GitHub repo

💡 *Mẹo:* Thêm `github` để auto-deploy, hoặc `local` để nhận file.""",
            parse_mode=TPM.MARKDOWN
        )
        return
    
    # Parse deploy mode
    deploy_mode = getattr(state, 'agent_deploy_mode', 'local')
    task_desc = " ".join(context.args)
    
    if context.args[0].lower() in ['github', 'local']:
        deploy_mode = context.args[0].lower()
        task_desc = " ".join(context.args[1:])
    
    if not task_desc.strip():
        await update.message.reply_text("❌ *Thiếu mô tả task!*\nVí dụ: `/agent Tạo API user management`", parse_mode=TPM.MARKDOWN)
        return
    
    # Create task with checkpointing
    task_id = f"task_{int(time.time()*1000)}_{hashlib.md5(f'{user_id}{task_desc}'.encode()).hexdigest()[:6]}"
    task = AgentTask(task_id=task_id, user_id=user_id, description=task_desc)
    state.agent_tasks.append(task)
    
    # Initial status
    status_msg = await update.message.reply_text(
        f"🤖 *Agent Task Started*\n━━━━━━━━\n🆔 `{task_id}`\n📝 {task_desc[:100]}{'...' if len(task_desc)>100 else ''}\n📦 Deploy: `{deploy_mode.upper()}`\n\n⏳ *Bước 1/5:* Phân tích yêu cầu...",
        parse_mode=TPM.MARKDOWN
    )
    
    # Run async
    asyncio.create_task(_run_agent_task(update, context, state, task, status_msg, deploy_mode))

async def _run_agent_task(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         state: ConversationState, task: AgentTask,
                         status_msg: Message, deploy_mode: str):
    """Execute agent task with checkpoints and auto-retry."""
    try:
        # ===== CHECKPOINT 1: Analyze =====
        task.add_checkpoint("analyze", {"desc": task.description})
        await _update_status(status_msg, task, 1, 5, "Phân tích yêu cầu...")
        
        # Smart model selection
        model_id = state.current_model
        if state.auto_model:
            task_type = SmartModelRouter.detect_task_type(task.description, state.history)
            model_id, model_display = SmartModelRouter.select_best_model(
                task.description, state.history, state.budget_conscious
            )
            logging.info(f"🎯 Auto-selected: {model_id} for {task_type.value}")
        
        # Generate plan
        plan_messages = [
            {"role": "system", "content": state.get_adaptive_prompt(AGENT_PROMPT)},
            {"role": "user", "content": f"Task: {task.description}\n\nCreate a brief implementation plan (bullet points)."}
        ]
        
        plan, plan_metrics = await ai_client.chat(model_id, plan_messages)
        task.model_used = model_id
        task.metrics.update(plan_metrics)
        
        # ===== CHECKPOINT 2: Code Generation =====
        task.add_checkpoint("plan", {"plan": plan[:500]})
        await _update_status(status_msg, task, 2, 5, "Viết code...")
        
        code_messages = [
            {"role": "system", "content": state.get_adaptive_prompt(AGENT_PROMPT)},
            {"role": "user", "content": f"Task: {task.description}\n\nPlan:\n{plan}\n\nWrite COMPLETE code with file markers."}
        ]
        
        code_text, code_metrics = await ai_client.chat(model_id, code_messages)
        task.metrics['total_tokens'] = task.metrics.get('total_tokens', 0) + code_metrics.get('output_tokens', 0)
        
        # ===== CHECKPOINT 3: Parse & Validate =====
        task.add_checkpoint("code", {"files_detected": True})
        await _update_status(status_msg, task, 3, 5, "Parse & validate...")
        
        files = RobustFileParser.parse(code_text)
        
        if not files:
            # Auto-retry with stronger prompt
            task.auto_retry_count += 1
            if task.auto_retry_count <= 2:
                retry_msg = "Previous output not parsed. Rewrite with EXACT <<<FILE:>>> markers."
                code_messages[-1]["content"] += f"\n\n{retry_msg}"
                code_text, code_metrics = await ai_client.chat(model_id, code_messages)
                files = RobustFileParser.parse(code_text)
        
        # Syntax check
        issues = []
        for fname, content in files.items():
            issues.extend(SmartSyntaxChecker.check(content, fname))
        
        # Auto-fix if critical errors
        critical = [i for i in issues if i['level'] == 'error']
        if critical and task.auto_retry_count < 2:
            task.add_checkpoint("syntax_check", {"errors": len(critical)})
            await _update_status(status_msg, task, 3, 5, f"Tự sửa {len(critical)} lỗi...")
            
            fix_messages = [
                {"role": "system", "content": AGENT_PROMPT},
                {"role": "user", "content": f"Fix these errors:\n{critical}\n\nOutput only fixed code with file markers."}
            ]
            fixed, _ = await ai_client.chat(model_id, fix_messages)
            files = RobustFileParser.parse(fixed)
        
        # ===== CHECKPOINT 4: Deploy =====
        task.add_checkpoint("deploy", {"mode": deploy_mode, "files": list(files.keys())})
        await _update_status(status_msg, task, 4, 5, "Deploying...")
        
        metadata = {
            "task_id": task_id, "description": task.description,
            "model": model_id, "files": list(files.keys())
        }
        
        if deploy_mode == 'local' or deploy_mode == 'both':
            zip_path, zip_size = await LocalAgent.create_package(task_id, files, metadata)
            task.local_path = str(zip_path)
            task.files_created = list(files.keys())
        
        if deploy_mode == 'github' or deploy_mode == 'both':
            # GitHub deploy
            success, username = await github.get_user()
            if success:
                repo_name = _smart_repo_name(task.description, user_id)
                success, repo_url = await github.create_repo(repo_name, f"Auto: {task.description[:100]}")
                if success or "already exists" in str(repo_url).lower():
                    success_push, final_url = await github.push_files(
                        username, repo_name, files,
                        f"Add {len(files)} files: {task.description[:50]}"
                    )
                    if success_push:
                        task.repo_url = final_url
                        if not task.files_created:
                            task.files_created = list(files.keys())
        
        # ===== CHECKPOINT 5: Complete =====
        task.status = "completed"
        task.result = "Success"
        state.usage.record(
            task.metrics.get('input_tokens', 0),
            task.metrics.get('output_tokens', 0),
            task.metrics.get('latency', 0),
            model_id,
            SmartModelRouter.detect_task_type(task.description, state.history)
        )
        state.add_note(f"Completed: {task.description[:50]}", success=True)
        SmartModelRouter.record_result(model_id, success=True)
        
        # Build success message
        file_summary = "\n".join(f"• `{f}`" for f in task.files_created[:8])
        if len(task.files_created) > 8:
            file_summary += f"\n• ...+{len(task.files_created)-8} more"
        
        result_msg = f"""✅ *Agent Task Completed!*
━━━━━━━━━━━━━━━━━━━━━━
🆔 `{task_id}`
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
        
        # Send files
        if task.local_path:
            with open(task.local_path, 'rb') as f:
                bio = io.BytesIO(f.read())
            bio.name = f"{task_id}.zip"
            await update.message.reply_document(document=bio, caption=f"📦 {len(files)} files")
        
        # Record usage
        await state_store.save(user_id)
        
    except Exception as e:
        task.status = "failed"
        task.error = str(e)[:300]
        state.add_note(f"Failed: {task.description[:50]} — {str(e)[:100]}", success=False)
        SmartModelRouter.record_result(task.model_used or state.current_model, success=False)
        
        error_msg = f"""❌ *Agent Task Failed*
━━━━━━━━━━━━━━━━━━━━━━
🆔 `{task.task_id}`
⚠️ Error: `{task.error}`

💡 Try:
• Simplify the task description
• Use `/agent local` for ZIP output
• Check GitHub token if using github mode

🔁 Auto-retry: `{task.auto_retry_count}/2`"""
        
        await status_msg.edit_text(error_msg, parse_mode=TPM.MARKDOWN)
        await state_store.save(user_id)

async def _update_status(msg: Message, task: AgentTask, step: int, total: int, text: str):
    """Update progress with rate-limit friendly edits."""
    try:
        await msg.edit_text(
            f"🤖 *Agent — {step}/{total}*\n━━━━━━━━\n🆔 `{task.task_id}`\n⏳ {text}\n\n⏱ Started: {task.created_at[:16]}",
            parse_mode=TPM.MARKDOWN
        )
    except BadRequest:
        pass  # Message unchanged, continue

def _smart_repo_name(desc: str, user_id: int) -> str:
    """Generate GitHub repo name from description."""
    words = re.findall(r'[a-zA-Z]+', desc.lower())
    keywords = [w for w in words if len(w) > 3 and w not in ['create', 'make', 'build', 'write', 'the', 'and', 'with']][:5]
    name = '-'.join(keywords) if keywords else f"project-{user_id % 1000}"
    return name[:30].strip('-') or f"fizzpop-{int(time.time())%10000}"

async def _send_stats(update: Update, state: ConversationState):
    """Send usage statistics."""
    s = state.usage
    avg_lat = s.avg_latency
    
    stats = f"""📊 *Usage Statistics*
━━━━━━━━━━━━━━━━━━━━━━
🔢 Requests: `{s.total_requests}`
📝 Input tokens: `{s.total_input_tokens}`
💬 Output tokens: `{s.total_output_tokens}`
📦 Total: `{s.total_tokens}`
⏱ Avg latency: `{avg_lat:.2f}s`

🤖 Models used:
{chr(10).join(f"• `{m}`: {c}x" for m, c in sorted(s.models_used.items(), key=lambda x:-x[1])[:5])}

📅 First: `{s.first_seen[:10]}`
🕐 Last: `{s.last_active[:16]}`}

💡 Tip: Use `/reset` to clear history if context gets confused."""
    
    await send_with_fallback(update, stats)

# ============================================================================
# 📨 MAIN MESSAGE HANDLER (Smart routing)
# ============================================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Smart message handler with auto-routing."""
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state = get_user_state(user_id)
    
    # Rate limit check
    allowed, msg = rate_limit_check(update)
    if not allowed:
        await update.message.reply_text(msg, parse_mode=TPM.MARKDOWN)
        return
    
    # Auto-detect and route
    if text.startswith('/'):
        return  # Let command handlers manage
    
    # Add to history
    state.history.append({"role": "user", "content": text})
    if len(state.history) > Config.MAX_HISTORY * 2:
        # Compress old history
        if Config.CONTEXT_COMPRESSION:
            state.history = ContextCompressor.compress_history(state.history, max_tokens=5000)
        else:
            state.history = state.history[-Config.MAX_HISTORY * 2:]
    
    # Show typing
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    
    # Status message for long responses
    status_msg = await update.message.reply_text("⏳ *Đang suy nghĩ...*", parse_mode=TPM.MARKDOWN)
    
    try:
        # Smart model selection
        model_id = state.current_model
        if state.auto_model:
            task_type = SmartModelRouter.detect_task_type(text, state.history)
            model_id, _ = SmartModelRouter.select_best_model(text, state.history, state.budget_conscious)
        
        # Prepare messages
        system_prompt = state.get_adaptive_prompt(SYSTEM_PROMPT if state.mode == 'chat' else AGENT_PROMPT)
        messages = [{"role": "system", "content": system_prompt}] + state.history[-Config.MAX_HISTORY:]
        
        # Call AI with streaming
        async def stream_callback(preview: str):
            try:
                await status_msg.edit_text(f"🤖 *Đang trả lời...*\n\n`{preview}`\n\n⏱ Typing...", parse_mode=TPM.MARKDOWN)
            except:
                pass
        
        response, metrics = await ai_client.chat(
            model_id, messages, 
            stream=Config.STREAMING_RESPONSES,
            status_callback=stream_callback if Config.STREAMING_RESPONSES else None
        )
        
        # Add to history
        state.history.append({"role": "assistant", "content": response})
        if len(state.history) > Config.MAX_HISTORY * 2:
            state.history = state.history[-Config.MAX_HISTORY * 2:]
        
        # Record usage
        state.usage.record(
            metrics.get('input_tokens', 0),
            metrics.get('output_tokens', 0),
            metrics.get('latency', 0),
            model_id,
            SmartModelRouter.detect_task_type(text, state.history)
        )
        SmartModelRouter.record_result(model_id, success=True)
        
        # Format response
        model_display = _get_model_display(state.mode, model_id)
        header = f"🤖 *{model_display}*\n{'━' * 20}\n\n"
        footer = f"\n\n⏱ `{metrics.get('latency', 0):.2f}s` | 📝 `{metrics.get('output_tokens', 0)}` tokens"
        full_text = header + response + footer
        
        # Send with fallback for long content
        await status_msg.delete()
        await send_with_fallback(update, full_text)
        
        # Save state
        await state_store.save(user_id)
        
    except Exception as e:
        logging.error(f"Error: {e}")
        await status_msg.edit_text(f"⚠️ *Error:* `{str(e)[:200]}`\n\n💡 Try `/reset` or change model.", parse_mode=TPM.MARKDOWN)
        state.add_note(f"Error: {str(e)[:100]}", success=False)
        await state_store.save(user_id)

# ============================================================================
# 📋 MODEL CONFIG (Simplified for single-file)
# ============================================================================

CATEGORY_EMOJI = {
    "GPT": "🟢", "Claude": "🟣", "Gemini": "🔵", "GLM": "🟡",
    "Qwen": "🟠", "MiniMax": "🔴", "Mistral": "⚪", "DeepSeek": "⚫",
    "Khác": "🟦", "TTS": "🔊", "Embedding": "📊"
}

MODE_CONFIG = {
    "chat": {
        "name": "💬 Chat",
        "models": [
            ("DeepSeek", "deepseek-3.2", "DeepSeek V3"),
            ("GLM", "glm4.7", "GLM-4.7"),
            ("Mistral", "mistral-medium-3.5-128b", "Mistral Medium 3.5"),
            ("Qwen", "qwen3-coder-480b-a35b-instruct", "Qwen3 Coder 480B"),
            ("Claude", "claude-sonnet-4.6", "Claude Sonnet 4.6"),
            ("GPT", "gpt-5.4", "GPT-5.4"),
            ("GPT", "gpt-5.4-mini", "GPT-5.4 Mini"),
            ("Mistral", "mistral-small-4-119b-2603", "Mistral Small 4"),
        ],
        "default": Config.DEFAULT_CHAT_MODEL,
    },
    "agent": {
        "name": "🤖 Agent", 
        "models": [
            ("Qwen", "qwen3-coder-480b-a35b-instruct", "Qwen3 Coder 480B"),
            ("Mistral", "mistral-medium-3.5-128b", "Mistral Medium 3.5"),
            ("DeepSeek", "deepseek-3.2", "DeepSeek V3"),
            ("Claude", "claude-sonnet-4.6", "Claude Sonnet 4.6"),
            ("GPT", "gpt-5.4", "GPT-5.4"),
        ],
        "default": Config.DEFAULT_AGENT_MODEL,
    },
    "embed": {
        "name": "📊 Embed",
        "models": [
            ("Embedding", "text-embedding-3-small", "Text Embed 3 Small"),
            ("Gemini", "gemini-embedding-2-preview", "Gemini Embed 2"),
        ],
        "default": "text-embedding-3-small",
    },
    "tts": {
        "name": "🔊 TTS",
        "models": [
            ("TTS", "google-tts/vi", "Google TTS Vietnamese"),
            ("TTS", "vi-VN-HoaiMyNeural", "HoaiMy Neural"),
        ],
        "default": "google-tts/vi",
    },
}

def _get_model_display(mode: str, model_id: str) -> str:
    """Get display name with emoji."""
    for cat, mid, display in MODE_CONFIG.get(mode, {}).get("models", []):
        if mid == model_id:
            return f"{CATEGORY_EMOJI.get(cat, '⚪')} {display}"
    return model_id

# ============================================================================
# 🔄 CLEANUP & SHUTDOWN
# ============================================================================

async def periodic_cleanup():
    """Background task to cleanup old files."""
    while True:
        await asyncio.sleep(3600)  # Every hour
        state_store.cleanup_old_tasks(Config.ZIP_RETENTION_HOURS)
        # Clean old ZIPs
        cutoff = time.time() - Config.ZIP_RETENTION_HOURS * 3600
        for zip_file in Config.WORK_DIR.glob("*.zip"):
            if zip_file.stat().st_mtime < cutoff:
                zip_file.unlink()
                logging.debug(f"🗑️ Cleaned: {zip_file.name}")

# ============================================================================
# 🚀 MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry — all in one file!"""
    Config.init()
    logging.info("🚀 Starting FizzPop AI Agent Bot v7.0 (Single-File Edition)")
    
    # Create app
    app = (
        ApplicationBuilder()
        .token(Config.BOT_TOKEN)
        .concurrent_updates(True)
        .get_updates_read_timeout(Config.API_TIMEOUT)
        .build()
    )
    
    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", lambda u, c: send_with_fallback(u, HELP_TEXT)))
    app.add_handler(CommandHandler("models", show_models))
    app.add_handler(CommandHandler("agent", agent_command))
    app.add_handler(CommandHandler("stats", lambda u, c: _send_stats(u, get_user_state(u.effective_user.id))))
    app.add_handler(CommandHandler("reset", lambda u, c: _handle_reset(u, get_user_state(u.effective_user.id))))
    
    # Callbacks
    app.add_handler(CallbackQueryHandler(model_callback))
    
    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error handler
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logging.error(f"Update {update} caused error: {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text("⚠️ Có lỗi xảy ra. Thử lại hoặc /reset.")
    
    app.add_error_handler(error_handler)
    
    # Post-init: start cleanup task
    async def post_init(app: Application):
        app.bot_data['ai_client'] = ai_client
        app.bot_data['github'] = github
        asyncio.create_task(periodic_cleanup())
        logging.info("✅ Bot initialized")
    
    app.post_init = post_init
    
    # Post-shutdown: cleanup
    async def post_shutdown(app: Application):
        await ai_client.close()
        await github.close()
        await state_store.save_all()
        logging.info("🔒 Bot shutdown complete")
    
    app.post_shutdown = post_shutdown
    
    # Run
    logging.info("✅ Bot is running. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)

# Help text constant
HELP_TEXT = """📖 *Hướng Dẫn FizzPop v7.0*
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
🤖 FizzPop v7.0 — Single-File Power ✨"""

def _handle_reset(update: Update, state: ConversationState):
    """Handle reset command."""
    state.history = []
    state.agent_tasks = state.agent_tasks[-5:]  # Keep last 5 tasks
    return update.message.reply_text("🗑️ *Đã reset!*\n\nLịch sử chat đã xóa. Tasks cũ giữ lại 5 cái gần nhất.", parse_mode=TPM.MARKDOWN)

if __name__ == '__main__':
    main()
