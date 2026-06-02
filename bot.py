#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 🤖 Denia Bot v9.0 — ULTIMATE PRO EDITION                     ║
║    Multi-Provider AI Agent | Auto-Fix | Smart Deploy | Professional Workflow ║
║          OpenCode + NVIDIA NIM | Context-Aware | Self-Improving              ║
╚══════════════════════════════════════════════════════════════════════════════╝
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
import signal
import platform
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable, Set
from collections import defaultdict

import aiohttp
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, Message, ChatAction,
    InputFile
)
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from telegram.constants import ParseMode as TPM, MessageLimit
from telegram.error import BadRequest, TimedOut, NetworkError

# ============================================================================
# 🔐 CONFIGURATION — Updated with your exact credentials
# ============================================================================

class Config:
    """Central configuration with your provided API endpoints."""

    # Telegram Bot Token
    BOT_TOKEN = "8909561772:AAGQgxrbvXbi-RACF4_Z7iiS4R7NA6Za6wU"

    # OpenCode Provider (Free Tier)
    PROVIDER_OPENCODE_BASE = "https://opencode.ai/zen"
    PROVIDER_OPENCODE_KEY = "sk-F9v1PpTAyB4CVvaXYp1894RnUdicmNKAx6pZwitfBuWWUkXehlOC0VNcd0Ivt3U8"

    # NVIDIA NIM Provider (Free Tier)
    PROVIDER_NVIDIA_BASE = "https://integrate.api.nvidia.com/v1"
    PROVIDER_NVIDIA_KEY = "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"

    # GitHub Integration
    GITHUB_TOKEN = "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"

    # Working Directory
    WORK_DIR = Path("denia_data_v9")

    # Limits & Performance
    MAX_HISTORY = 60
    MAX_TOKENS_PER_CALL = 8192
    API_TIMEOUT = 300  # Increased for complex agent tasks
    STREAM_CHUNK_SIZE = 256

    # Rate Limiting
    USER_REQUESTS_PER_MIN = 25
    GLOBAL_REQUESTS_PER_MIN = 400

    # Storage & Cleanup
    ZIP_RETENTION_HOURS = 72
    MAX_SELF_NOTES = 200
    STATE_SAVE_INTERVAL = 300  # Auto-save every 5 minutes

    # Agent Settings
    AGENT_MAX_RETRIES = 3
    AGENT_RETRY_DELAY = 2.0
    MAX_AGENT_FILES = 20

    # Default Models
    DEFAULT_CHAT_MODEL = "z-ai/glm-5.1"
    DEFAULT_AGENT_MODEL = "minimaxai/minimax-m2.7"

    # Feature Flags
    AUTO_MODEL_SELECTION = True
    CONTEXT_COMPRESSION = True
    STREAMING_RESPONSES = True
    AUTO_DEPENDENCY_DETECT = True

    @classmethod
    def init(cls):
        cls.WORK_DIR.mkdir(parents=True, exist_ok=True)
        (cls.WORK_DIR / "agents").mkdir(exist_ok=True)
        (cls.WORK_DIR / "zips").mkdir(exist_ok=True)
        (cls.WORK_DIR / "logs").mkdir(exist_ok=True)

        log_file = cls.WORK_DIR / "logs" / f"denia_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8', mode='a'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logging.getLogger("telegram.ext.Application").setLevel(logging.WARNING)
        logging.info(f"🚀 Denia Bot v9.0 Pro initialized | Work dir: {cls.WORK_DIR.resolve()}")

# ============================================================================
# 🧠 TASK CLASSIFICATION & MODEL ROUTING
# ============================================================================

class TaskType(Enum):
    CHAT = "chat"
    CODE_GEN = "code_gen"
    CODE_FIX = "code_fix"
    CODE_REVIEW = "code_review"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    SHORT_ANSWER = "short"
    LONG_FORM = "long_form"
    AGENT_TASK = "agent_task"
    DEBUG = "debug"
    ARCHITECTURE = "architecture"

@dataclass
class ModelProfile:
    model_id: str
    display_name: str
    category: str
    provider: str  # 'opencode' or 'nvidia'
    strengths: Set[TaskType]
    cost_tier: int  # 1=free/cheap, 2=standard, 3=premium
    speed_tier: int  # 1=fast, 2=medium, 3=slow
    max_context: int = 128000
    supports_streaming: bool = True
    supports_tools: bool = False
    usage_count: int = 0
    success_rate: float = 1.0
    avg_latency: float = 0.0

    def score_for_task(self, task_type: TaskType, budget_conscious: bool = True, 
                       need_streaming: bool = True, complexity: int = 2) -> float:
        score = 0.0

        # Task match (40%)
        if task_type in self.strengths:
            score += 0.40
        elif any(t in self.strengths for t in self._related_tasks(task_type)):
            score += 0.25

        # Speed (20%) - faster is better for simple tasks
        if complexity <= 2:
            score += (4 - self.speed_tier) / 3 * 0.20
        else:
            score += (self.speed_tier) / 3 * 0.10  # For complex tasks, accuracy > speed

        # Cost/Budget (20%)
        if budget_conscious:
            score += (4 - self.cost_tier) / 3 * 0.20
        else:
            score += 0.15

        # Reliability (10%)
        score += self.success_rate * 0.10

        # Streaming support (5%)
        if need_streaming and self.supports_streaming:
            score += 0.05

        # Latency penalty/bonus (5%)
        if self.avg_latency > 0:
            score += max(0, 1.0 - (self.avg_latency / 30)) * 0.05

        return min(1.0, score)

    @staticmethod
    def _related_tasks(task_type: TaskType) -> List[TaskType]:
        relations = {
            TaskType.CODE_GEN: [TaskType.AGENT_TASK, TaskType.ARCHITECTURE],
            TaskType.CODE_FIX: [TaskType.DEBUG, TaskType.CODE_REVIEW],
            TaskType.ANALYSIS: [TaskType.LONG_FORM, TaskType.CODE_REVIEW],
            TaskType.AGENT_TASK: [TaskType.CODE_GEN, TaskType.ARCHITECTURE],
        }
        return relations.get(task_type, [])

# Model Registry — Updated with your exact endpoints
MODEL_REGISTRY: Dict[str, ModelProfile] = {
    # OpenCode Models (Free)
    "minimax-m2.5-free": ModelProfile(
        "minimax-m2.5-free", "MiniMax M2.5 Free", "MiniMax", "opencode",
        {TaskType.CHAT, TaskType.SHORT_ANSWER, TaskType.CREATIVE, TaskType.CODE_GEN},
        1, 1, 128000, True, False
    ),

    # NVIDIA NIM Models (Free Tier)
    "z-ai/glm-5.1": ModelProfile(
        "z-ai/glm-5.1", "GLM-5.1", "GLM", "nvidia",
        {TaskType.CHAT, TaskType.ANALYSIS, TaskType.CODE_GEN, TaskType.CODE_FIX, TaskType.LONG_FORM},
        2, 1, 128000, True, True
    ),
    "minimaxai/minimax-m2.7": ModelProfile(
        "minimaxai/minimax-m2.7", "MiniMax M2.7", "MiniMax", "nvidia",
        {TaskType.CODE_GEN, TaskType.CODE_FIX, TaskType.ANALYSIS, TaskType.AGENT_TASK, TaskType.ARCHITECTURE},
        2, 2, 128000, True, True
    ),
    "mistralai/mistral-large-3-675b-instruct-2512": ModelProfile(
        "mistralai/mistral-large-3-675b-instruct-2512", "Mistral Large 3", "Mistral", "nvidia",
        {TaskType.CODE_GEN, TaskType.ANALYSIS, TaskType.LONG_FORM, TaskType.AGENT_TASK, TaskType.CODE_REVIEW},
        2, 2, 256000, True, True
    ),
}

class SmartModelRouter:
    """Intelligent model selection based on task analysis."""

    _task_keywords = {
        TaskType.CODE_FIX: ['fix', 'bug', 'error', 'debug', 'sửa', 'lỗi', 'crash', 'exception', 'traceback'],
        TaskType.CODE_REVIEW: ['review', 'review code', 'đánh giá code', 'optimize', 'refactor', 'clean code'],
        TaskType.CODE_GEN: ['code', 'function', 'def ', 'class ', 'api', 'endpoint', 'script', 'write a program',
                           'viết code', 'tạo hàm', 'tạo class', 'javascript', 'python', 'react', 'fastapi'],
        TaskType.AGENT_TASK: ['agent', 'full project', 'complete app', 'build a bot', 'tạo project', 
                             'system', 'microservice', 'fullstack', 'backend', 'frontend'],
        TaskType.ARCHITECTURE: ['architecture', 'design pattern', 'structure', 'folder structure', 'database schema'],
        TaskType.ANALYSIS: ['analyze', 'phân tích', 'compare', 'so sánh', 'explain', 'giải thích', 'review', 'evaluate'],
        TaskType.CREATIVE: ['story', 'poem', 'essay', 'creative', 'viết truyện', 'viết bài', 'content', 'blog'],
        TaskType.SHORT_ANSWER: ['?', 'là gì', 'what is', 'how to', 'tại sao', 'how do', 'short'],
        TaskType.DEBUG: ['debug', 'traceback', 'stack trace', 'not working', 'broken', 'fails'],
    }

    @classmethod
    def detect_task_type(cls, text: str, context: Optional[List[Dict]] = None) -> TaskType:
        text_lower = text.lower()
        scores = defaultdict(int)

        for task_type, keywords in cls._task_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    scores[task_type] += 1

        # Check for agent-level complexity
        agent_indicators = ['multiple files', 'project', 'app', 'system', 'deploy', 'github', 'repo', 
                           'full', 'complete solution', 'end to end', 'từ đầu đến cuối']
        if any(ind in text_lower for ind in agent_indicators) and scores[TaskType.CODE_GEN] > 0:
            scores[TaskType.AGENT_TASK] += 3

        if scores:
            best_task = max(scores.items(), key=lambda x: x[1])[0]
            return best_task

        # Fallback based on length and context
        if len(text) < 80:
            return TaskType.SHORT_ANSWER
        elif len(text) > 800:
            return TaskType.LONG_FORM
        return TaskType.CHAT

    @classmethod
    def select_best_model(cls, user_input: str, history: Optional[List[Dict]] = None,
                         budget_conscious: bool = True, need_streaming: bool = True,
                         preferred_provider: Optional[str] = None) -> Tuple[str, str, str]:
        """Returns (model_id, display_name, provider)"""
        task_type = cls.detect_task_type(user_input, history)
        complexity = cls._estimate_complexity(user_input)

        candidates = []
        for model_id, profile in MODEL_REGISTRY.items():
            # Skip if provider preference doesn't match
            if preferred_provider and profile.provider != preferred_provider:
                continue

            score = profile.score_for_task(
                task_type, budget_conscious, need_streaming, complexity
            )

            # Boost for exact task match
            if task_type in profile.strengths:
                score += 0.15

            # Recent success rate bonus
            if profile.success_rate > 0.95:
                score += 0.05

            candidates.append((model_id, profile.display_name, profile.provider, score, profile))

        candidates.sort(key=lambda x: -x[3])

        if not candidates:
            # Ultimate fallback
            return "z-ai/glm-5.1", "GLM-5.1", "nvidia"

        winner = candidates[0]
        logging.info(f"🎯 Router selected: {winner[0]} (score: {winner[3]:.2f}) for task: {task_type.value}")
        return winner[0], winner[1], winner[2]

    @classmethod
    def record_result(cls, model_id: str, success: bool, latency: float = 0.0):
        if model_id in MODEL_REGISTRY:
            profile = MODEL_REGISTRY[model_id]
            profile.usage_count += 1
            alpha = 0.15
            profile.success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * profile.success_rate
            if latency > 0:
                profile.avg_latency = alpha * latency + (1 - alpha) * (profile.avg_latency or latency)

    @staticmethod
    def _estimate_complexity(text: str) -> int:
        """Estimate complexity 1-5 based on request."""
        score = 1
        if len(text) > 500: score += 1
        if len(text) > 1500: score += 1
        if any(k in text.lower() for k in ['database', 'auth', 'deploy', 'microservice', 'architecture']): score += 1
        if any(k in text.lower() for k in ['multiple', 'full stack', 'system', 'complex']): score += 1
        return min(5, score)

