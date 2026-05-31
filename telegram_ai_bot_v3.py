import logging
import requests
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# ================= CONFIGURATION =================

# 1. Telegram Bot Token
TELEGRAM_BOT_TOKEN = "8909561772:AAGQgxrbvXbi-RACF4_Z7iiS4R7NA6Za6wU"

# 2. AI Provider Settings (Single Endpoint)
API_BASE_URL = "https://ckey.vn/v1/chat/completions"
API_KEY = "sk-e317a237354192e26f99951f06e4882779e8a0e08e86d2f71242e8ff770bdf24"

# 3. Model List (From your data)
# Format: "Display Name": "Model_ID_for_API"
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

# Default Model to start with
DEFAULT_MODEL_KEY = "🚀 GLM4.7" 

# System Prompt
SYSTEM_PROMPT = "You are a helpful, intelligent, and concise AI assistant."

# =================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store user state: { chat_id: { 'history': [], 'current_model_key': '...' } }
user_states = {}

def get_user_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = {
            'history': [],
            'current_model_key': DEFAULT_MODEL_KEY
        }
    return user_states[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = get_user_state(update.effective_user.id)
    current_model_name = state['current_model_key']
    
    welcome_msg = (
        f"👋 *Welcome to FizzPop AI Bot!*\n\n"
        f"I am connected to multiple high-end AI models.\n"
        f"Currently using: *{current_model_name}*\n\n"
        f"📂 Use /models to see the full list.\n"
        f"🔄 Use /switch <number> to change model.\n"
        f"🗑 Use /reset to clear chat history."
    )
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def show_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all available models with numbers."""
    model_keys = list(AVAILABLE_MODELS.keys())
    state = get_user_state(update.effective_user.id)
    current_key = state['current_model_key']
    
    message = "📂 *Available AI Models*\n________________________\n"
    
    for index, key in enumerate(model_keys, 1):
        # Mark current model
        marker = "✅" if key == current_key else "⚪"
        # Truncate long names for cleaner display if needed, but keeping full for now
        message += f"*{index}.* {marker} {key}\n"
        
    message += "\n👉 *Reply with:* `/switch <number>`\n(e.g., `/switch 2` to use GLM4.7)"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def switch_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Switches the active model based on user input number."""
    if not context.args:
        await update.message.reply_text("❌ *Error:* Please provide a number.\nExample: `/switch 1`", parse_mode='Markdown')
        return
    
    try:
        choice = int(context.args[0])
        model_keys = list(AVAILABLE_MODELS.keys())
        
        if 1 <= choice <= len(model_keys):
            selected_key = model_keys[choice - 1]
            state = get_user_state(update.effective_user.id)
            state['current_model_key'] = selected_key
            
            # Optional: Clear history when switching to avoid context confusion between different model architectures
            # state['history'] = [] 
            
            await update.message.reply_text(f"✅ *Success!* Switched to:\n*{selected_key}*", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ *Error:* Number out of range. Choose between 1 and {len(model_keys)}.", parse_mode='Markdown')
            
    except ValueError:
        await update.message.reply_text("❌ *Error:* Please enter a valid number.", parse_mode='Markdown')

async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clears chat history."""
    user_id = update.effective_user.id
    if user_id in user_states:
        user_states[user_id]['history'] = []
    await update.message.reply_text("🗑 *Chat history cleared.*", parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    user_input = update.message.text
    state = get_user_state(user_id)
    
    # Get Model ID from the selected Key
    model_key = state['current_model_key']
    if model_key not in AVAILABLE_MODELS:
        # Fallback if key is missing
        model_key = DEFAULT_MODEL_KEY
        state['current_model_key'] = DEFAULT_MODEL_KEY
        
    model_id = AVAILABLE_MODELS[model_key]
    
    # Show typing action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Manage History (Keep last 10 messages to save tokens)
    state['history'].append({"role": "user", "content": user_input})
    if len(state['history']) > 10:
        state['history'] = state['history'][-10:]

    # Prepare Payload
    messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}] + state['history']

    try:
        # Call API
        ai_response = call_ai_api(model_id, messages_payload)
        
        if ai_response:
            # Append AI response to history
            state['history'].append({"role": "assistant", "content": ai_response})
            
            # Format and Send Response
            formatted_response = f"🤖 *{model_key}*\n________________________\n{ai_response}"
            await send_long_message(update, formatted_response)
        else:
            await update.message.reply_text("❌ *Error:* No response from AI.", parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"⚠️ *API Error:* {str(e)}", parse_mode='Markdown')

def call_ai_api(model_id, messages):
    """Sends request to the configured AI API endpoint."""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    data = {
        "model": model_id,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048
    }

    try:
        response = requests.post(API_BASE_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()  # Raise exception for bad status codes
        
        result = response.json()
        
        # Extract content
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            logger.error(f"Unexpected API response: {result}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"API Error Detail: {e.response.text}")
        raise e

async def send_long_message(update, text):
    """Telegram has a limit of 4096 chars per message. This splits long texts."""
    max_len = 4000
    if len(text) <= max_len:
        await update.message.reply_text(text, parse_mode='Markdown')
    else:
        chunks = [text[i:i+max_len] for i in range(0, len(text), max_len)]
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode='Markdown')

if __name__ == '__main__':
    logger.info("Bot is starting...")
    
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers
    start_handler = CommandHandler('start', start)
    models_handler = CommandHandler('models', show_models)
    switch_handler = CommandHandler('switch', switch_model)
    reset_handler = CommandHandler('reset', reset_chat)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)

    application.add_handler(start_handler)
    application.add_handler(models_handler)
    application.add_handler(switch_handler)
    application.add_handler(reset_handler)
    application.add_handler(message_handler)

    application.run_polling(drop_pending_updates=True)
