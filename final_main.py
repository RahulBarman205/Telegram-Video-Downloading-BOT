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
user_choice = {}


required_channel_usernames = ["chachabbc"]

user_started = {}
user_joined_channels = {}



def check_channel_membership(user_id):
    for channel_username in required_channel_usernames:
        try:
            chat_member = bot.get_chat_member("@" + channel_username, user_id)
            if chat_member.status not in ["member", "administrator"]:
                return False  # User is not a member of at least one required channel
        except telebot.apihelper.ApiException as e:
            print(f"Error checking channel membership: {e}")
    return True  # User is a member of all required channels


@bot.message_handler(commands=['start', 'help'])
def start(message):
    user_id = message.from_user.id
    user_started[user_id] = True

    if check_channel_membership(user_id):  # Check if the user is a member of all required channels
        user_joined_channels[user_id] = True
        bot.reply_to(
            message, "Send me a video or audio link (starts with http or www) and I'll download it for you, works with *YouTube*, *TikTok*, *Reddit* and more.\n\nAuthor: Tech4Sandy", parse_mode="MARKDOWN", disable_web_page_preview=True)
    else:
        missing_channel_usernames = required_channel_usernames.copy()
        for channel_username in required_channel_usernames:
            try:
                chat_member = bot.get_chat_member("@" + channel_username, user_id)
                if chat_member.status in ["member", "administrator"]:
                    missing_channel_usernames.remove(channel_username)
            except telebot.apihelper.ApiException as e:
                print(f"Error checking channel membership: {e}")

        channel_links = [f"https://t.me/{channel}" for channel in missing_channel_usernames]
        channel_links_text = "\n".join(channel_links)
        reply_text = f"You must join the following channels before using other commands:\n\n{channel_links_text}"
        bot.reply_to(message, reply_text, parse_mode="Markdown")


@bot.message_handler(func=lambda message: True)
def restrict_commands(message):
    user_id = message.from_user.id
    user_started.setdefault(user_id, False)

    if user_started[user_id]:
        user_joined_channels[user_id] = check_channel_membership(user_id)

    if not user_joined_channels.get(user_id):
        bot.reply_to(message, "You must join the required channels before using other commands. Please enter '/start' again")
    else:
        text = message.text.lower()
        if text.startswith("/download"):
            if user_choice.get(user_id) == "audio":
                download_audio_command(message)
            else:
                download_command(message)
        elif text.startswith("/audio"):
            user_choice[user_id] = "audio"
            download_audio_command(message)
        elif text.startswith("/custom"):
            custom(message)
        elif text.startswith("http") or text.startswith("www"):
            if youtube_url_validation(text):
                ask_media_format(message)
            else:
                download_command(message)
        else:
            bot.reply_to(message, "Invalid Command, Please Enter a Valid URL")


@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_youtube_links(message):
    text = message.text.lower()
    user_id = message.from_user.id

    
    if youtube_url_validation(text):
        
        ask_media_format(message)
    else:
       
        user_choice[user_id] = "video"
        download_command(message)


def ask_media_format(message):
    user_id = message.from_user.id
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton("Video", callback_data="mp4"))
    markup.row(telebot.types.InlineKeyboardButton("Audio", callback_data="mp3"))

    bot.reply_to(message, "Which media format would you like to download?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.from_user.id == call.message.reply_to_message.from_user.id:
        url = get_text(call.message.reply_to_message)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        download_format = call.data
        if download_format == "mp4":
            download_command(call.message.reply_to_message)
        elif download_format == "mp3":
            download_audio_command(call.message.reply_to_message)
    else:
        bot.answer_callback_query(call.id, "You didn't send the request")



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
        message, "Send me a video or audio link (starts with http or www) and I'll download it for you, works with *YouTube*, *TikTok*, *Reddit* and more.\n\nAuthor: Tech4Sandy", parse_mode="MARKDOWN", disable_web_page_preview=True)


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
    text = message.text if message.text else message.caption if message.caption else None
    if not text and message.reply_to_message:
        text = message.reply_to_message.text if message.reply_to_message.text else message.reply_to_message.caption
    return text



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