# ============================================================================
# 🗜️ ADVANCED CONTEXT COMPRESSOR
# ============================================================================

class ContextCompressor:
    CHARS_PER_TOKEN = 3.8  # More accurate estimate

    @classmethod
    def estimate_tokens(cls, messages: List[Dict]) -> int:
        total_chars = sum(len(m.get('content', '')) for m in messages)
        return int(len(messages) * 4 + total_chars / cls.CHARS_PER_TOKEN)

    @classmethod
    def compress_history(cls, history: List[Dict], max_tokens: int = 6000, 
                        preserve_system: bool = True) -> List[Dict]:
        if not history or len(history) <= 12:
            return history

        # Separate system messages
        system_msgs = [m for m in history if m.get('role') == 'system']
        conversation = [m for m in history if m.get('role') != 'system']

        # Always keep recent messages
        keep_recent = min(12, len(conversation))
        recent = conversation[-keep_recent:]
        old_messages = conversation[:-keep_recent]

        if not old_messages:
            return system_msgs + recent

        # Summarize old messages in chunks
        chunks = []
        chunk_size = 5
        for i in range(0, len(old_messages), chunk_size):
            chunk = old_messages[i:i+chunk_size]
            chunk_text = " | ".join([
                f"{m['role']}: {m['content'][:120]}..." if len(m['content']) > 120 
                else f"{m['role']}: {m['content']}"
                for m in chunk
            ])
            chunks.append(chunk_text)

        summary = f"[Previous conversation summary ({len(old_messages)} messages)]: " + " | ".join(chunks[:8])

        compressed = system_msgs + [{"role": "system", "content": summary}] + recent
        return compressed

    @classmethod
    def trim_for_agent(cls, history: List[Dict], max_messages: int = 20) -> List[Dict]:
        """Aggressive trim for agent mode to save tokens for code generation."""
        if len(history) <= max_messages:
            return history
        return history[:2] + history[-(max_messages-2):]  # Keep first 2 (system/context) + recent

# ============================================================================
# 🔄 STREAMING & API HANDLER
# ============================================================================

class APIProvider:
    """Unified API provider interface."""

    def __init__(self, provider: str):
        self.provider = provider
        if provider == "opencode":
            self.base = Config.PROVIDER_OPENCODE_BASE
            self.key = Config.PROVIDER_OPENCODE_KEY
        else:  # nvidia
            self.base = Config.PROVIDER_NVIDIA_BASE
            self.key = Config.PROVIDER_NVIDIA_KEY

    def headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.key}"
        }

    def build_payload(self, model_id: str, messages: List[Dict], 
                     temperature: float = 0.7, max_tokens: int = None,
                     stream: bool = True, **extra) -> Dict:
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or Config.MAX_TOKENS_PER_CALL,
            "stream": stream
        }
        if extra:
            payload.update(extra)
        return payload

class StreamingHandler:
    """Robust streaming handler with fallback and retry logic."""

    @staticmethod
    async def chat_complete(model_id: str, provider: str, messages: List[Dict],
                            status_msg: Optional[Message] = None,
                            progress_callback: Optional[Callable] = None,
                            temperature: float = 0.7,
                            max_retries: int = 2) -> Tuple[str, Dict]:
        """Main chat completion with streaming support."""
        api = APIProvider(provider)
        payload = api.build_payload(model_id, messages, temperature, stream=True)

        for attempt in range(max_retries + 1):
            try:
                return await StreamingHandler._stream_request(
                    api, payload, status_msg, progress_callback
                )
            except Exception as e:
                if attempt < max_retries:
                    wait = Config.AGENT_RETRY_DELAY * (2 ** attempt)
                    logging.warning(f"Stream attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
                    if status_msg and attempt == 0:
                        try:
                            await status_msg.edit_text(
                                f"⚠️ API hiccup, retrying... ({attempt+1}/{max_retries})",
                                parse_mode=TPM.MARKDOWN
                            )
                        except:
                            pass
                    await asyncio.sleep(wait)
                else:
                    logging.error(f"All streaming attempts failed: {e}")
                    # Final fallback to non-streaming
                    return await StreamingHandler._non_stream_request(api, payload)

        return "Error: All API attempts failed", {"error": True, "latency": 0}

    @staticmethod
    async def _stream_request(api: APIProvider, payload: Dict,
                              status_msg: Optional[Message] = None,
                              progress_callback: Optional[Callable] = None) -> Tuple[str, Dict]:
        accumulated = []
        start_time = time.time()
        last_update = 0
        update_interval = 1.5  # Update Telegram every 1.5s

        timeout = aiohttp.ClientTimeout(total=Config.API_TIMEOUT, connect=30)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{api.base}/chat/completions",
                headers=api.headers(),
                json=payload
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"HTTP {resp.status}: {text[:300]}")

                async for line in resp.content:
                    line = line.decode('utf-8', errors='ignore').strip()
                    if not line or line == 'data: [DONE]':
                        continue
                    if line.startswith('data: '):
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk.get('choices', [{}])[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                accumulated.append(content)

                                # Progress updates
                                now = time.time()
                                if progress_callback and (now - last_update) > update_interval:
                                    preview = ''.join(accumulated)[-300:]
                                    try:
                                        await progress_callback(preview)
                                    except:
                                        pass
                                    last_update = now
                        except json.JSONDecodeError:
                            continue

        final_text = ''.join(accumulated)
        latency = time.time() - start_time

        metrics = {
            'latency': round(latency, 2),
            'output_chars': len(final_text),
            'output_tokens': int(len(final_text) / 4),
            'streaming': True,
            'success': True
        }

        return final_text, metrics

    @staticmethod
    async def _non_stream_request(api: APIProvider, payload: Dict) -> Tuple[str, Dict]:
        """Fallback non-streaming request."""
        start_time = time.time()
        payload["stream"] = False

        timeout = aiohttp.ClientTimeout(total=Config.API_TIMEOUT, connect=30)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{api.base}/chat/completions",
                headers=api.headers(),
                json=payload
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"HTTP {resp.status}: {text[:300]}")

                result = await resp.json()

        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        latency = time.time() - start_time

        return content, {
            'latency': round(latency, 2),
            'output_chars': len(content),
            'output_tokens': int(len(content) / 4),
            'streaming': False,
            'success': True
        }

    @staticmethod
    async def agent_generate(model_id: str, provider: str, messages: List[Dict],
                             step_name: str = "generating",
                             status_msg: Optional[Message] = None) -> Tuple[str, Dict]:
        """Specialized generation for agent mode with step tracking."""
        if status_msg:
            try:
                await status_msg.edit_text(
                    f"🤖 *Agent Step: {step_name}*\n⏳ Processing with {model_id}...",
                    parse_mode=TPM.MARKDOWN
                )
            except:
                pass

        return await StreamingHandler.chat_complete(
            model_id, provider, messages, status_msg, None, temperature=0.6
        )

# ============================================================================
# 📊 DATA MODELS
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
    agent_tasks_completed: int = 0
    agent_tasks_failed: int = 0

    def record(self, input_tokens: int, output_tokens: int, latency: float, 
               model_id: str, task_type: TaskType):
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

@dataclass
class AgentCheckpoint:
    step: str
    timestamp: str
    status: str  # success, warning, error
    data: Dict[str, Any]
    duration_ms: int = 0

@dataclass
class AgentTask:
    task_id: str
    user_id: int
    description: str
    status: str = "pending"  # pending, analyzing, planning, coding, validating, fixing, deploying, completed, failed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    checkpoints: List[AgentCheckpoint] = field(default_factory=list)
    result: Optional[str] = None
    error: Optional[str] = None
    error_details: Optional[str] = None
    files_created: List[str] = field(default_factory=list)
    file_contents: Dict[str, str] = field(default_factory=dict)
    local_path: Optional[str] = None
    repo_url: Optional[str] = None
    repo_name: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    model_used: Optional[str] = None
    provider_used: Optional[str] = None
    auto_retry_count: int = 0
    deploy_mode: str = "local"
    detected_language: str = "python"
    dependencies: List[str] = field(default_factory=list)

    def add_checkpoint(self, step: str, status: str, data: Dict, duration_ms: int = 0):
        self.checkpoints.append(AgentCheckpoint(
            step=step,
            timestamp=datetime.now().isoformat(),
            status=status,
            data=data,
            duration_ms=duration_ms
        ))
        self.updated_at = datetime.now().isoformat()
        # Keep only last 10 checkpoints to save memory
        if len(self.checkpoints) > 10:
            self.checkpoints = self.checkpoints[-10:]

    def to_summary(self) -> str:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "files": len(self.files_created),
            "retries": self.auto_retry_count,
            "model": self.model_used,
            "deploy": self.deploy_mode
        }

@dataclass
class ConversationState:
    history: List[Dict[str, str]] = field(default_factory=list)
    mode: str = "chat"  # chat, agent, embed, tts
    current_model: str = Config.DEFAULT_CHAT_MODEL
    current_provider: str = "nvidia"
    auto_model: bool = True
    usage: UsageStats = field(default_factory=UsageStats)
    agent_tasks: List[AgentTask] = field(default_factory=list)
    preferred_style: str = "balanced"  # concise, balanced, verbose
    language_hint: str = "auto"
    budget_conscious: bool = True
    self_notes: List[str] = field(default_factory=list)
    error_patterns: Dict[str, int] = field(default_factory=dict)
    successful_patterns: Dict[str, int] = field(default_factory=dict)
    agent_deploy_mode: str = "local"  # local, github, both
    last_model_suggestion: Optional[str] = None

    def add_note(self, note: str, success: bool = True):
        sig = note[:200].strip()
        if success:
            self.successful_patterns[sig] = self.successful_patterns.get(sig, 0) + 1
            if sig not in self.self_notes:
                self.self_notes.append(f"✅ {sig}")
        else:
            self.error_patterns[sig] = self.error_patterns.get(sig, 0) + 1
            if sig not in self.self_notes:
                self.self_notes.append(f"❌ {sig}")

        if len(self.self_notes) > Config.MAX_SELF_NOTES:
            self.self_notes = self.self_notes[-Config.MAX_SELF_NOTES:]

    def get_adaptive_prompt(self, base: str, mode: str = "chat") -> str:
        prompt = base

        if self.preferred_style == "concise":
            prompt += "\n\n[STYLE: Be extremely concise. Minimal explanations. Focus on code quality.]"
        elif self.preferred_style == "verbose":
            prompt += "\n\n[STYLE: Provide detailed explanations, examples, and thorough documentation.]"
        else:
            prompt += "\n\n[STYLE: Balanced — clear explanations with efficient code.]"

        if self.language_hint == "vi":
            prompt += "\n\n[LANGUAGE: Respond in Vietnamese for natural language, English for all code.]"
        elif self.language_hint == "auto":
            prompt += "\n\n[LANGUAGE: Detect user's language and respond accordingly. Code always in English.]"

        # Inject learned patterns
        if self.successful_patterns:
            top = sorted(self.successful_patterns.items(), key=lambda x: -x[1])[:3]
            if top:
                prompt += "\n\n[PREFERRED APPROACHES:\n" + "\n".join(f"- {p}" for p, _ in top) + "]"

        if mode == "agent":
            prompt += "\n\n[AGENT MODE: You MUST output complete, runnable code. Use file markers. Include error handling.]"

        return prompt

    def get_recent_context(self, max_messages: int = 30) -> List[Dict]:
        """Get recent history with smart compression."""
        if len(self.history) <= max_messages:
            return self.history
        if Config.CONTEXT_COMPRESSION:
            return ContextCompressor.compress_history(self.history)
        return self.history[-max_messages:]

