from urllib.parse import urlparse
import datetime
import telebot
import config
import yt_dlp
import re
import os
import telebot
from telebot.util import quick_markup

bot = telebot.TeleBot(config.token)
last_edited = {}


# Define the channel usernames that users must join
required_channel_usernames = ["testblack12", "kysblack"]
# Create dictionaries to track user status
user_started = {}
user_joined_channels = {}

# Helper function to check if the user is a member of the required channels
def check_channel_membership(user_id):
    missing_channel_usernames = []

    for channel_username in required_channel_usernames:
        try:
            chat_member = bot.get_chat_member("@" + channel_username, user_id)
            if chat_member.status not in ["member", "administrator"]:
                missing_channel_usernames.append("@" + channel_username)
        except telebot.apihelper.ApiException as e:
            print(f"Error checking channel membership: {e}")
            # Handle the error gracefully (e.g., log it) without raising an exception

    return missing_channel_usernames

# Command handler for "/start" command
@bot.message_handler(commands=['start', 'help'])
def start(message):
    user_id = message.from_user.id
    user_started[user_id] = True

    missing_channel_usernames = check_channel_membership(user_id)

    if not missing_channel_usernames:
        user_joined_channels[user_id] = True
        bot.reply_to(
            message, "*Send me a video link (starts with https) with '/download' command* and I'll download it for you, works with *YouTube*, *TikTok*, *Reddit* and more.\n\nAuthor: Tech4Sandy", parse_mode="MARKDOWN", disable_web_page_preview=True)
    else:
        bot.reply_to(
    message, "You must join the following channels before using other commands:\n\n" + '\n'.join(missing_channel_usernames)
)


# Restrict users from using other commands if they haven't run /start or joined channels
@bot.message_handler(func=lambda message: True)
def restrict_commands(message):
    user_id = message.from_user.id
    if not user_started.get(user_id) or not user_joined_channels.get(user_id):
        bot.reply_to(message, "You must run the `/start` command and join the required channels before using other commands.")
    else:
        # Handle other commands as usual
        text = message.text.lower()
        if text.startswith("/download"):
            download_command(message)
        elif text.startswith("/audio"):
            download_audio_command(message)
        elif text.startswith("/custom"):
            custom(message)
        # Add other command handlers as needed


