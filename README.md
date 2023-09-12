# YT-DLP Telegram Bot
Telegram bot that allows you to download videos from YouTube, Twitter, Reddit and many other socials using [yt-dlp](https://github.com/yt-dlp/yt-dlp) 

## Usage
In the bot private chat just use `/download <url>`

## Self hosting
```bash
https://github.com/RahulBarman205/Telegram-Video-Downloading-BOT.git
cd Telegram-Video-Downloading-BOT
pip install -r requirements.txt
```
create a `config.py` file and set the `token` variable to your bot token (check `example.config.py`)
```py
python temp_main.py
```

**The Telegram API limits files sent by bots to 50mb**

**https://core.telegram.org/bots/faq#how-do-i-upload-a-large-file**
