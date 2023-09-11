
def join_channel():

    from telegram import Update
    from telegram.ext import Updater, CommandHandler, CallbackContext

    # Enable logging
    

    # Your bot token
    BOT_TOKEN = '6565741324:AAHn4lF4Ysx9AJYI2yfIscWhshzeov7DMZY'

    # List of channels that users need to join
    REQUIRED_CHANNELS = ['@giginigi', '@uwusenpai1234']  # Replace with your channel usernames

    # Initialize the bot
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    def start(update: Update, context: CallbackContext):
        user = update.effective_user

        # Check if the user is a member of all required channels
        user_channels = update.effective_chat.get_member(user.id)
        for channel_username in REQUIRED_CHANNELS:
            channel_member = context.bot.get_chat_member(chat_id=channel_username, user_id=user.id)
            if channel_member.status != "member":
                user_channels = None
                break

        if user_channels and user_channels.status == "member":
            update.message.reply_text(f"Welcome, {user.first_name}! You are a member of all required channels.")
            print("Updater Terminated")
            updater.stop()
            return "Done"
            

        else:
            update.message.reply_text(f"Hello, {user.first_name}! Please join the required channels to use this bot.")

    # Register the /start command handler
    dispatcher.add_handler(CommandHandler('start', start))

    # Start the bot
    updater.start_polling()
    updater.idle()

join_channel()
