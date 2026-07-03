import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from config import config
from handlers import (
    start_command,
    help_command,
    about_command,
    generate_command,
    settings_command,
    settings_callback,
    error_handler
)

logger = logging.getLogger(__name__)

def main():
    """Main bot entry point"""
    try:
        # Get bot token
        token = config.get_telegram_token()
        
        # Build application with production settings
        app = (
            ApplicationBuilder()
            .token(token)
            .concurrent_updates(True)
            .build()
        )
        
        # Register command handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("about", about_command))
        app.add_handler(CommandHandler("generate", generate_command))
        app.add_handler(CommandHandler("imagine", generate_command))
        app.add_handler(CommandHandler("settings", settings_command))
        
        # Register callback query handlers
        app.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings_"))
        app.add_handler(CallbackQueryHandler(settings_callback, pattern="^size_"))
        app.add_handler(CallbackQueryHandler(settings_callback, pattern="^quality_"))
        app.add_handler(CallbackQueryHandler(settings_callback, pattern="^style_"))
        
        # Register error handler
        app.add_error_handler(error_handler)
        
        # Start bot
        logger.info("🚀 ArttForgeBot is starting...")
        logger.info(f"Environment: {'Production' if config.is_production() else 'Development'}")
        
        # Run with webhook in production, polling in development
        if config.is_production():
            port = config.get_port()
            logger.info(f"Starting webhook on port {port}")
            app.run_webhook(
                listen="0.0.0.0",
                port=port,
                webhook_url=None  # Railway handles this
            )
        else:
            logger.info("Starting polling mode...")
            app.run_polling(drop_pending_updates=True)
            
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