def youtube_url_validation(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')

    youtube_regex_match = re.match(youtube_regex, url)
    if youtube_regex_match:
        return youtube_regex_match

    return youtube_regex_match


@bot.message_handler(commands=['help'])
def test(message):
    bot.reply_to(
        message, "*Send me a video link* and I'll download it for you, works with *YouTube*, *Twitter*, *TikTok*, *Reddit* and more.\n\n_Powered by_ [yt-dlp](https://github.com/yt-dlp/yt-dlp/)", parse_mode="MARKDOWN", disable_web_page_preview=True)


def download_video(message, url, audio=False, format_id="mp4"):
    url_info = urlparse(url)
    if url_info.scheme:
        if url_info.netloc in ['www.youtube.com', 'youtu.be', 'youtube.com', 'youtu.be']:
            if not youtube_url_validation(url):
                bot.reply_to(message, 'Invalid URL')
                return

        def progress(d):

            if d['status'] == 'downloading':
                try:
                    update = False

                    if last_edited.get(f"{message.chat.id}-{msg.message_id}"):
                        if (datetime.datetime.now() - last_edited[f"{message.chat.id}-{msg.message_id}"]).total_seconds() >= 5:
                            update = True
                    else:
                        update = True

                    if update:
                        perc = round(d['downloaded_bytes'] *
                                     100 / d['total_bytes'])
                        bot.edit_message_text(
                            chat_id=message.chat.id, message_id=msg.message_id, text=f"Downloading {d['info_dict']['title']}\n\n{perc}%")
                        last_edited[f"{message.chat.id}-{msg.message_id}"] = datetime.datetime.now()
                except Exception as e:
                    print(e)

        msg = bot.reply_to(message, 'Downloading...')
        with yt_dlp.YoutubeDL({'cookiefile': 'cookies.txt', 'format': format_id, 'outtmpl': 'outputs/%(title)s.%(ext)s', 'progress_hooks': [progress], 'postprocessors': [{  # Extract audio using ffmpeg
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }] if audio else [], 'max_filesize': config.max_filesize}) as ydl:
            try:
                info = ydl.extract_info(url, download=True)

                bot.edit_message_text(
                    chat_id=message.chat.id, message_id=msg.message_id, text='Sending file to Telegram...')
                try:
                    if audio:
                        bot.send_audio(message.chat.id, open(
                            info['requested_downloads'][0]['filepath'], 'rb'), reply_to_message_id=message.message_id)

                    else:
                        bot.send_video(message.chat.id, open(
                            info['requested_downloads'][0]['filepath'], 'rb'), reply_to_message_id=message.message_id)
                    bot.delete_message(message.chat.id, msg.message_id)
                except Exception as e:
                    bot.edit_message_text(
                        chat_id=message.chat.id, message_id=msg.message_id, text=f"Couldn't send file, make sure it's supported by Telegram and it doesn't exceed *{round(config.max_filesize / 1000000)}MB*", parse_mode="MARKDOWN")
                    for file in info['requested_downloads']:
                        os.remove(file['filepath'])
                else:
                    for file in info['requested_downloads']:
                        os.remove(file['filepath'])
            except Exception as e:
                if isinstance(e, yt_dlp.utils.DownloadError):
                    bot.edit_message_text(
                        'Invalid URL', message.chat.id, msg.message_id)
                else:
                    bot.edit_message_text(
                        'There was an error downloading your video', message.chat.id, msg.message_id)
    else:
        bot.reply_to(message, 'Invalid URL')


def log(message, text: str, media: str):
    if config.logs:
        if message.chat.type == 'private':
            chat_info = "Private chat"
        else:
            chat_info = f"Group: *{message.chat.title}* (`{message.chat.id}`)"

        bot.send_message(
            config.logs, f"Download request ({media}) from @{message.from_user.username} ({message.from_user.id})\n\n{chat_info}\n\n{text}")


def get_text(message):
    if len(message.text.split(' ')) < 2:
        if message.reply_to_message and message.reply_to_message.text:
            return message.reply_to_message.text

        else:
            return None
    else:
        return message.text.split(' ')[1]


@bot.message_handler(commands=['download'])
def download_command(message):
    text = get_text(message)
    if not text:
        bot.reply_to(
            message, 'Invalid usage, use `/download url`', parse_mode="MARKDOWN")
        return

    log(message, text, 'video')
    download_video(message, text)


@bot.message_handler(commands=['audio'])
def download_audio_command(message):
    text = get_text(message)
    if not text:
        bot.reply_to(
            message, 'Invalid usage, use `/audio url`', parse_mode="MARKDOWN")
        return

    log(message, text, 'audio')
    download_video(message, text, True)


@bot.message_handler(commands=['custom'])
def custom(message):
    text = get_text(message)
    if not text:
        bot.reply_to(
            message, 'Invalid usage, use `/custom url`', parse_mode="MARKDOWN")
        return

    msg = bot.reply_to(message, 'Getting formats...')

    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(text, download=False)

    data = {f"{x['resolution']}.{x['ext']}": {
        'callback_data': f"{x['format_id']}"} for x in info['formats'] if x['video_ext'] != 'none'}

    markup = quick_markup(data, row_width=2)

    bot.delete_message(msg.chat.id, msg.message_id)
    bot.reply_to(message, "Choose a format", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.from_user.id == call.message.reply_to_message.from_user.id:
        url = get_text(call.message.reply_to_message)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        download_video(call.message.reply_to_message, url,
                       format_id=f"{call.data}+bestaudio")
    else:
        bot.answer_callback_query(call.id, "You didn't send the request")


@bot.message_handler(func=lambda m: True, content_types=["text", "pinned_message", "photo", "audio", "video", "location", "contact", "voice", "document"])
def handle_private_messages(message):
    text = message.text if message.text else message.caption if message.caption else None

    if message.chat.type == 'private':
        log(message, text, 'video')
        download_video(message, text)
        return


bot.infinity_polling()