# ============================================================================
# 🗄️ PERSISTENT STATE STORE
# ============================================================================

class StateStore:
    """Thread-safe async state persistence with auto-save."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._cache: Dict[int, ConversationState] = {}
        self._lock = asyncio.Lock()
        self._dirty: Set[int] = set()
        self._last_save = time.time()
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for uid_str, state_data in data.items():
                    uid = int(uid_str)
                    # Reconstruct nested dataclasses
                    if 'usage' in state_data and isinstance(state_data['usage'], dict):
                        state_data['usage'] = UsageStats(**state_data['usage'])
                    if 'agent_tasks' in state_data and isinstance(state_data['agent_tasks'], list):
                        tasks = []
                        for t in state_data['agent_tasks']:
                            if 'checkpoints' in t:
                                t['checkpoints'] = [AgentCheckpoint(**c) for c in t['checkpoints']]
                            tasks.append(AgentTask(**t))
                        state_data['agent_tasks'] = tasks
                    self._cache[uid] = ConversationState(**state_data)
                logging.info(f"📥 Loaded {len(self._cache)} user states from {self.file_path}")
            except Exception as e:
                logging.warning(f"⚠️ Failed to load states: {e}")
                self._cache = {}

    async def _save(self, force: bool = False):
        async with self._lock:
            if not force and not self._dirty:
                return

            try:
                data = {}
                for uid, state in self._cache.items():
                    state_dict = asdict(state)
                    # Convert dataclasses to dicts
                    state_dict['usage'] = asdict(state.usage)
                    state_dict['agent_tasks'] = [
                        {**asdict(t), 'checkpoints': [asdict(c) for c in t.checkpoints]}
                        for t in state.agent_tasks
                    ]
                    data[str(uid)] = state_dict

                temp_file = self.file_path.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                # Atomic replace
                temp_file.replace(self.file_path)
                self._dirty.clear()
                self._last_save = time.time()
                logging.debug("💾 State saved")
            except Exception as e:
                logging.error(f"❌ Failed to save states: {e}")

    async def save_user(self, user_id: int):
        self._dirty.add(user_id)
        # Auto-save if enough time passed
        if time.time() - self._last_save > Config.STATE_SAVE_INTERVAL:
            await self._save()

    async def force_save(self):
        await self._save(force=True)

    def get(self, user_id: int) -> ConversationState:
        if user_id not in self._cache:
            self._cache[user_id] = ConversationState()
        return self._cache[user_id]

    def cleanup_old_tasks(self, hours: int = 72):
        cutoff = datetime.now() - timedelta(hours=hours)
        removed = 0
        for state in self._cache.values():
            original = len(state.agent_tasks)
            state.agent_tasks = [
                t for t in state.agent_tasks 
                if datetime.fromisoformat(t.created_at.replace('Z', '+00:00').replace('+00:00', '')) > cutoff
            ]
            removed += original - len(state.agent_tasks)
        if removed > 0:
            logging.info(f"🗑️ Cleaned {removed} old agent tasks")

    async def periodic_save(self):
        """Background task for periodic saves."""
        while True:
            await asyncio.sleep(Config.STATE_SAVE_INTERVAL)
            if self._dirty:
                await self._save()

state_store = StateStore(Config.WORK_DIR / "states_v9.json")

def get_user_state(user_id: int) -> ConversationState:
    return state_store.get(user_id)

# ============================================================================
# ⏱️ RATE LIMITER
# ============================================================================

class RateLimiter:
    """Token bucket style rate limiter."""

    def __init__(self, rate: int, window: float = 60.0):
        self.rate = rate
        self.window = window
        self.buckets: Dict[Any, List[float]] = {}
        self._lock = asyncio.Lock()

    async def allow(self, key: Any) -> Tuple[bool, float]:
        async with self._lock:
            now = time.time()
            if key not in self.buckets:
                self.buckets[key] = []

            # Clean old entries
            self.buckets[key] = [t for t in self.buckets[key] if now - t < self.window]

            if len(self.buckets[key]) >= self.rate:
                oldest = min(self.buckets[key])
                wait = self.window - (now - oldest)
                return False, max(0.0, wait)

            self.buckets[key].append(now)
            return True, 0.0

    async def get_status(self, key: Any) -> Dict:
        async with self._lock:
            now = time.time()
            if key not in self.buckets:
                return {"used": 0, "limit": self.rate, "remaining": self.rate}
            valid = [t for t in self.buckets[key] if now - t < self.window]
            return {
                "used": len(valid),
                "limit": self.rate,
                "remaining": max(0, self.rate - len(valid))
            }

user_limiter = RateLimiter(Config.USER_REQUESTS_PER_MIN)
global_limiter = RateLimiter(Config.GLOBAL_REQUESTS_PER_MIN)

async def rate_limit_check(update: Update) -> Tuple[bool, Optional[str]]:
    user_id = update.effective_user.id if update.effective_user else "unknown"

    allowed, wait = await global_limiter.allow("global")
    if not allowed:
        return False, f"🌍 *Server đang bận.*\n⏳ Vui lòng thử lại sau `{wait:.0f}` giây."

    allowed, wait = await user_limiter.allow(user_id)
    if not allowed:
        return False, f"⏱ *Bạn gửi quá nhanh!*\n⏳ Đợi `{wait:.0f}` giây để tiếp tục."

    return True, None

# ============================================================================
# 📁 ADVANCED FILE PARSER & CODE EXTRACTOR
# ============================================================================

class FileExtractor:
    """Multi-strategy code file extractor with conflict resolution."""

    # Strategy: (regex_pattern, filename_group, content_group, priority)
    STRATEGIES = [
        # Explicit file markers (highest priority)
        (
            re.compile(r'<<<FILE:\s*([^>\n]+?)\s*>>>(.*?)<<<ENDFILE>>>', re.DOTALL | re.IGNORECASE),
            1, 2, 10
        ),
        # Markdown code block with filename in comment
        (
            re.compile(r'```(?:\w+)?\s*\n?\s*#\s*filename:\s*([^\n]+)\s*\n(.*?)```', re.DOTALL | re.IGNORECASE),
            1, 2, 9
        ),
        # Markdown with filename on same line as opening backticks
        (
            re.compile(r'```(?:\w+)?\s+([^\n`]+?\\.\w+)\s*\n(.*?)```', re.DOTALL | re.IGNORECASE),
            1, 2, 8
        ),
        # Header-style file declarations
        (
            re.compile(r'^#\s*File:\s*([^\n]+)\s*\n(.*?)(?=\n^#\s*File:|\Z)', re.DOTALL | re.MULTILINE | re.IGNORECASE),
            1, 2, 7
        ),
        # Python __file__ or module declarations
        (
            re.compile(r'#\s*\\-\\*\\-.*?file:\s*([^\n]+).*?\n(.*?)\n#\s*end\s+file', re.DOTALL | re.IGNORECASE),
            1, 2, 6
        ),
    ]

    DANGEROUS_PATTERNS = ['../', '..\\', '/etc/', '/proc/', 'null', 'undefined', '<', '>', '|', '\\0']

    @classmethod
    def extract(cls, text: str) -> Dict[str, str]:
        """Extract files from AI response with priority handling."""
        all_matches = []

        for pattern, fname_group, content_group, priority in cls.STRATEGIES:
            for match in pattern.finditer(text):
                try:
                    fname = match.group(fname_group).strip().strip('`').strip()
                    content = match.group(content_group).strip()
                    if cls._is_valid_filename(fname) and content:
                        all_matches.append((priority, fname, content, match.start()))
                except:
                    continue

        if not all_matches:
            # Fallback: detect if entire text is code
            if cls._looks_like_code(text):
                ext = cls._detect_language(text)
                return {f"main.{ext}": text.strip()}
            return {}

        # Sort by priority (high first) then position
        all_matches.sort(key=lambda x: (-x[0], x[3]))

        # Resolve conflicts: keep highest priority for each filename
        files = {}
        for priority, fname, content, pos in all_matches:
            safe_name = cls._sanitize_filename(fname)
            if safe_name not in files:
                files[safe_name] = content

        return files

    @classmethod
    def _is_valid_filename(cls, filename: str) -> bool:
        if not filename or len(filename) > 255:
            return False
        if any(d in filename.lower() for d in cls.DANGEROUS_PATTERNS):
            return False
        if filename.count('.') > 3 or filename.startswith('.'):
            return False
        return True

    @classmethod
    def _sanitize_filename(cls, filename: str) -> str:
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
        name = name.strip('. ')
        if len(name) > 200:
            base, ext = os.path.splitext(name)
            name = base[:195] + ext
        if not name or name.startswith('_'):
            name = f"file_{hashlib.md5(filename.encode()).hexdigest()[:8]}.txt"
        return name

    @classmethod
    def _looks_like_code(cls, text: str) -> bool:
        indicators = [
            r'\b(import|from|class|def|function|const|let|var|#include|package)\b',
            r'\{\s*\w+\s*:\s*',
            r'->\s*\w+',
            r'^(const|let|var|def|class|function|import)\s+',
            r'\b(main|if __name__|public static|func main)\b'
        ]
        return any(re.search(p, text, re.MULTILINE | re.IGNORECASE) for p in indicators)

    @classmethod
    def _detect_language(cls, text: str) -> str:
        if re.search(r'\bimport\s+\w+|from\s+\w+\s+import', text): return 'py'
        if re.search(r'\bfunction\s+\w+|const\s+\w+\s*=|require\\(', text): return 'js'
        if re.search(r'\binterface\s+\w+|:\s*(string|number|boolean)\b', text): return 'ts'
        if re.search(r'#include|int main\\(|cout <<', text): return 'cpp'
        if re.search(r'package main|func main|import "', text): return 'go'
        if re.search(r'<!DOCTYPE|<html|<div', text, re.IGNORECASE): return 'html'
        return 'txt'

    @classmethod
    def auto_generate_dependencies(cls, files: Dict[str, str]) -> Dict[str, str]:
        """Auto-generate requirements.txt, package.json, etc. if missing."""
        extras = {}

        # Python detection
        if any(f.endswith('.py') for f in files):
            if 'requirements.txt' not in files and 'pyproject.toml' not in files:
                imports = set()
                for content in files.values():
                    for match in re.finditer(r'^(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_]*)', content, re.MULTILINE):
                        imports.add(match.group(1))

                stdlib = {'os', 'sys', 'json', 're', 'time', 'datetime', 'pathlib', 'typing', 
                         'collections', 'asyncio', 'io', 'base64', 'hashlib', 'logging', 'traceback',
                         'dataclasses', 'enum', 'math', 'random', 'string', 'inspect'}
                deps = sorted(imports - stdlib)
                if deps:
                    extras['requirements.txt'] = "\n".join(f"{d}" for d in deps) + "\n"

        # Node.js detection
        if any(f.endswith(('.js', '.ts', '.tsx')) for f in files):
            if 'package.json' not in files:
                imports = set()
                for content in files.values():
                    for match in re.finditer(r"require\\(['\"]([^'\"]+)['\"]\\)|import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", content):
                        dep = match.group(1) or match.group(2)
                        if dep and not dep.startswith('.') and not dep.startswith('@types/'):
                            imports.add(dep.split('/')[0])

                if imports:
                    pkg = {
                        "name": "auto-generated-project",
                        "version": "1.0.0",
                        "dependencies": {dep: "latest" for dep in sorted(imports)}
                    }
                    extras['package.json'] = json.dumps(pkg, indent=2) + "\n"

        return extras

# ============================================================================
# 🔍 SMART SYNTAX VALIDATOR
# ============================================================================

class SyntaxValidator:
    """Multi-language syntax validation with fix suggestions."""

    @classmethod
    def validate(cls, code: str, filename: str) -> List[Dict]:
        ext = Path(filename).suffix.lower()
        issues = []

        if ext == '.py':
            issues.extend(cls._validate_python(code, filename))
        elif ext in ['.js', '.ts', '.tsx']:
            issues.extend(cls._validate_js_ts(code, filename))
        elif ext == '.json':
            issues.extend(cls._validate_json(code, filename))
        elif ext in ['.yml', '.yaml']:
            issues.extend(cls._validate_yaml(code, filename))
        elif ext == '.html':
            issues.extend(cls._validate_html(code, filename))

        # General checks
        issues.extend(cls._validate_general(code, filename))
        return issues

    @staticmethod
    def _validate_python(code: str, filename: str) -> List[Dict]:
        issues = []
        try:
            compile(code, filename, 'exec')
        except SyntaxError as e:
            return [{
                "level": "error",
                "line": e.lineno,
                "message": f"Python syntax error: {e.msg}",
                "suggestion": "Check indentation, colons, quotes, or parentheses near this line."
            }]

        # Warnings
        if re.search(r'\bexcept\s*:', code) and not re.search(r'\bexcept\s+\w+', code):
            issues.append({
                "level": "warning",
                "line": None,
                "message": "Bare `except:` clause detected",
                "suggestion": "Use `except Exception:` or specific exceptions."
            })

        if 'print(' in code and 'logging' not in code and len(code) > 500:
            issues.append({
                "level": "info",
                "line": None,
                "message": "Using print() statements",
                "suggestion": "Consider using the `logging` module for production code."
            })

        if re.search(r'\binput\s*\\(', code):
            issues.append({
                "level": "warning",
                "line": None,
                "message": "Interactive input() detected",
                "suggestion": "For bots/APIs, use environment variables or config files instead of input()."
            })

        return issues

    @staticmethod
    def _validate_js_ts(code: str, filename: str) -> List[Dict]:
        issues = []

        # Brace matching (simple)
        open_braces = code.count('{') - code.count('}')
        if open_braces != 0:
            issues.append({
                "level": "error" if abs(open_braces) > 2 else "warning",
                "line": None,
                "message": f"Mismatched braces: {open_braces} unclosed",
                "suggestion": "Check all opening '{' have matching '}'."
            })

        # Parentheses matching
        open_parens = code.count('(') - code.count(')')
        if open_parens != 0:
            issues.append({
                "level": "error" if abs(open_parens) > 2 else "warning",
                "line": None,
                "message": f"Mismatched parentheses: {open_parens} unclosed",
                "suggestion": "Check all function calls and expressions."
            })

        if 'console.log' in code and 'debug' not in filename.lower():
            issues.append({
                "level": "info",
                "line": None,
                "message": "console.log found",
                "suggestion": "Remove console.log in production or replace with a logger."
            })

        return issues

    @staticmethod
    def _validate_json(code: str, filename: str) -> List[Dict]:
        try:
            json.loads(code)
            return []
        except json.JSONDecodeError as e:
            return [{
                "level": "error",
                "line": e.lineno if hasattr(e, 'lineno') else None,
                "message": f"JSON parse error: {e.msg}",
                "suggestion": "Check for trailing commas, missing quotes, or brackets."
            }]

    @staticmethod
    def _validate_yaml(code: str, filename: str) -> List[Dict]:
        try:
            import yaml
            yaml.safe_load(code)
            return []
        except Exception as e:
            return [{
                "level": "error",
                "line": getattr(e, 'problem_mark', None).line if hasattr(e, 'problem_mark') and e.problem_mark else None,
                "message": f"YAML error: {str(e)[:100]}",
                "suggestion": "Check indentation (must be spaces, not tabs) and colon spacing."
            }]

    @staticmethod
    def _validate_html(code: str, filename: str) -> List[Dict]:
        issues = []
        open_tags = len(re.findall(r'<\w+[^>]*>', code))
        close_tags = len(re.findall(r'</\w+>', code))
        self_closing = len(re.findall(r'<\w+[^>]*/>', code))

        if open_tags > close_tags + self_closing + 2:
            issues.append({
                "level": "warning",
                "line": None,
                "message": "Potentially unclosed HTML tags",
                "suggestion": "Verify all opened tags are properly closed."
            })
        return issues

    @staticmethod
    def _validate_general(code: str, filename: str) -> List[Dict]:
        issues = []
        if len(code) > 10000 and '\n' not in code[:1000]:
            issues.append({
                "level": "warning",
                "line": None,
                "message": "Code appears to be minified or lacks proper formatting",
                "suggestion": "Add proper line breaks and indentation for readability."
            })
        return issues

    @classmethod
    def format_issues(cls, issues: List[Dict]) -> str:
        if not issues:
            return "✅ No issues found"

        lines = []
        for issue in issues:
            emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(issue['level'], "•")
            line_info = f" (line {issue['line']})" if issue.get('line') else ""
            lines.append(f"{emoji} **{issue['level'].upper()}**{line_info}: {issue['message']}\n   💡 {issue['suggestion']}")
        return "\n\n".join(lines)

# ============================================================================
# 📦 LOCAL PACKAGE BUILDER
# ============================================================================

class PackageBuilder:
    """Builds deployable ZIP packages with auto-documentation."""

    @classmethod
    async def create_package(cls, task_id: str, files: Dict[str, str], 
                            metadata: Dict, task: AgentTask) -> Tuple[Path, int]:
        task_dir = Config.WORK_DIR / "agents" / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # Write all files
        total_size = 0
        for filename, content in files.items():
            file_path = task_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            total_size += file_path.stat().st_size

        # Write metadata
        meta = {
            **metadata,
            "created_at": datetime.now().isoformat(),
            "denia_version": "9.0",
            "files_count": len(files),
            "task_id": task_id,
            "model": task.model_used,
            "dependencies": task.dependencies
        }
        (task_dir / ".denia_meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8'
        )

        # Generate README if missing
        if "README.md" not in files and "readme.md" not in files:
            readme = cls._generate_readme(metadata, files, task)
            (task_dir / "README.md").write_text(readme, encoding='utf-8')
            total_size += len(readme.encode('utf-8'))

        # Generate .env.example if env vars detected
        env_vars = set()
        for content in files.values():
            for match in re.finditer(r'os\\.getenv\\(["\']([A-Z_][A-Z0-9_]*)', content):
                env_vars.add(match.group(1))
            for match in re.finditer(r'process\\.env\\.([A-Z_][A-Z0-9_]*)', content):
                env_vars.add(match.group(1))

        if env_vars and ".env.example" not in files:
            env_example = "# Environment Variables\n" + "\n".join(f"{v}=your_{v.lower().replace('_', '_')}_here" for v in sorted(env_vars))
            (task_dir / ".env.example").write_text(env_example + "\n", encoding='utf-8')

        # Create ZIP
        zip_path = Config.WORK_DIR / "zips" / f"{task_id}.zip"
        zip_path.parent.mkdir(exist_ok=True)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for fp in task_dir.rglob('*'):
                if fp.is_file():
                    zf.write(fp, fp.relative_to(task_dir))

        zip_size = zip_path.stat().st_size
        logging.info(f"📦 Package created: {zip_path.name} ({zip_size/1024:.1f}KB, {len(files)} files)")
        return zip_path, zip_size

    @staticmethod
    def _generate_readme(meta: Dict, files: Dict[str, str], task: AgentTask) -> str:
        desc = meta.get('description', 'Auto-generated project')[:250]

        # Build file tree
        tree_lines = []
        for f in sorted(files.keys()):
            size = len(files[f])
            tree_lines.append(f"- `{f}` ({size} chars)")

        # Detect setup command
        setup = ""
        if "requirements.txt" in files:
            setup = """### Python Setup
