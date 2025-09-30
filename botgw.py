# Store user links with short keys for callback data
from uuid import uuid4
user_links = {}
import subprocess

import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# Command handlers
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text(
		'Yo! Drop me a YouTube, TikTok, or Instagram link, I’ll snag the audio for ya\n'
		'Use /start for a welcome message.'
	)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text(
		'Yo! Drop me a YouTube, TikTok, or Instagram link, I’ll snag the audio for ya'
	)


# Replace with your bot token from BotFather
TELEGRAM_BOT_TOKEN = '8127357501:AAEFiC0ZC9gn1kShMoXOP_aS9dDRr9F_fao'

DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)



# Improved URL extraction: match any URL, then filter for supported sites
def extract_url(text):
	url_pattern = r'(https?://[\w\-\.\?\=\&\/%#]+)'
	urls = re.findall(url_pattern, text)
	for url in urls:
		if any(site in url for site in ['youtube.com', 'youtu.be', 'tiktok.com', 'instagram.com']):
			return url
	return None



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
	text = update.message.text
	url = extract_url(text)
	if not url:
		await update.message.reply_text('Yo! drop me a YouTube, TikTok, or Instagram link, I’ll snag the audio for ya')
		return
	await update.message.reply_text("Snatchin' your damn track, sit yo ass down.")
	try:
		ydl_opts = {
			'format': 'bestaudio/best',
			'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
			'postprocessors': [{
				'key': 'FFmpegExtractAudio',
				'preferredcodec': 'mp3',
				'preferredquality': '192',
			}],
			'concurrent_fragment_downloads': 8,  # Use up to 8 threads for fragments
			'writesubtitles': False,
			'writethumbnail': False,
			'writeinfojson': False,
			'quiet': True,
			'no_warnings': True,
		}
		with yt_dlp.YoutubeDL(ydl_opts) as ydl:
			info = ydl.extract_info(url, download=True)
			filename = ydl.prepare_filename(info)
			file_path = os.path.splitext(filename)[0] + '.mp3'
			title = info.get('title', 'Unknown')
			duration = int(info.get('duration', 0))
			mins, secs = divmod(duration, 60)
			await update.message.reply_text(f"Title: {title}\nDuration: {mins}:{secs:02d}")
			await update.message.reply_audio(audio=open(file_path, 'rb'))
	except Exception as e:
		error_msg = str(e)
		if 'Unable to extract webpage video data' in error_msg and 'TikTok' in error_msg:
			await update.message.reply_text('Sorry, this TikTok video cannot be downloaded right now. TikTok may have changed their site. Try another link or check back later!')
		elif 'Unsupported URL' in error_msg:
			await update.message.reply_text('This link is not supported. Please send a direct video link from YouTube, TikTok, or Instagram.')
		elif 'ffmpeg' in error_msg or 'ffprobe' in error_msg:
			await update.message.reply_text('Audio/video conversion failed. Please make sure FFmpeg is installed and available in your PATH.')
		elif 'Timed out' in error_msg or 'ReadTimeout' in error_msg or 'HTTPSConnectionPool' in error_msg:
			await update.message.reply_text("What the fuck? Download failed. Probably 'cause the file’s too damn big or my internet’s slow as hell. Hold up a sec or try again.")
		else:
			await update.message.reply_text(f'Error: {e}')


def main():
	# Automatically update yt-dlp for latest site support
	try:
		subprocess.run(["python", "-m", "yt_dlp", "-U"], check=True)
	except Exception:
		print("Warning: Could not update yt-dlp automatically.")
	app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
	app.add_handler(CommandHandler('start', start))
	app.add_handler(CommandHandler('help', help_command))
	app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
	print('Bot is running...')
	app.run_polling()


if __name__ == '__main__':
	main()
