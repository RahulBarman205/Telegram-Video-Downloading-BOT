def join_channel():
    import logging
    import sys
    import threading
    from telegram import Update
    from telegram.ext import Updater, CommandHandler, CallbackContext
    from telegram.error import BadRequest

    # Enable logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # Your bot token
    BOT_TOKEN = '6565741324:AAHn4lF4Ysx9AJYI2yfIscWhshzeov7DMZY'

    # List of channels that users need to join
    REQUIRED_CHANNELS = ['@giginigi', '@uwusenpai1234']  # Replace with your channel usernames

    # Event to signal the main thread to exit
    exit_event = threading.Event()

    # Dictionary to track whether the user has joined each channel
    user_joined_channels = {}

    def check_channels(updater: Updater, user_id: int):
        user_channels = []
        for channel_username in REQUIRED_CHANNELS:
            try:
                channel_member = updater.bot.get_chat_member(chat_id=channel_username, user_id=user_id)
                if channel_member.status == "member":
                    user_channels.append(channel_username)
            except BadRequest as e:
                # Handle user not found or other errors gracefully
                logging.warning(f"Error checking membership for user {user_id} in channel {channel_username}: {e}")

        return user_channels

    def bot_thread():
        # Initialize the bot
        updater = Updater(token=BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher

        def start(update: Update, context: CallbackContext):
            user = update.effective_user
            user_id = user.id

            if user_id not in user_joined_channels:
                user_joined_channels[user_id] = []

            joined_channels = check_channels(updater, user_id)

            if len(joined_channels) == len(REQUIRED_CHANNELS):
                update.message.reply_text(f"Welcome, {user.first_name}! You are a member of all required channels.")
                exit_event.set()  # Signal to exit the thread
            else:
                missing_channels = list(set(REQUIRED_CHANNELS) - set(joined_channels))
                update.message.reply_text(f"Hello, {user.first_name}! Please join the following channels: {', '.join(missing_channels)}.")

        # Register the /start command handler
        dispatcher.add_handler(CommandHandler('start', start))

        # Start the bot
        updater.start_polling()

        # Block until the event is set
        exit_event.wait()

        # Stop the updater
        updater.stop()

    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=bot_thread)
    bot_thread.start()

    # Main thread will continue running other tasks
    while not exit_event.is_set():
        pass