```bash
pip install -r requirements.txt
python main.py
```"""
        elif "package.json" in files:
            setup = """### Node.js Setup
```bash
npm install
npm start
```"""
        elif any(f.endswith('.py') for f in files):
            setup = """### Run
```bash
python main.py
```"""
        elif any(f.endswith('.js') for f in files):
            setup = """### Run
```bash
node main.js
```"""

        deps_section = ""
        if task.dependencies:
            deps_section = f"""### Dependencies
{chr(10).join(f'- `{d}`' for d in task.dependencies[:10])}
"""

        return f"""# 🤖 {meta.get('task_id', 'Project')}

> {desc}

## 📁 Files ({len(files)})

{chr(10).join(tree_lines)}

{deps_section}
## 🚀 Quick Start

{setup}

## 📊 Generation Info

- **Model**: `{task.model_used or 'unknown'}`
- **Task ID**: `{task.task_id}`
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Denia Bot**: v9.0 Pro

---
*Generated by Denia Bot — AI Agent Platform*
"""

# ============================================================================
# 🌐 GITHUB MANAGER
# ============================================================================

class GitHubManager:
    """Professional GitHub integration with conflict handling."""

    BASE = "https://api.github.com"

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Denia-Bot/9.0"
        }
        self._session: Optional[aiohttp.ClientSession] = None
        self._username: Optional[str] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=60, connect=15)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"User-Agent": self.headers["User-Agent"]}
            )
        return self._session

    async def _request(self, method: str, endpoint: str, **kwargs) -> Tuple[int, Any]:
        session = await self._get_session()
        url = f"{self.BASE}{endpoint}"
        headers = {**self.headers, **kwargs.pop('headers', {})}

        try:
            async with session.request(method, url, headers=headers, **kwargs) as resp:
                try:
                    data = await resp.json()
                except:
                    data = await resp.text()
                return resp.status, data
        except Exception as e:
            logging.error(f"GitHub API error: {e}")
            return 0, str(e)

    async def verify_auth(self) -> Tuple[bool, str]:
        status, data = await self._request("GET", "/user")
        if status == 200 and isinstance(data, dict):
            self._username = data.get("login", "")
            return True, self._username
        return False, str(data)[:200]

    async def get_username(self) -> Optional[str]:
        if not self._username:
            await self.verify_auth()
        return self._username

    async def create_repo(self, name: str, description: str = "", 
                         private: bool = False, auto_init: bool = True) -> Tuple[bool, str]:
        payload = {
            "name": name,
            "description": description[:300],
            "private": private,
            "auto_init": auto_init,
            "license_template": "mit"
        }
        status, data = await self._request("POST", "/user/repos", json=payload)

        if status == 201 and isinstance(data, dict):
            return True, data.get("html_url", "")

        # Handle existing repo
        if status == 422 and isinstance(data, dict):
            errors = data.get("errors", [])
            if any(e.get("message", "").lower().find("exist") >= 0 for e in errors):
                username = await self.get_username()
                if username:
                    return True, f"https://github.com/{username}/{name}"

        return False, str(data)[:300]

    async def push_files(self, owner: str, repo: str, files: Dict[str, str], 
                        message: str, branch: str = "main") -> Tuple[bool, str]:
        """Push multiple files with conflict resolution."""
        success_count = 0
        failed_files = []

        for path, content in files.items():
            encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')

            # Check if file exists
            status, data = await self._request(
                "GET", 
                f"/repos/{owner}/{repo}/contents/{path}?ref={branch}"
            )

            payload = {
                "message": f"{message[:150]} — {path}",
                "content": encoded,
                "branch": branch
            }

            if status == 200 and isinstance(data, dict) and "sha" in data:
                payload["sha"] = data["sha"]

            put_status, put_data = await self._request(
                "PUT",
                f"/repos/{owner}/{repo}/contents/{path}",
                json=payload
            )

            if put_status in (200, 201):
                success_count += 1
            else:
                failed_files.append(f"{path}: {put_status}")
                logging.warning(f"Failed to push {path}: {put_status}")

            await asyncio.sleep(0.4)  # Rate limit safety

        if success_count == len(files):
            return True, f"https://github.com/{owner}/{repo}"
        elif success_count > 0:
            return True, f"https://github.com/{owner}/{repo} ({success_count}/{len(files)} files)"
        else:
            return False, f"Failed to push all files: {', '.join(failed_files[:3])}"

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

# Global GitHub instance
github = GitHubManager(Config.GITHUB_TOKEN)

# ============================================================================
# 🎯 SYSTEM PROMPTS
# ============================================================================

SYSTEM_PROMPT_CHAT = """You are Denia Bot v9.0 — an elite AI assistant powered by multiple providers (OpenCode + NVIDIA NIM).

