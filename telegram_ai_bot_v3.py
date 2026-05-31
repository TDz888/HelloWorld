#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════╗
║                    🤖 FizzPop AI Bot v2.0                     ║
║              Advanced Multi-Model AI Assistant                ║
╚═══════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import logging
import time
import re
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
API_BASE_URL = "https://ckey.vn/v1/chat/completions"
API_KEY = "sk-e317a237354192e26f99951f06e4882779e8a0e08e86d2f71242e8ff770bdf24"

SYSTEM_PROMPT = "You are a helpful, intelligent, and concise AI assistant."

DEFAULT_MODEL_KEY = "🚀 GLM4.7"
MAX_HISTORY = 24
MAX_OUTPUT_TOKENS = 4096
STATUS_UPDATE_INTERVAL = 2.0

AVAILABLE_MODELS = {
    "💎 Gemini Embedding 2": "gemini-embedding-2-preview",
    "🚀 GLM4.7": "glm4.7",
    "👨‍💻 Qwen3 Coder 480B": "qwen3-coder-480b-a35b-instruct",
    "⚡ Mistral Medium 3.5": "mistral-medium-3.5-128b",
    "🧠 Mistral Small 4": "mistral-small-4-119b-2603",
    "🔥 DeepSeek V3 (DeepSeek-3.2)": "deepseek-3.2",
    "🐬 DeepSeek R1 Distill Qwen": "deepseek-r1-distill-qwen-32b",
    "🦙 Llama Nemotron Embed": "llama-nemotron-embed-vl-1b-v2",
    "🇻🇳 ViTTS HoaiMy": "google-tts/vi",
    "🏆 Mistral Large 3 (ChieuStudio)": "chieustudio/mistral-large-3-675b-instruct-2512",
    "🤖 DeepSeek R1 (ChieuStudio)": "chieustudio/deepseek-r1",
    "🌟 MiniMax M2.7": "namtran96hth/MiniMax-M2.7",
    "📝 Text Embedding 3 Small": "text-embedding-3-small",
    "🚀 Qwen3 Coder Next": "qwen3-coder-next",
    "💎 MiniMax M2.5": "minimax-m2.5",
    "💎 MiniMax M2.1": "minimax-m2.1",
    "🏆 Mistral Large 3 (Official)": "mistral-large-3-675b-instruct-2512",
    "⚡ DeepSeek V4 Flash": "deepseek-v4-flash",
    "⚡ DeepSeek V4 Flash (Vyke)": "vykelongthuong/Deepseek V4 Flash",
    "🤖 Kimi K2.5": "kimi-k2.5",
    "🐉 GLM-5": "glm-5",
    "🤖 Kimi K2.6": "kimi-k2.6",
    "🤔 Grok 4.20 Thinking": "grok-4.20-thinking",
    "🤖 Grok 4.3": "grok-4.3",
    "⚡ Grok 4.20 Fast": "grok-4.20-fast",
    "🤖 GPT-5.4 Mini": "gpt-5.4-mini",
    "🐉 GLM-5.1": "glm-5.1",
    "🤖 Claude Haiku 4.5": "claude-haiku-4.5",
    "🤖 GPT-5.2": "gpt-5.2",
    "🤖 GPT-5.3 Codex": "gpt-5.3-codex",
    "🤖 GPT-5.3 Codex High": "gpt-5.3-codex-high",
    "🤖 GPT-5.4": "gpt-5.4",
    "🤖 Claude Sonnet 4.6": "claude-sonnet-4.6",
    "🤖 Claude Sonnet 4.5": "claude-sonnet-4.5",
    "🤖 Qwen 3.7 Max": "phuocanh421994/Qwen 3.7 max",
    "🤖 GPT-5.5 (Vyke)": "vykelongthuong/GPT 5.5",
    "🤖 GPT-5.5 (W3leee)": "w3leee/GPT 5.5",
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
    current_model_key: str = DEFAULT_MODEL_KEY
    stats: UserStats = field(default_factory=UserStats)

# ==================== STATE MANAGEMENT ====================

user_states: Dict[int, ConversationState] = {}

def get_user_state(user_id: int) -> ConversationState:
    if user_id not in user_states:
        user_states[user_id] = ConversationState()
    return user_states[user_id]

# ==================== UTILITIES ====================

def estimate_tokens(text: str) -> int:
    """Estimate token count. ~4 bytes per token for mixed content."""
    if not text:
        return 0
    return max(1, len(text.encode('utf-8')) // 4)

def split_smart(text: str, max_len: int = 4000) -> List[str]:
    """
    Smart message splitting that respects code blocks and newlines.
    """
    if len(text) <= max_len:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= max_len:
            chunks.append(remaining)
            break

        split_pos = remaining.rfind('\n', 0, max_len)
        if split_pos == -1:
            split_pos = remaining.rfind(' ', 0, max_len)
        if split_pos == -1 or split_pos < max_len * 0.5:
            split_pos = max_len

        chunk = remaining[:split_pos]
        remaining = remaining[split_pos:].lstrip()

        # Check code block integrity
        code_blocks = chunk.count('```')
        if code_blocks % 2 != 0:
            chunk += '\n```'
            remaining = '```\n' + remaining

        chunks.append(chunk)

    return chunks

def build_metrics_footer(metrics: Dict[str, Any], state: ConversationState) -> str:
    """Build beautiful metrics footer."""
    latency = metrics.get('latency', 0)
    inp = metrics.get('input_tokens', 0)
    out = metrics.get('output_tokens', 0)
    total = inp + out
    tps = metrics.get('tps', 0)

    # Update user stats
    state.stats.total_requests += 1
    state.stats.total_input_tokens += inp
    state.stats.total_output_tokens += out
    state.stats.total_latency += latency
    state.stats.last_active = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    footer = (
        f"\n\n{'━' * 18}\n"
        f"📊 *Metrics*\n"
        f"• ⏱ Latency: `{latency:.2f}s`\n"
        f"• 📝 Input: `{inp}` tokens\n"
        f"• 💬 Output: `{out}` tokens\n"
        f"• 📦 Total: `{total}` tokens\n"
        f"• ⚡ Speed: `{tps:.1f}` tok/s"
    )
    return footer

# ==================== API CLIENT ====================

async def call_ai_api(
    session: aiohttp.ClientSession,
    model_id: str,
    messages: List[Dict[str, str]],
    status_msg: Any,
    context: ContextTypes.DEFAULT_TYPE
) -> Tuple[str, Dict[str, Any]]:
    """
    Call AI API with NO TIMEOUT and periodic status updates.
    Returns (content, metrics_dict)
    """

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

    # Status updater coroutine
    async def _update_status():
        dots = 0
        while True:
            try:
                await asyncio.sleep(STATUS_UPDATE_INTERVAL)
                elapsed = time.time() - start_time
                dots = (dots + 1) % 4
                status_text = (
                    f"⏳ *Đang suy nghĩ{'·' * dots}{' ' * (3-dots)}*\n\n"
                    f"🤖 *Model:* `{model_id}`\n"
                    f"⏱ *Thời gian chờ:* `{elapsed:.1f}s`\n"
                    f"💡 *Trạng thái:* `Đang tạo phản hồi...`"
                )
                await status_msg.edit_text(
                    status_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                pass

    # Start status updates
    status_task = asyncio.create_task(_update_status())

    try:
        # NO TIMEOUT for long AI responses
        timeout = aiohttp.ClientTimeout(total=None, connect=30)

        async with session.post(
            API_BASE_URL,
            headers=headers,
            json=payload,
            timeout=timeout
        ) as resp:

            if resp.status != 200:
                error_body = await resp.text()
                raise aiohttp.ClientResponseError(
                    resp.request_info,
                    resp.history,
                    status=resp.status,
                    message=f"API Error: {error_body[:500]}"
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
        raise ValueError(f"No choices in API response: {json.dumps(result, ensure_ascii=False)[:500]}")

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

# ==================== HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with beautiful formatting."""
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    model_name = state.current_model_key

    welcome = (
        f"╔════════════════════╗\n"
        f"║   🤖 *FizzPop AI*   ║\n"
        f"╚════════════════════╝\n\n"
        f"👋 Chào mừng *{update.effective_user.first_name or 'bạn'}*!\n\n"
        f"🧠 Tôi là trợ lý AI đa mô hình thông minh.\n"
        f"🚀 Hiện đang sử dụng: *{model_name}*\n\n"
        f"📚 *Hướng dẫn nhanh:*\n"
        f"• 💬 Chat trực tiếp để hỏi AI\n"
        f"• 📂 /models - Chọn mô hình AI\n"
        f"• ℹ️ /status - Xem trạng thái hiện tại\n"
        f"• 📊 /stats - Thống kê sử dụng\n"
        f"• 🗑 /reset - Xóa lịch sử chat\n"
        f"• ❓ /help - Trợ giúp chi tiết\n\n"
        f"💡 *Mẹo:* Dùng `/models` để chọn model phù hợp với từng tác vụ."
    )

    await update.message.reply_text(
        welcome,
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detailed help with commands."""
    help_text = (
        f"📖 *Hướng Dẫn Sử Dụng*\n"
        f"{'━' * 22}\n\n"
        f"🚀 *Lệnh chính:*\n"
        f"• `/start` - Khởi động bot\n"
        f"• `/models` - Danh sách model (có nút bấm)\n"
        f"• `/switch <số>` - Đổi model nhanh\n"
        f"• `/status` - Xem model & lịch sử\n"
        f"• `/stats` - Thống kê tổng quát\n"
        f"• `/reset` - Xóa lịch sử trò chuyện\n"
        f"• `/help` - Hiển thị trợ giúp này\n\n"
        f"💡 *Tính năng nổi bật:*\n"
        f"• ⏱ *Không timeout* - Chờ AI trả lời dù lâu\n"
        f"• 📊 *Metrics real-time* - Xem tốc độ, token\n"
        f"• 🧠 *Nhớ context* - Giữ {MAX_HISTORY} tin nhắn gần nhất\n"
        f"• 🎨 *Markdown đẹp* - Hỗ trợ code, bảng, in đậm\n\n"
        f"⚠️ *Lưu ý:*\n"
        f"• Nếu AI trả lời lâu, bot sẽ hiển thị trạng thái chờ\n"
        f"• Tin nhắn quá dài sẽ được tự động chia nhỏ\n"
        f"• Dùng `/reset` nếu AI bị lẫn ngữ cảnh cũ"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def show_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show models with inline keyboard."""
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    current = state.current_model_key

    keyboard = []
    row = []
    model_keys = list(AVAILABLE_MODELS.keys())

    for idx, key in enumerate(model_keys, 1):
        prefix = "✅ " if key == current else ""
        display = f"{prefix}{idx}. {key[:22]}"
        button = InlineKeyboardButton(
            display,
            callback_data=f"model_{idx}"
        )
        row.append(button)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔄 Làm mới", callback_data="refresh_models")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    header = (
        f"📂 *Danh Sách Mô Hình AI*\n"
        f"{'━' * 22}\n"
        f"✅ = Đang sử dụng: *{current}*\n\n"
        f"👇 *Chọn model bên dưới:*"
    )

    await update.message.reply_text(
        header,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def model_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle model selection from inline keyboard."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    state = get_user_state(user_id)
    data = query.data

    if data == "refresh_models":
        await query.edit_message_text("🔄 Đang làm mới...")
        # Re-trigger by sending a new message
        keyboard = []
        row = []
        model_keys = list(AVAILABLE_MODELS.keys())
        for idx, key in enumerate(model_keys, 1):
            prefix = "✅ " if key == state.current_model_key else ""
            button = InlineKeyboardButton(
                f"{prefix}{idx}. {key[:22]}",
                callback_data=f"model_{idx}"
            )
            row.append(button)
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔄 Làm mới", callback_data="refresh_models")])

        await query.edit_message_text(
            f"📂 *Danh Sách Mô Hình AI*\n{'━' * 22}\n✅ = Đang sử dụng: *{state.current_model_key}*\n\n👇 *Chọn model bên dưới:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("model_"):
        try:
            choice = int(data.split("_")[1])
            model_keys = list(AVAILABLE_MODELS.keys())

            if 1 <= choice <= len(model_keys):
                selected = model_keys[choice - 1]
                state.current_model_key = selected

                await query.edit_message_text(
                    f"✅ *Đã chuyển model!*\n\n"
                    f"🤖 Hiện tại: *{selected}*\n"
                    f"🆔 ID: `{AVAILABLE_MODELS[selected]}`\n\n"
                    f"💡 Gõ `/reset` nếu muốn xóa ngữ cảnh cũ trước khi chat.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await query.edit_message_text(
                    "❌ Số không hợp lệ.",
                    parse_mode=ParseMode.MARKDOWN
                )
        except ValueError:
            await query.edit_message_text(
                "❌ Lỗi xử lý lựa chọn.",
                parse_mode=ParseMode.MARKDOWN
            )

async def switch_model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Switch model via command."""
    if not context.args:
        await update.message.reply_text(
            "❌ *Cú pháp:* `/switch <số>`\n"
            "Ví dụ: `/switch 2`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        choice = int(context.args[0])
        model_keys = list(AVAILABLE_MODELS.keys())

        if 1 <= choice <= len(model_keys):
            selected = model_keys[choice - 1]
            state = get_user_state(update.effective_user.id)
            state.current_model_key = selected

            await update.message.reply_text(
                f"✅ *Đã chuyển model!*\n\n"
                f"🤖 Model: *{selected}*",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                f"❌ Chọn số từ 1 đến {len(model_keys)}.",
                parse_mode=ParseMode.MARKDOWN
            )
    except ValueError:
        await update.message.reply_text(
            "❌ Vui lòng nhập số hợp lệ.",
            parse_mode=ParseMode.MARKDOWN
        )

async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset conversation history."""
    user_id = update.effective_user.id
    if user_id in user_states:
        user_states[user_id].history = []

    await update.message.reply_text(
        "🗑 *Đã xóa lịch sử trò chuyện!*\n"
        "🆕 Bắt đầu ngữ cảnh mới.",
        parse_mode=ParseMode.MARKDOWN
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current status."""
    user_id = update.effective_user.id
    state = get_user_state(user_id)

    history_len = len(state.history)
    model = state.current_model_key
    model_id = AVAILABLE_MODELS.get(model, "unknown")

    status = (
        f"ℹ️ *Trạng Thái Hiện Tại*\n"
        f"{'━' * 20}\n\n"
        f"🤖 *Model:* {model}\n"
        f"🆔 *ID:* `{model_id}`\n"
        f"💬 *Lịch sử:* `{history_len // 2}` cặp hỏi/đáp\n"
        f"📝 *Tin nhắn lưu:* `{history_len}/{MAX_HISTORY * 2}`\n"
        f"📅 *Bắt đầu:* `{state.stats.first_seen}`\n"
        f"🕐 *Hoạt động cuối:* `{state.stats.last_active}`"
    )
    await update.message.reply_text(status, parse_mode=ParseMode.MARKDOWN)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show usage statistics."""
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    s = state.stats

    avg_latency = s.total_latency / s.total_requests if s.total_requests > 0 else 0

    stats_text = (
        f"📊 *Thống Kê Sử Dụng*\n"
        f"{'━' * 20}\n\n"
        f"🔢 *Tổng request:* `{s.total_requests}`\n"
        f"📝 *Input tokens:* `{s.total_input_tokens}`\n"
        f"💬 *Output tokens:* `{s.total_output_tokens}`\n"
        f"📦 *Tổng tokens:* `{s.total_input_tokens + s.total_output_tokens}`\n"
        f"⏱ *Tổng thời gian:* `{s.total_latency:.2f}s`\n"
        f"⚡ *Latency TB:* `{avg_latency:.2f}s`\n"
        f"📅 *Bắt đầu:* `{s.first_seen}`\n"
        f"🕐 *Cuối cùng:* `{s.last_active}`"
    )
    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main message handler with full status and metrics."""
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    user_input = update.message.text.strip()
    state = get_user_state(user_id)

    if not user_input:
        return

    # Get model
    model_key = state.current_model_key
    if model_key not in AVAILABLE_MODELS:
        model_key = DEFAULT_MODEL_KEY
        state.current_model_key = DEFAULT_MODEL_KEY

    model_id = AVAILABLE_MODELS[model_key]

    # Send initial status message
    status_msg = await update.message.reply_text(
        f"⏳ *Đang khởi tạo...*\n"
        f"🤖 Model: `{model_id}`",
        parse_mode=ParseMode.MARKDOWN
    )

    # Typing action
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    # Update history
    state.history.append({"role": "user", "content": user_input})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]

    # Prepare messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state.history

    # Get session
    session = context.bot_data.get('session')
    if not session:
        session = aiohttp.ClientSession()
        context.bot_data['session'] = session

    try:
        # Call API
        ai_response, metrics = await call_ai_api(
            session, model_id, messages, status_msg, context
        )

        # Update history with AI response
        state.history.append({"role": "assistant", "content": ai_response})
        if len(state.history) > MAX_HISTORY * 2:
            state.history = state.history[-(MAX_HISTORY * 2):]

        # Build response
        header = f"🤖 *{model_key}*\n{'━' * 20}\n\n"
        footer = build_metrics_footer(metrics, state)
        full_text = header + ai_response + footer

        # Delete status message
        try:
            await status_msg.delete()
        except Exception:
            pass

        # Send response (split if too long)
        chunks = split_smart(full_text, 4000)

        for idx, chunk in enumerate(chunks):
            try:
                await update.message.reply_text(
                    chunk,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                # Fallback to plain text if markdown parse fails
                logger.warning(f"Markdown parse failed, sending plain: {e}")
                await update.message.reply_text(chunk)

            if idx < len(chunks) - 1:
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id,
                    action=ChatAction.TYPING
                )
                await asyncio.sleep(0.5)

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        error_msg = (
            f"⚠️ *Lỗi xử lý*\n"
            f"{'━' * 15}\n"
            f"`{str(e)[:400]}`\n\n"
            f"💡 *Thử:* `/reset` hoặc đổi model qua `/models`"
        )
        try:
            await status_msg.edit_text(error_msg, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler."""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "😵 *Đã xảy ra lỗi không mong muốn!*\n"
            "Vui lòng thử lại sau.",
            parse_mode=ParseMode.MARKDOWN
        )

# ==================== MAIN ====================

async def post_init(application: Application):
    """Initialize bot data."""
    application.bot_data['session'] = aiohttp.ClientSession()
    logger.info("✅ Bot initialized. aiohttp session created.")

async def post_shutdown(application: Application):
    """Cleanup."""
    session = application.bot_data.get('session')
    if session:
        await session.close()
        logger.info("🛑 Session closed.")

def main():
    logger.info("🚀 Starting FizzPop AI Bot v2.0...")

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('models', show_models))
    application.add_handler(CommandHandler('switch', switch_model_command))
    application.add_handler(CommandHandler('reset', reset_chat))
    application.add_handler(CommandHandler('status', status_command))
    application.add_handler(CommandHandler('stats', stats_command))

    # Callback handler for inline keyboards
    application.add_handler(CallbackQueryHandler(model_callback))

    # Message handler
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Error handler
    application.add_error_handler(error_handler)

    # Run
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
