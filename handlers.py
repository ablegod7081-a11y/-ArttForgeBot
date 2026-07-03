import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
import httpx
from openai import AsyncOpenAI

from config import config
from utils import SessionManager, RateLimiter, format_prompt, parse_command_args

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = AsyncOpenAI(
    api_key=config.get_openai_key(),
    timeout=httpx.Timeout(60.0, connect=10.0)
)

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_text = (
        "🎨 *Welcome to ArttForgeBot!*\n\n"
        "I use AI to create stunning images from your text descriptions.\n\n"
        "✨ *Quick Commands:*\n"
        "`/generate [prompt]` - Create an image\n"
        "`/imagine [prompt]` - Same as generate\n"
        "`/settings` - Customize preferences\n"
        "`/help` - Show all commands\n"
        "`/about` - About this bot\n\n"
        "💡 *Example:*\n"
        "`/generate a magical forest with glowing mushrooms, fantasy art style`\n\n"
        "⚡ *Note:* You can make 30 requests per hour."
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "🆘 *Help & Commands*\n\n"
        "📝 *Main Commands:*\n"
        "`/start` - Start the bot\n"
        "`/generate [prompt]` - Generate an image\n"
        "`/imagine [prompt]` - Same as generate\n"
        "`/settings` - Adjust settings\n"
        "`/help` - Show this help\n"
        "`/about` - About this bot\n\n"
        "🎯 *Tips for Better Images:*\n"
        "• Be descriptive: colors, mood, lighting\n"
        "• Specify art styles: watercolor, 3D, oil painting\n"
        "• Include details: composition, perspective\n"
        "• Mention subjects: objects, people, animals\n\n"
        "📐 *Settings Available:*\n"
        "• Size: Square, Portrait, Landscape\n"
        "• Quality: Standard or HD\n"
        "• Style: Natural or Vivid\n\n"
        "⚡ *Rate Limit:* 30 requests per hour\n"
        "💡 Use `/settings` to customize!"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command"""
    about_text = (
        "🤖 *About ArttForgeBot*\n\n"
        "ArttForgeBot is an AI image generator powered by OpenAI's DALL-E 3 technology.\n\n"
        "🔧 *Technology Stack:*\n"
        "• OpenAI DALL-E 3 API\n"
        "• Python Telegram Bot v20\n"
        "• Hosted on Railway\n"
        "• Async architecture\n\n"
        "📊 *Version:* 2.0.0\n"
        "📅 *Last Updated:* 2026\n\n"
        "💡 *Pro Tip:* Use descriptive prompts for best results!\n\n"
        "⭐ *Open Source:*\n"
        "https://github.com/yourusername/ArttForgeBot\n\n"
        "❤️ *Enjoying the bot?* Share it with friends!"
    )
    await update.message.reply_text(about_text, parse_mode=ParseMode.MARKDOWN)

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /generate and /imagine commands"""
    user_id = update.effective_user.id
    prompt = parse_command_args(update.message.text)
    
    # Check if prompt exists
    if not prompt:
        await update.message.reply_text(
            "❌ *Please provide a prompt!*\n\n"
            "Example:\n"
            "`/generate a cute cat playing with yarn`\n"
            "`/imagine a futuristic city at night, cyberpunk style`\n\n"
            "Use `/help` for more tips.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Check rate limit
    is_allowed, limit_data = RateLimiter.check_limit(user_id)
    if not is_allowed:
        minutes = limit_data // 60
        await update.message.reply_text(
            f"⏳ *Rate limit exceeded*\n\n"
            f"You have made 30 requests in the last hour.\n"
            f"Please wait {minutes} minutes before trying again.\n\n"
            "💡 *Tip:* Higher quality images use more credits.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Get user settings
    settings = SessionManager.get_settings(user_id)
    size = settings.get('size', '1024x1024')
    quality = settings.get('quality', 'standard')
    style = settings.get('style', 'natural')
    
    # Send processing message
    status_msg = await update.message.reply_text(
        f"🎨 *Generating your image...*\n\n"
        f"📝 Prompt: _{format_prompt(prompt)}_\n"
        f"📐 Size: {size}\n"
        f"✨ Quality: {quality.upper()}\n"
        f"⏳ Remaining: {limit_data} of 30\n\n"
        "This may take 10-30 seconds...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        # Generate image with OpenAI
        response = await openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
            style=style
        )
        
        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt
        
        # Download the image
        async with httpx.AsyncClient() as client:
            image_response = await client.get(image_url, timeout=30.0)
            image_data = image_response.content
        
        # Delete status message
        await status_msg.delete()
        
        # Send the image
        await update.message.reply_photo(
            photo=image_data,
            caption=(
                f"🖼️ *Generated Image*\n\n"
                f"📝 Prompt: _{format_prompt(prompt, 80)}_\n"
                f"🔄 Revised: _{format_prompt(revised_prompt, 80)}_\n"
                f"📐 Size: {size}\n"
                f"✨ Quality: {quality.upper()}\n"
                f"🎨 Style: {style.upper()}\n\n"
                f"💡 Remaining requests: {limit_data - 1}"
            ),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error generating image for user {user_id}: {e}")
        await status_msg.edit_text(
            f"❌ *Error generating image*\n\n"
            f"Error: {str(e)[:200]}\n\n"
            "Please try:\n"
            "• A different prompt\n"
            "• Simpler description\n"
            "• Again in a few seconds\n\n"
            "If this persists, contact support."
        )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command"""
    user_id = update.effective_user.id
    settings = SessionManager.get_settings(user_id)
    
    keyboard = [
        [
            InlineKeyboardButton("📐 Size", callback_data="settings_size"),
            InlineKeyboardButton("✨ Quality", callback_data="settings_quality"),
        ],
        [
            InlineKeyboardButton("🎨 Style", callback_data="settings_style"),
            InlineKeyboardButton("🔄 Reset", callback_data="settings_reset"),
        ],
        [
            InlineKeyboardButton("📊 Current Settings", callback_data="settings_view"),
        ]
    ]
    
    message = (
        "⚙️ *Settings*\n\n"
        "Customize how your images are generated:\n\n"
        f"{SessionManager.format_settings(settings)}\n\n"
        "Select an option below:"
    )
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings callback queries"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    action = data.split('_')[1] if '_' in data else data
    
    # Handle reset
    if action == 'reset':
        SessionManager.reset_settings(user_id)
        await query.edit_message_text(
            "✅ *Settings Reset to Default*\n\n"
            "• Size: 1024x1024 (Square)\n"
            "• Quality: Standard\n"
            "• Style: Natural\n\n"
            "Use `/settings` to customize again.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Handle view
    if action == 'view':
        settings = SessionManager.get_settings(user_id)
        await query.edit_message_text(
            f"📊 *Current Settings*\n\n"
            f"{SessionManager.format_settings(settings)}",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Handle back
    if action == 'back':
        settings = SessionManager.get_settings(user_id)
        keyboard = [
            [
                InlineKeyboardButton("📐 Size", callback_data="settings_size"),
                InlineKeyboardButton("✨ Quality", callback_data="settings_quality"),
            ],
            [
                InlineKeyboardButton("🎨 Style", callback_data="settings_style"),
                InlineKeyboardButton("🔄 Reset", callback_data="settings_reset"),
            ],
            [
                InlineKeyboardButton("📊 Current Settings", callback_data="settings_view"),
            ]
        ]
        await query.edit_message_text(
            f"⚙️ *Settings*\n\n"
            f"{SessionManager.format_settings(settings)}\n\n"
            "Select an option below:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Handle size selection
    if action == 'size':
        keyboard = [
            [InlineKeyboardButton("🔲 Square (1024x1024)", callback_data="size_square")],
            [InlineKeyboardButton("📱 Portrait (1024x1792)", callback_data="size_portrait")],
            [InlineKeyboardButton("🖥️ Landscape (1792x1024)", callback_data="size_landscape")],
            [InlineKeyboardButton("◀️ Back", callback_data="settings_back")]
        ]
        await query.edit_message_text(
            "📐 *Select Image Size*\n\n"
            "Choose the dimensions for your generated images:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if action.startswith('size_'):
        size_key = action.split('_')[1]
        if size_key in config.IMAGE_SIZES:
            size_value = config.IMAGE_SIZES[size_key]
            SessionManager.update_setting(user_id, 'size', size_value)
            await query.edit_message_text(
                f"✅ *Size Updated*\n\n"
                f"Image size set to: {size_value}\n"
                "Use `/settings` to customize more options.",
                parse_mode=ParseMode.MARKDOWN
            )
        return
    
    # Handle quality selection
    if action == 'quality':
        keyboard = [
            [InlineKeyboardButton("⭐ Standard (Faster)", callback_data="quality_standard")],
            [InlineKeyboardButton("🌟 HD (Better Quality)", callback_data="quality_hd")],
            [InlineKeyboardButton("◀️ Back", callback_data="settings_back")]
        ]
        await query.edit_message_text(
            "✨ *Select Image Quality*\n\n"
            "• Standard: Faster generation\n"
            "• HD: Higher quality (uses more credits)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if action.startswith('quality_'):
        quality_key = action.split('_')[1]
        if quality_key in config.IMAGE_QUALITY:
            quality_value = config.IMAGE_QUALITY[quality_key]
            SessionManager.update_setting(user_id, 'quality', quality_value)
            await query.edit_message_text(
                f"✅ *Quality Updated*\n\n"
                f"Image quality set to: {quality_value.upper()}\n"
                "Use `/settings` to customize more options.",
                parse_mode=ParseMode.MARKDOWN
            )
        return
    
    # Handle style selection
    if action == 'style':
        keyboard = [
            [InlineKeyboardButton("🎨 Natural", callback_data="style_natural")],
            [InlineKeyboardButton("🖌️ Vivid", callback_data="style_vivid")],
            [InlineKeyboardButton("◀️ Back", callback_data="settings_back")]
        ]
        await query.edit_message_text(
            "🎨 *Select Image Style*\n\n"
            "• Natural: Realistic and natural look\n"
            "• Vivid: More vibrant and artistic",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if action.startswith('style_'):
        style_key = action.split('_')[1]
        if style_key in config.IMAGE_STYLES:
            style_value = config.IMAGE_STYLES[style_key]
            SessionManager.update_setting(user_id, 'style', style_value)
            await query.edit_message_text(
                f"✅ *Style Updated*\n\n"
                f"Image style set to: {style_value.upper()}\n"
                "Use `/settings` to customize more options.",
                parse_mode=ParseMode.MARKDOWN
            )
        return

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error: {context.error}")
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ *Something went wrong*\n\n"
                "Please try again. If the problem continues, contact support.",
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")