CORE DIRECTIVES:
1. Provide accurate, helpful responses with clear structure.
2. For coding questions: give complete, runnable examples with comments.
3. Adapt to user's language preference automatically.
4. Use Markdown formatting for readability.
5. Be concise unless asked for detailed explanations.

When writing code:
- Include error handling
- Add docstrings/comments
- Follow language conventions
- Never use placeholders like "// TODO" or "..." — always complete the implementation
"""

SYSTEM_PROMPT_AGENT = """You are Denia Agent v9.0 — an AUTONOMOUS SOFTWARE ENGINEER.

MISSION: Complete software tasks end-to-end with ZERO follow-up questions.

WORKFLOW:
1. ANALYZE requirements thoroughly
2. PLAN architecture and file structure
3. IMPLEMENT complete, production-ready code
4. INCLUDE all necessary files (main, utils, config, tests if needed)

STRICT RULES:
- Write COMPLETE code — no placeholders, no pseudocode, no "// your code here"
- Every function must be fully implemented
- Include proper error handling, logging, type hints
- Add requirements.txt or package.json if dependencies exist
- Follow security best practices (no hardcoded secrets)

OUTPUT FORMAT — You MUST use this exact format for each file:

<<<FILE:filename.py>>>
[complete file content here]
<<<ENDFILE>>>

<<<FILE:another_file.js>>>
[complete file content here]
<<<ENDFILE>>>

After all files, add:
<<<META>>>
dependencies: package1, package2, package3
main_file: filename.py
language: python
<<<ENDMETA>>>
"""

SYSTEM_PROMPT_AGENT_FIX = """You are Denia Fixer v9.0 — a code repair specialist.

TASK: Fix the provided code errors while preserving all functionality.

RULES:
1. Output ONLY the corrected files using the <<<FILE:>>> format
2. Do not add explanations outside the file markers
3. Ensure syntax is 100% valid
4. Maintain original logic intent
5. Add defensive checks where errors occurred
"""

# ============================================================================
# 🎨 UI HELPERS
# ============================================================================

CATEGORY_EMOJI = {
    "GLM": "🟡", "MiniMax": "🔴", "Mistral": "⚪",
    "GPT": "🟢", "Claude": "🟣", "Gemini": "🔵",
    "Qwen": "🟠", "DeepSeek": "⚫", "Khác": "🟦"
}

PROVIDER_EMOJI = {"opencode": "🟢 OC", "nvidia": "🔵 NV"}

def build_model_keyboard(mode: str, current: str, page: int = 0) -> InlineKeyboardMarkup:
    """Build paginated model selector."""
    models = MODE_CONFIG.get(mode, {}).get("models", [])
    per_page = 6
    total_pages = max(1, (len(models) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    start_idx = page * per_page
    page_models = models[start_idx:start_idx + per_page]

    keyboard = []
    for cat, model_id, display, provider in page_models:
        prefix = "✅ " if model_id == current else ""
        prov_tag = PROVIDER_EMOJI.get(provider, "⚪")
        btn = InlineKeyboardButton(
            f"{prefix}{prov_tag} {display[:20]}",
            callback_data=f"model_{mode}_{model_id}"
        )
        keyboard.append([btn])

    # Navigation
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"models_{mode}_{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"models_{mode}_{page+1}"))
    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([InlineKeyboardButton("🔄 Auto-Select Best", callback_data=f"auto_{mode}")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")])

    return InlineKeyboardMarkup(keyboard)

def build_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Agent Mode", callback_data="mode_agent"),
         InlineKeyboardButton("💬 Chat Mode", callback_data="mode_chat")],
        [InlineKeyboardButton("📊 My Stats", callback_data="menu_stats"),
         InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")],
        [InlineKeyboardButton("🗑️ Reset Chat", callback_data="menu_reset"),
         InlineKeyboardButton("❓ Help", callback_data="menu_help")],
    ])

def build_deploy_keyboard(current: str) -> InlineKeyboardMarkup:
    options = [
        ("📦 Local ZIP", "local", current == "local"),
        ("🌐 GitHub Push", "github", current == "github"),
        ("🚀 Both", "both", current == "both"),
    ]
    keyboard = []
    for label, value, active in options:
        prefix = "✅ " if active else ""
        keyboard.append([InlineKeyboardButton(f"{prefix}{label}", callback_data=f"deploy_{value}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_settings")])
    return InlineKeyboardMarkup(keyboard)

def build_style_keyboard(current: str) -> InlineKeyboardMarkup:
    styles = [
        ("⚡ Concise", "concise"),
        ("⚖️ Balanced", "balanced"),
        ("📚 Verbose", "verbose"),
    ]
    keyboard = []
    for label, value in styles:
        prefix = "✅ " if current == value else ""
        keyboard.append([InlineKeyboardButton(f"{prefix}{label}", callback_data=f"style_{value}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_settings")])
    return InlineKeyboardMarkup(keyboard)

def escape_md(text: str) -> str:
    """Escape MarkdownV2 special characters."""
    chars = r'_*[]()~`>#+-=|{}.!'
    for ch in chars:
        text = text.replace(ch, f'\\{ch}')
    return text

def truncate_md(text: str, limit: int = 3500) -> str:
    """Smart truncate preserving markdown structure."""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n... _(content truncated)_"

async def send_long_message(update: Update, text: str, parse_mode: str = TPM.MARKDOWN,
                           reply_markup=None, caption: str = None):
    """Send long text as message or document."""
    if len(text) <= MessageLimit.MAX_TEXT_LENGTH - 100:
        try:
            return await update.message.reply_text(text, parse_mode=parse_mode, 
                                                   reply_markup=reply_markup)
        except BadRequest as e:
            if "too long" not in str(e).lower() and "parse" not in str(e).lower():
                raise
            # Fallback to plain text if markdown parse fails
            try:
                return await update.message.reply_text(text, parse_mode=None,
                                                       reply_markup=reply_markup)
            except:
                pass

    # Send as file
    bio = io.BytesIO(text.encode('utf-8'))
    bio.name = f"denia_response_{int(time.time())}.txt"
    cap = caption or "📄 Response too long for chat — sent as file"
    return await update.message.reply_document(document=bio, caption=cap)

# ============================================================================
# 🎯 COMMAND HANDLERS
# ============================================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    allowed, msg = await rate_limit_check(update)
    if not allowed:
        await update.message.reply_text(msg, parse_mode=TPM.MARKDOWN)
        return

    state = get_user_state(user_id)

    welcome = f"""╔══════════════════════════════╗
║     🤖 *Denia Bot v9\\.0*      ║
║    *Ultimate AI Agent*        ║
╚══════════════════════════════╝

👋 Xin chào *{escape_md(update.effective_user.first_name or 'bạn')}*\\!

🧠 *AI đa nền tảng* — Tự chọn model, tự nén context, tự học từ lỗi

📦 *Chế độ hiện tại:*
• 💬 *Chat* — Hỏi đáp thông minh
• 🤖 *Agent* — Code tự động \\+ Deploy

🚀 *Model:* `{escape_md(state.current_model)}`
🎯 *Auto\\-select:* {'✅ Bật' if state.auto_model else '❌ Tắt'}
📦 *Deploy:* `{state.agent_deploy_mode.upper()}`

📚 *Lệnh chính:*
• `/agent` \\- Chạy agent tự động
• `/models` \\- Chọn model AI
• `/style` \\- Đổi phong cách trả lời
• `/deploy` \\- Cài đặt deploy
• `/stats` \\- Xem thống kê
• `/reset` \\- Xóa lịch sử
• `/help` \\- Hướng dẫn chi tiết

💡 *Mẹo:* Gõ `/agent github Tạo API FastAPI \\+ SQLite` để auto\\-deploy\\!"""

    await update.message.reply_text(welcome, parse_mode=TPM.MARKDOWN_V2,
                                    reply_markup=build_main_menu())
    await state_store.save_user(user_id)

async def cmd_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    keyboard = build_model_keyboard(state.mode, state.current_model)

    header = f"""📂 *Model Catalog*
{'━' * 25}
✅ = Đang dùng | 🟢 OpenCode | 🔵 NVIDIA

*Chế độ:* {MODE_CONFIG[state.mode]['name']}
*Auto\\-select:* {'Bật' if state.auto_model else 'Tắt'}

👇 Chọn model hoặc dùng *Auto\\-Select* để bot tự chọn tối ưu"""

    await update.message.reply_text(header, parse_mode=TPM.MARKDOWN,
                                    reply_markup=keyboard)

async def cmd_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)

    if not context.args:
        deploy_modes = {
            "local": "📦 Gửi ZIP qua Telegram",
            "github": "🌐 Push lên GitHub repo",
            "both": "🚀 Cả hai (ZIP + GitHub)"
        }
        current_deploy = deploy_modes.get(state.agent_deploy_mode, state.agent_deploy_mode)

        help_text = f"""🤖 *Agent Mode — Code Tự Động*
{'━' * 25}

*Cách dùng:*
`/agent [github|local|both] <mô tả task>`

*Ví dụ:*
• `/agent Tạo REST API FastAPI \\+ SQLite`
• `/agent github Viết bot Telegram có webhook`
• `/agent both Xây dựng blog React \\+ Node.js`

*Deploy hiện tại:* {current_deploy}
*Model:* `{state.current_model}`

⚡ Agent sẽ:
1\\. Phân tích yêu cầu
2\\. Lập kế hoạch kiến trúc
3\\. Code đầy đủ file
4\\. Kiểm tra syntax
5\\. Tự sửa lỗi \\(nếu có\\)
6\\. Deploy theo yêu cầu

💡 *Mẹo:* Mô tả càng chi tiết, code càng chính xác\\!"""

        await update.message.reply_text(help_text, parse_mode=TPM.MARKDOWN_V2)
        return

    # Parse deploy mode and task
    deploy_mode = state.agent_deploy_mode
    args = list(context.args)

    if args[0].lower() in ['github', 'local', 'both']:
        deploy_mode = args[0].lower()
        args = args[1:]

    task_desc = " ".join(args).strip()
    if not task_desc:
        await update.message.reply_text("❌ *Thiếu mô tả task\\!*\nVí dụ: `/agent Tạo API Python`",
                                        parse_mode=TPM.MARKDOWN)
        return

    # Generate task ID
    task_id = f"denia_{int(time.time())}_{hashlib.md5(f'{user_id}{task_desc}'.encode()).hexdigest()[:8]}"
    task = AgentTask(
        task_id=task_id,
        user_id=user_id,
        description=task_desc,
        deploy_mode=deploy_mode,
        status="pending"
    )
    state.agent_tasks.append(task)

    # Initial status message
    status_text = f"""🤖 *Agent Task Khởi Động*
{'━' * 25}
🆔 `{task_id}`
📝 {escape_md(task_desc[:100])}{'...' if len(task_desc) > 100 else ''}
📦 Deploy: `{deploy_mode.upper()}`

⏳ *Bước 1/6:* Phân tích yêu cầu\\.\\.\\."""

    status_msg = await update.message.reply_text(status_text, parse_mode=TPM.MARKDOWN_V2)

    # Launch background task
    asyncio.create_task(
        run_agent_workflow(update, context, state, task, status_msg, deploy_mode)
    )

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    s = state.usage

    # Calculate derived stats
    success_rate = 0.0
    if s.agent_tasks_completed + s.agent_tasks_failed > 0:
        success_rate = s.agent_tasks_completed / (s.agent_tasks_completed + s.agent_tasks_failed) * 100

    models_str = "\n".join([
        f"• `{m}`: {c}x" 
        for m, c in sorted(s.models_used.items(), key=lambda x: -x[1])[:5]
    ]) or "Chưa có dữ liệu"

    stats_text = f"""📊 *Thống Kê Sử Dụng*
{'━' * 25}

🔢 *Tổng request:* `{s.total_requests}`
📝 *Input tokens:* `{s.total_input_tokens:,}`
💬 *Output tokens:* `{s.total_output_tokens:,}`
📦 *Tổng tokens:* `{s.total_tokens:,}`
⏱ *Latency trung bình:* `{s.avg_latency:.2f}s`

🤖 *Model đã dùng:*
{models_str}

🎯 *Agent tasks:*
• Hoàn thành: `{s.agent_tasks_completed}`
• Thất bại: `{s.agent_tasks_failed}`
• Tỷ lệ thành công: `{success_rate:.1f}%`

📅 *Bắt đầu:* `{s.first_seen[:10]}`
🕐 *Hoạt động gần nhất:* `{s.last_active[:16]}`

💡 Dùng `/reset` để xóa lịch sử"""

    await send_long_message(update, stats_text)
    await state_store.save_user(user_id)

async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)

    state.history = []
    state.agent_tasks = state.agent_tasks[-5:]  # Keep last 5
    state.error_patterns = {}
    state.successful_patterns = {}

    await update.message.reply_text(
        "🗑️ *Đã reset\\!*\n\n"
        "✅ Lịch sử chat đã xóa\n"
        "✅ Pattern cache đã xóa\n"
        "📦 Giữ lại 5 task gần nhất",
        parse_mode=TPM.MARKDOWN
    )
    await state_store.save_user(user_id)

async def cmd_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)

    if not context.args:
        await update.message.reply_text(
            "⚙️ *Chọn phong cách trả lời:*",
            parse_mode=TPM.MARKDOWN,
            reply_markup=build_style_keyboard(state.preferred_style)
        )
        return

    style = context.args[0].lower()
    if style in ['concise', 'balanced', 'verbose']:
        state.preferred_style = style
        await update.message.reply_text(
            f"✅ *Đã đổi phong cách:* `{style.upper()}`",
            parse_mode=TPM.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "❌ *Phong cách không hợp lệ*\nChọn: `concise`, `balanced`, `verbose`",
            parse_mode=TPM.MARKDOWN
        )
    await state_store.save_user(user_id)

async def cmd_deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)

    if not context.args:
        await update.message.reply_text(
            "📦 *Cài đặt Deploy Mode:*\n\n"
            "Chọn nơi Agent sẽ gửi code sau khi hoàn thành:",
            parse_mode=TPM.MARKDOWN,
            reply_markup=build_deploy_keyboard(state.agent_deploy_mode)
        )
        return

    mode = context.args[0].lower()
    if mode in ['local', 'github', 'both']:
        state.agent_deploy_mode = mode
        await update.message.reply_text(
            f"✅ *Deploy mode:* `{mode.upper()}`",
            parse_mode=TPM.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "❌ *Chọn:* `local`, `github`, hoặc `both`",
            parse_mode=TPM.MARKDOWN
        )
    await state_store.save_user(user_id)

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """📖 *Hướng Dẫn Denia Bot v9.0*
━━━━━━━━━━━━━━━━━━━━━━

🎯 *Lệnh chính:*
• `/start` — Menu chính
• `/agent [mode] <task>` — Chạy agent
• `/models` — Chọn model AI
• `/style <concise|balanced|verbose>` — Phong cách
• `/deploy <local|github|both>` — Cài deploy
• `/stats` — Thống kê
• `/reset` — Xóa lịch sử
• `/help` — Hiển thị hướng dẫn

🤖 *Agent Mode:*
• `/agent Tạo API FastAPI` — ZIP local
• `/agent github Viết bot Telegram` — Push GitHub
• `/agent both Xây dựng fullstack app` — Cả hai

⚙️ *Tùy chỉnh:*
• Bot tự chọn model phù hợp
• Context tự nén khi dài
• Học từ lỗi để cải thiện
• Streaming: thấy chữ hiện dần

🔧 *Troubleshooting:*
• Lỗi timeout? → Thử `/models` chọn model khác
• Code lỗi? → Agent tự động retry + fix
• GitHub lỗi? → Kiểm tra token hoặc dùng local

━━━━━━━━
🤖 Denia Bot v9.0 — Ultimate Pro Edition"""
    await send_long_message(update, help_text)

# ============================================================================
# 🎛️ CALLBACK HANDLER
# ============================================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    state = get_user_state(user_id)
    data = query.data

    try:
        if data.startswith("model_"):
            parts = data.split("_", 2)
            if len(parts) >= 3:
                mode, model_id = parts[1], parts[2]
                valid_models = [m[1] for m in MODE_CONFIG.get(mode, {}).get("models", [])]
                if model_id in valid_models:
                    state.mode = mode
                    state.current_model = model_id
                    state.current_provider = MODEL_REGISTRY[model_id].provider if model_id in MODEL_REGISTRY else "nvidia"
                    state.auto_model = False
                    display = _get_model_display(mode, model_id)
                    await query.edit_message_text(
                        f"✅ *Đã chọn model\\!*\n\n🤖 {display}\n🆔 `{model_id}`\n\n💡 Auto\\-select đã tắt.",
                        parse_mode=TPM.MARKDOWN
                    )

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
            await query.edit_message_text(
                "🎯 *Auto\\-Select đã BẬT*\n\n"
                "Bot sẽ tự chọn model tối ưu cho từng task.",
                parse_mode=TPM.MARKDOWN_V2
            )

        elif data.startswith("mode_"):
            mode = data.split("_")[1]
            if mode in MODE_CONFIG:
                state.mode = mode
                state.current_model = MODE_CONFIG[mode]["default"]
                state.current_provider = MODEL_REGISTRY[state.current_model].provider if state.current_model in MODEL_REGISTRY else "nvidia"
                await query.edit_message_text(
                    f"✅ *Chế độ:* {MODE_CONFIG[mode]['name']}\n"
                    f"🤖 *Model:* `{state.current_model}`",
                    parse_mode=TPM.MARKDOWN
                )

        elif data.startswith("deploy_"):
            mode = data.split("_")[1]
            if mode in ['local', 'github', 'both']:
                state.agent_deploy_mode = mode
                await query.edit_message_text(
                    f"✅ *Deploy mode:* `{mode.upper()}`\n\n"
                    f"Agent sẽ deploy code ở chế độ này.",
                    parse_mode=TPM.MARKDOWN,
                    reply_markup=build_deploy_keyboard(mode)
                )

        elif data.startswith("style_"):
            style = data.split("_")[1]
            if style in ['concise', 'balanced', 'verbose']:
                state.preferred_style = style
                await query.edit_message_text(
                    f"✅ *Phong cách:* `{style.upper()}`",
                    parse_mode=TPM.MARKDOWN,
                    reply_markup=build_style_keyboard(style)
                )

        elif data == "menu_main":
            await query.edit_message_text(
                "🏠 *Main Menu*\n\nChọn chức năng:",
                parse_mode=TPM.MARKDOWN,
                reply_markup=build_main_menu()
            )

        elif data == "menu_stats":
            await cmd_stats(update, context)

        elif data == "menu_settings":
            await query.edit_message_text(
                "⚙️ *Settings*\n\nChọn tùy chỉnh:",
                parse_mode=TPM.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎨 Phong cách", callback_data="menu_style")],
                    [InlineKeyboardButton("📦 Deploy mode", callback_data="menu_deploy")],
                    [InlineKeyboardButton("🧠 Model", callback_data="menu_models")],
                    [InlineKeyboardButton("🔙 Back", callback_data="menu_main")]
                ])
            )

        elif data == "menu_style":
            await query.edit_message_text(
                "🎨 *Phong cách trả lời*",
                parse_mode=TPM.MARKDOWN,
                reply_markup=build_style_keyboard(state.preferred_style)
            )

        elif data == "menu_deploy":
            await query.edit_message_text(
                "📦 *Deploy Settings*",
                parse_mode=TPM.MARKDOWN,
                reply_markup=build_deploy_keyboard(state.agent_deploy_mode)
            )

        elif data == "menu_models":
            keyboard = build_model_keyboard(state.mode, state.current_model)
            await query.edit_message_text(
                "🧠 *Model Selection*",
                parse_mode=TPM.MARKDOWN,
                reply_markup=keyboard
            )

        elif data == "menu_reset":
            await cmd_reset(update, context)

        elif data == "menu_help":
            await cmd_help(update, context)

        await state_store.save_user(user_id)

    except Exception as e:
        logging.error(f"Callback error: {e}")
        await query.edit_message_text(
            f"⚠️ Lỗi xử lý callback: `{str(e)[:100]}`",
            parse_mode=TPM.MARKDOWN
        )

# ============================================================================
# 🤖 PROFESSIONAL AGENT WORKFLOW
# ============================================================================

async def run_agent_workflow(update: Update, context: ContextTypes.DEFAULT_TYPE,
                             state: ConversationState, task: AgentTask,
                             status_msg: Message, deploy_mode: str):
    """
    Professional 6-step agent workflow:
    1. ANALYZE — Understand requirements
    2. PLAN — Architecture & file structure
    3. CODE — Generate complete implementation
    4. VALIDATE — Syntax check & completeness
    5. FIX — Auto-repair if needed
    6. DEPLOY — Package and deliver
    """
    start_time = time.time()

    try:
        # Step 1: ANALYZE
        task.status = "analyzing"
        await _update_agent_status(status_msg, task, 1, 6, "🔍 Phân tích yêu cầu...")

        model_id, display, provider = _select_agent_model(state, task.description)
        task.model_used = model_id
        task.provider_used = provider

        analyze_messages = [
            {"role": "system", "content": SYSTEM_PROMPT_AGENT},
            {"role": "user", "content": f"Analyze this task and provide a brief technical plan:\n\n{task.description}\n\nRespond with:\n1. Main goal\n2. Tech stack recommendation\n3. Key files needed\n4. Potential challenges"}
        ]

        analysis, metrics = await StreamingHandler.agent_generate(
            model_id, provider, analyze_messages, "Phân tích", status_msg
        )
        task.add_checkpoint("analyze", "success", {"analysis": analysis[:500]}, 
                          int(metrics.get('latency', 0) * 1000))
        task.metrics.update(metrics)

        # Detect language from description
        task.detected_language = _detect_project_language(task.description, analysis)

        # Step 2: PLAN
        task.status = "planning"
        await _update_agent_status(status_msg, task, 2, 6, "📐 Lập kế hoạch kiến trúc...")

        plan_messages = [
            {"role": "system", "content": SYSTEM_PROMPT_AGENT},
            {"role": "user", "content": f"Task: {task.description}\n\nAnalysis: {analysis}\n\nCreate a detailed implementation plan with file structure. List every file to create and its purpose."}
        ]

        plan, plan_metrics = await StreamingHandler.agent_generate(
            model_id, provider, plan_messages, "Lập kế hoạch", status_msg
        )
        task.add_checkpoint("plan", "success", {"plan": plan[:800]}, 
                          int(plan_metrics.get('latency', 0) * 1000))
        task.metrics['total_tokens'] = task.metrics.get('total_tokens', 0) + plan_metrics.get('output_tokens', 0)

        # Step 3: CODE
        task.status = "coding"
        await _update_agent_status(status_msg, task, 3, 6, "💻 Viết code...")

        code_messages = [
            {"role": "system", "content": SYSTEM_PROMPT_AGENT},
            {"role": "user", "content": f"Task: {task.description}\n\nPlan:\n{plan}\n\nNow write COMPLETE code for ALL files. Use exact <<<FILE:filename>>> format. Every file must be complete and runnable. Include error handling, logging, and comments."}
        ]

        code_text, code_metrics = await StreamingHandler.agent_generate(
            model_id, provider, code_messages, "Viết code", status_msg
        )
        task.metrics['total_tokens'] = task.metrics.get('total_tokens', 0) + code_metrics.get('output_tokens', 0)

        # Step 4: PARSE & VALIDATE
        task.status = "validating"
        await _update_agent_status(status_msg, task, 4, 6, "🔍 Parse & kiểm tra syntax...")

        files = FileExtractor.extract(code_text)

        # Extract metadata if present
        meta_match = re.search(r'<<<META>>>(.*?)<<<ENDMETA>>>', code_text, re.DOTALL | re.IGNORECASE)
        if meta_match:
            meta_text = meta_match.group(1)
            for line in meta_text.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    key = key.strip().lower()
                    val = val.strip()
                    if key == 'dependencies':
                        task.dependencies = [d.strip() for d in val.split(',') if d.strip()]
                    elif key == 'language':
                        task.detected_language = val

        if not files:
            # Retry with stronger prompt
            task.auto_retry_count += 1
            if task.auto_retry_count <= Config.AGENT_MAX_RETRIES:
                await _update_agent_status(status_msg, task, 4, 6, 
                    f"⚠️ Parse lỗi, retry {task.auto_retry_count}/{Config.AGENT_MAX_RETRIES}...")

                retry_messages = [
                    {"role": "system", "content": SYSTEM_PROMPT_AGENT},
                    {"role": "user", "content": f"Task: {task.description}\n\nCRITICAL: Your previous response could not be parsed. You MUST use EXACT format:\n<<<FILE:filename.py>>>\n[complete code]\n<<<ENDFILE>>>\n\nRewrite ALL files with this format."}
                ]

                code_text, _ = await StreamingHandler.agent_generate(
                    model_id, provider, retry_messages, f"Retry {task.auto_retry_count}", status_msg
                )
                files = FileExtractor.extract(code_text)

        if not files:
            raise Exception("Could not parse any files from AI response after retries")

        # Auto-generate dependencies
        if Config.AUTO_DEPENDENCY_DETECT:
            extras = FileExtractor.auto_generate_dependencies(files)
            files.update(extras)

        # Validate all files
        all_issues = []
        for fname, content in files.items():
            issues = SyntaxValidator.validate(content, fname)
            all_issues.extend(issues)

        critical = [i for i in all_issues if i['level'] == 'error']

        task.add_checkpoint("validate", 
                          "warning" if critical else "success",
                          {"files": len(files), "errors": len(critical), "warnings": len([i for i in all_issues if i['level'] == 'warning'])},
                          0)

        # Step 5: AUTO-FIX (if critical errors)
        if critical and task.auto_retry_count < Config.AGENT_MAX_RETRIES:
            task.status = "fixing"
            task.auto_retry_count += 1
            await _update_agent_status(status_msg, task, 5, 6, 
                f"🔧 Tự sửa {len(critical)} lỗi... (retry {task.auto_retry_count})")

            fix_messages = [
                {"role": "system", "content": SYSTEM_PROMPT_AGENT_FIX},
                {"role": "user", "content": f"Fix these errors in the code:\n\n{SyntaxValidator.format_issues(critical)}\n\nOriginal task: {task.description}\n\nOutput ONLY corrected files using <<<FILE:>>> format."}
            ]

            fixed_code, _ = await StreamingHandler.agent_generate(
                model_id, provider, fix_messages, "Sửa lỗi", status_msg
            )
            fixed_files = FileExtractor.extract(fixed_code)

            if fixed_files:
                # Validate fixes
                new_issues = []
                for fname, content in fixed_files.items():
                    new_issues.extend(SyntaxValidator.validate(content, fname))
                new_critical = [i for i in new_issues if i['level'] == 'error']

                if len(new_critical) <= len(critical) // 2:
                    files = fixed_files
                    all_issues = new_issues
                    critical = new_critical

        task.files_created = list(files.keys())
        task.file_contents = files

        # Step 6: DEPLOY
        task.status = "deploying"
        await _update_agent_status(status_msg, task, 6, 6, "📦 Deploying...")

        metadata = {
            "task_id": task.task_id,
            "description": task.description,
            "model": model_id,
            "files": list(files.keys()),
            "language": task.detected_language,
            "dependencies": task.dependencies
        }

        deploy_results = []

        if deploy_mode in ['local', 'both']:
            try:
                zip_path, zip_size = await PackageBuilder.create_package(
                    task.task_id, files, metadata, task
                )
                task.local_path = str(zip_path)
                deploy_results.append(f"📦 ZIP: `{zip_size/1024:.1f}KB`")
            except Exception as e:
                deploy_results.append(f"❌ ZIP failed: {str(e)[:50]}")
                logging.error(f"ZIP creation failed: {e}")

        if deploy_mode in ['github', 'both']:
            try:
                success, username = await github.verify_auth()
                if success and username:
                    repo_name = _generate_repo_name(task.description, user_id)
                    task.repo_name = repo_name

                    success_repo, repo_url = await github.create_repo(
                        repo_name, f"Auto: {task.description[:120]}", private=False
                    )

                    if success_repo:
                        success_push, final_url = await github.push_files(
                            username, repo_name, files,
                            f"Denia Agent: {task.description[:80]}"
                        )
                        if success_push:
                            task.repo_url = final_url
                            deploy_results.append(f"🌐 GitHub: [Link]({final_url})")
                        else:
                            deploy_results.append(f"⚠️ GitHub push partial: {final_url[:100]}")
                    else:
                        deploy_results.append(f"⚠️ GitHub repo: {repo_url[:100]}")
                else:
                    deploy_results.append("❌ GitHub auth failed — kiểm tra token")
            except Exception as e:
                deploy_results.append(f"❌ GitHub error: {str(e)[:50]}")
                logging.error(f"GitHub deploy failed: {e}")

        # Complete
        task.status = "completed"
        task.result = "success"
        total_time = time.time() - start_time

        state.usage.record(
            task.metrics.get('input_tokens', 0),
            task.metrics.get('total_tokens', 0),
            total_time,
            model_id,
            TaskType.AGENT_TASK
        )
        state.usage.agent_tasks_completed += 1
        state.add_note(f"Agent success: {task.description[:60]}", success=True)
        SmartModelRouter.record_result(model_id, True, total_time)

        # Build success message
        file_list = "\n".join(f"• `{f}`" for f in task.files_created[:10])
        if len(task.files_created) > 10:
            file_list += f"\n• ... và {len(task.files_created)-10} file khác"

        issues_summary = ""
        if all_issues:
            errors = len([i for i in all_issues if i['level'] == 'error'])
            warns = len([i for i in all_issues if i['level'] == 'warning'])
            if errors == 0:
                issues_summary = f"\n🔍 *Kiểm tra:* `{warns}` warning(s)"
            else:
                issues_summary = f"\n⚠️ *Kiểm tra:* `{errors}` error(s), `{warns}` warning(s)"
        else:
            issues_summary = "\n✅ *Kiểm tra:* Không phát hiện lỗi"

        result_msg = f"""✅ *Agent Task Hoàn Thành\\!*
{'━' * 25}
🆔 `{task.task_id}`
📝 {escape_md(task.description[:90])}{'...' if len(task.description) > 90 else ''}

📁 *Files ({len(task.files_created)}):*
{file_list}
{issues_summary}

📊 *Metrics:*
• ⏱ Thời gian: `{total_time:.1f}s`
• 📝 Tokens: `{task.metrics.get('total_tokens', 0):,}`
• 🔄 Retries: `{task.auto_retry_count}`
• 🤖 Model: `{model_id}`

{'\n'.join(deploy_results)}

💡 *Tip:* Dùng `/stats` để xem lịch sử"""

        await status_msg.edit_text(result_msg, parse_mode=TPM.MARKDOWN_V2)

        # Send ZIP if local
        if task.local_path and os.path.exists(task.local_path):
            with open(task.local_path, 'rb') as f:
                bio = io.BytesIO(f.read())
            bio.name = f"{task.task_id}.zip"
            await update.message.reply_document(
                document=bio,
                caption=f"📦 {len(files)} files | {task.detected_language} | Denia Agent"
            )

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.error_details = traceback.format_exc()
        total_time = time.time() - start_time

        state.usage.agent_tasks_failed += 1
        state.add_note(f"Agent failed: {task.description[:60]} — {str(e)[:80]}", success=False)
        SmartModelRouter.record_result(task.model_used or state.current_model, False, total_time)

        logging.error(f"Agent task failed: {e}\n{traceback.format_exc()}")

        error_msg = f"""❌ *Agent Task Thất Bại*
{'━' * 25}
🆔 `{task.task_id}`
⚠️ *Lỗi:* `{escape_md(str(e)[:200])}`

📊 *Thông tin debug:*
• ⏱ Thời gian: `{total_time:.1f}s`
• 🔄 Retries: `{task.auto_retry_count}`
• 🤖 Model: `{task.model_used or 'unknown'}`

💡 *Khắc phục:*
• Mô tả task chi tiết hơn
• Thử `/agent local` thay vì `github`
• Kiểm tra kết nối mạng
• Dùng `/reset` nếu lỗi liên tục"""

        await status_msg.edit_text(error_msg, parse_mode=TPM.MARKDOWN_V2)

    finally:
        await state_store.save_user(user_id)

async def _update_agent_status(msg: Message, task: AgentTask, step: int, total: int, text: str):
    """Update agent progress message."""
    progress_bar = "▓" * step + "░" * (total - step)
    try:
        await msg.edit_text(
            f"🤖 *Agent Task*\n"
            f"`[{progress_bar}]` {step}/{total}\n"
            f"{'━' * 20}\n"
            f"🆔 `{task.task_id}`\n"
            f"⏳ {escape_md(text)}\n\n"
            f"⏱ Bắt đầu: {task.created_at[:16]}",
            parse_mode=TPM.MARKDOWN_V2
        )
    except BadRequest:
        pass
    except Exception:
        pass

def _select_agent_model(state: ConversationState, description: str) -> Tuple[str, str, str]:
    """Select best model for agent task."""
    if state.auto_model:
        return SmartModelRouter.select_best_model(
            description, state.history, state.budget_conscious, True
        )
    return state.current_model, _get_model_display("agent", state.current_model), state.current_provider

def _detect_project_language(desc: str, analysis: str) -> str:
    """Detect primary programming language."""
    text = (desc + " " + analysis).lower()
    lang_map = {
        'python': ['python', 'fastapi', 'flask', 'django', 'pandas', 'numpy', 'tensorflow'],
        'javascript': ['javascript', 'node.js', 'nodejs', 'express', 'react', 'vue'],
        'typescript': ['typescript', 'angular', 'nestjs', '.ts'],
        'go': ['golang', 'go lang', 'gin', 'echo framework'],
        'rust': ['rust', 'actix', 'rocket.rs'],
        'java': ['java', 'spring boot', 'maven'],
    }
    scores = {lang: sum(1 for k in keywords if k in text) for lang, keywords in lang_map.items()}
    if scores:
        best = max(scores.items(), key=lambda x: x[1])
        if best[1] > 0:
            return best[0]
    return 'python'

def _generate_repo_name(desc: str, user_id: int) -> str:
    """Generate clean repo name from description."""
    words = re.findall(r'[a-zA-Z]+', desc.lower())
    keywords = [w for w in words if len(w) > 2 and w not in 
                {'the', 'and', 'for', 'with', 'create', 'make', 'build', 'using', 'use'}][:6]

    if keywords:
        name = '-'.join(keywords)
    else:
        name = f"denia-project-{user_id % 10000}"

    # Clean
    name = re.sub(r'[^a-z0-9-]', '-', name)
    name = re.sub(r'-+', '-', name).strip('-')

    # GitHub repo name limits
    if len(name) > 50:
        name = name[:50].rsplit('-', 1)[0]

    # Ensure uniqueness with timestamp
    name = f"{name}-{int(time.time()) % 10000}"
    return name[:100] or f"denia-{int(time.time()) % 100000}"

# ============================================================================
# 💬 MESSAGE HANDLER
# ============================================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    text = update.message.text.strip()
    state = get_user_state(user_id)

    # Rate limit
    allowed, msg = await rate_limit_check(update)
    if not allowed:
        await update.message.reply_text(msg, parse_mode=TPM.MARKDOWN)
        return

    # Ignore commands
    if text.startswith('/'):
        return

    # Add to history
    state.history.append({"role": "user", "content": text})

    # Manage history size
    if len(state.history) > Config.MAX_HISTORY * 2:
        if Config.CONTEXT_COMPRESSION:
            state.history = ContextCompressor.compress_history(state.history)
        else:
            state.history = state.history[-Config.MAX_HISTORY * 2:]

    # Typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action=ChatAction.TYPING
    )

    status_msg = await update.message.reply_text(
        "⏳ *Đang suy nghĩ...*",
        parse_mode=TPM.MARKDOWN
    )

    try:
        # Select model
        model_id = state.current_model
        provider = state.current_provider

        if state.auto_model:
            model_id, display, provider = SmartModelRouter.select_best_model(
                text, state.history, state.budget_conscious, Config.STREAMING_RESPONSES
            )
            state.last_model_suggestion = model_id

        # Build messages
        system_prompt = state.get_adaptive_prompt(
            SYSTEM_PROMPT_CHAT if state.mode == 'chat' else SYSTEM_PROMPT_AGENT,
            state.mode
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(state.get_recent_context(Config.MAX_HISTORY))

        # Stream callback
        async def stream_progress(preview: str):
            try:
                preview_clean = preview[-200:].replace('`', '').replace('*', '')
                await status_msg.edit_text(
                    f"🤖 *Đang trả lời...*\n\n`{preview_clean}`\n\n⏳ Đang gõ...",
                    parse_mode=TPM.MARKDOWN
                )
            except:
                pass

        # Call API
        response, metrics = await StreamingHandler.chat_complete(
            model_id, provider, messages,
            status_msg=status_msg,
            progress_callback=stream_progress if Config.STREAMING_RESPONSES else None
        )

        # Update history
        state.history.append({"role": "assistant", "content": response})

        # Record usage
        task_type = SmartModelRouter.detect_task_type(text, state.history)
        state.usage.record(
            metrics.get('input_tokens', 0),
            metrics.get('output_tokens', 0),
            metrics.get('latency', 0),
            model_id,
            task_type
        )
        SmartModelRouter.record_result(model_id, True, metrics.get('latency', 0))
        state.add_note(f"Chat success: {text[:40]}", success=True)

        # Format response
        display = _get_model_display(state.mode, model_id)
        header = f"🤖 *{display}*\n{'━' * 20}\n\n"
        footer = f"\n\n⏱ `{metrics.get('latency', 0):.2f}s` | 📝 `{metrics.get('output_tokens', 0):,}` tokens"

        if state.auto_model and state.last_model_suggestion:
            footer += f" | 🎯 `{state.last_model_suggestion}`"

        full_text = header + response + footer

        # Delete status and send result
        await status_msg.delete()
        await send_long_message(update, full_text)

    except Exception as e:
        logging.error(f"Message handler error: {e}\n{traceback.format_exc()}")
        error_msg = f"""⚠️ *Lỗi xử lý*
{'━' * 15}
`{str(e)[:300]}`

💡 *Thử:*
• `/reset` để xóa lịch sử
• `/models` đổi model khác
• Kiểm tra kết nối mạng"""

        try:
            await status_msg.edit_text(error_msg, parse_mode=TPM.MARKDOWN)
        except:
            await update.message.reply_text(error_msg, parse_mode=TPM.MARKDOWN)

        state.add_note(f"Chat error: {str(e)[:80]}", success=False)
        SmartModelRouter.record_result(model_id, False)

    finally:
        await state_store.save_user(user_id)

# ============================================================================
# 📋 MODEL CONFIGURATION
# ============================================================================

MODE_CONFIG = {
    "chat": {
        "name": "💬 Chat",
        "models": [
            ("GLM", "z-ai/glm-5.1", "GLM-5.1", "nvidia"),
            ("MiniMax", "minimax-m2.5-free", "MiniMax M2.5 Free", "opencode"),
            ("MiniMax", "minimaxai/minimax-m2.7", "MiniMax M2.7", "nvidia"),
            ("Mistral", "mistralai/mistral-large-3-675b-instruct-2512", "Mistral Large 3", "nvidia"),
        ],
        "default": Config.DEFAULT_CHAT_MODEL
    },
    "agent": {
        "name": "🤖 Agent",
        "models": [
            ("MiniMax", "minimaxai/minimax-m2.7", "MiniMax M2.7", "nvidia"),
            ("GLM", "z-ai/glm-5.1", "GLM-5.1", "nvidia"),
            ("Mistral", "mistralai/mistral-large-3-675b-instruct-2512", "Mistral Large 3", "nvidia"),
            ("MiniMax", "minimax-m2.5-free", "MiniMax M2.5 Free", "opencode"),
        ],
        "default": Config.DEFAULT_AGENT_MODEL
    },
}

def _get_model_display(mode: str, model_id: str) -> str:
    for cat, mid, display, provider in MODE_CONFIG.get(mode, {}).get("models", []):
        if mid == model_id:
            return f"{CATEGORY_EMOJI.get(cat, '⚪')} {display} ({PROVIDER_EMOJI.get(provider, '')})"
    return model_id

# ============================================================================
# 🧹 MAINTENANCE TASKS
# ============================================================================

async def periodic_maintenance():
    """Background maintenance: cleanup and save."""
    while True:
        try:
            await asyncio.sleep(300)  # Every 5 minutes

            # Save dirty states
            if state_store._dirty:
                await state_store._save()

            # Cleanup old tasks
            state_store.cleanup_old_tasks(Config.ZIP_RETENTION_HOURS)

            # Cleanup old ZIP files
            cutoff = time.time() - Config.ZIP_RETENTION_HOURS * 3600
            cleaned = 0
            for zip_file in (Config.WORK_DIR / "zips").glob("*.zip"):
                if zip_file.stat().st_mtime < cutoff:
                    zip_file.unlink()
                    cleaned += 1

            if cleaned > 0:
                logging.info(f"🗑️ Cleaned {cleaned} old ZIP files")

        except Exception as e:
            logging.error(f"Maintenance error: {e}")

# ============================================================================
# 🚀 MAIN ENTRY POINT — FIXED EVENT LOOP
# ============================================================================

async def main():
    """Async main entry point with proper event loop handling."""
    Config.init()

    # Platform-specific event loop policy (fixes Windows issues)
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    logging.info("🚀 Initializing Denia Bot v9.0 Pro...")

    # Build application
    application = (
        ApplicationBuilder()
        .token(Config.BOT_TOKEN)
        .concurrent_updates(True)
        .get_updates_read_timeout(30)
        .get_updates_write_timeout(30)
        .build()
    )

    # Register handlers
    application.add_handler(CommandHandler('start', cmd_start))
    application.add_handler(CommandHandler('help', cmd_help))
    application.add_handler(CommandHandler('models', cmd_models))
    application.add_handler(CommandHandler('agent', cmd_agent))
    application.add_handler(CommandHandler('stats', cmd_stats))
    application.add_handler(CommandHandler('reset', cmd_reset))
    application.add_handler(CommandHandler('style', cmd_style))
    application.add_handler(CommandHandler('deploy', cmd_deploy))

    # Callback handler (consolidated)
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Message handler
    application.add_handler(MessageHandler(
        filters.TEXT & (~filters.COMMAND), 
        handle_message
    ))

    # Error handler
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logging.error(f"Update {update} caused error: {context.error}")

        if update and update.effective_user:
            state = get_user_state(update.effective_user.id)
            state.add_note(f"System error: {str(context.error)[:150]}", success=False)

        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "😵 *Đã xảy ra lỗi không mong muốn\\!*\n"
                    "Vui lòng thử lại sau.\n\n"
                    "💡 *Thử:* `/reset` hoặc `/help`",
                    parse_mode=TPM.MARKDOWN_V2
                )
            except:
                pass

    application.add_error_handler(error_handler)

    # Post-init: start background tasks
    async def post_init(app: Application):
        app.bot_data['github'] = github
        asyncio.create_task(periodic_maintenance())
        logging.info("✅ Bot initialized. Background tasks started.")

    # Post-shutdown: cleanup
    async def post_shutdown(app: Application):
        await github.close()
        await state_store.force_save()
        logging.info("🔒 Shutdown complete. All sessions closed.")

    application.post_init = post_init
    application.post_shutdown = post_shutdown

    # Graceful shutdown handling
    def signal_handler(sig, frame):
        logging.info(f"Received signal {sig}, shutting down gracefully...")
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    if platform.system() != 'Windows':
        signal.signal(signal.SIGHUP, signal_handler)

    logging.info("✅ Bot is running. Press Ctrl+C to stop.")

    # Start polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)

    # Keep running until interrupted
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    # CRITICAL FIX: Use asyncio.run() to properly manage event loop
    # This resolves "There is no current event loop in thread 'MainThread'"
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("👋 Bot stopped by user.")
    except Exception as e:
        logging.critical(f"Fatal error: {e}\n{traceback.format_exc()}")
        sys.exit(1)
