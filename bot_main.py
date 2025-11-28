import os
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import instaloader

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# متغیرهای محیطی
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
PORT = int(os.environ.get('PORT', 5000))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

class RealVideoTrendBot:
    def __init__(self):
        try:
            self.L = instaloader.Instaloader(
                sleep=True,
                max_connection_attempts=2,
                request_timeout=60,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            logger.info("✅ Instaloader initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing instaloader: {e}")
            self.L = None

    def search_trending_videos(self, hashtag, count=10):
        if not self.L:
            return self.get_fallback_videos(hashtag, count)

        try:
            logger.info(f"🔍 Searching for videos with #{hashtag}")
            posts = []
            hashtag_obj = instaloader.Hashtag.from_name(self.L.context, hashtag)

            for i, post in enumerate(hashtag_obj.get_posts()):
                if len(posts) >= count:
                    break

                if (post.is_video and
                    post.likes and post.likes > 1000 and
                    (post.video_url or post.url)):

                    caption = post.caption
                    if caption and len(caption) > 120:
                        caption = caption[:120] + "..."

                    posts.append({
                        'url': f"https://www.instagram.com/p/{post.shortcode}/",
                        'video_url': post.video_url,
                        'caption': caption or f"ویدیو ترند #{hashtag}",
                        'likes': post.likes or 0,
                        'comments': post.comments or 0,
                        'views': post.video_view_count or 0,
                        'owner': post.owner_username or "unknown",
                        'engagement': (post.likes or 0) + ((post.comments or 0) * 2),
                        'hashtag': hashtag
                    })

            posts.sort(key=lambda x: x['engagement'], reverse=True)
            return posts

        except Exception as e:
            logger.error(f"❌ Error searching #{hashtag}: {e}")
            return self.get_fallback_videos(hashtag, count)

    def get_trending_from_hashtags(self, hashtags, count=8):
        all_videos = []
        for hashtag in hashtags:
            videos = self.search_trending_videos(hashtag, 3)
            if videos:
                all_videos.extend(videos)
            if len(all_videos) >= count:
                break

        unique_videos = []
        seen_urls = set()
        for video in all_videos:
            if video['url'] not in seen_urls:
                unique_videos.append(video)
                seen_urls.add(video['url'])

        unique_videos.sort(key=lambda x: x['engagement'], reverse=True)
        return unique_videos[:count]

    def get_fallback_videos(self, category, count):
        logger.info(f"📊 Using fallback data for {category}")
        fallback_data = {
            "global": [{'url': 'https://www.instagram.com/p/C1abc123/', 'caption': 'ویدیو نمونه', 'likes': 50000, 'comments': 1000, 'views': 100000, 'owner': 'viral_creator', 'engagement': 52000, 'hashtag': 'viral'}]
        }
        category_data = fallback_data.get(category, fallback_data["global"])
        return category_data

video_bot = RealVideoTrendBot()

TREND_CATEGORIES = {
    "global": ["viral", "trending", "fyp"],
    "kpop": ["kpop", "blackpink", "bts"],
    "memes": ["memes", "funny", "dankmemes"],
    "dance": ["dance", "dancechallenge"],
    "music": ["music", "newmusic"]
}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🤖 **Real Video Trend Bot**
برای دریافت ویدیوها از دستورات زیر استفاده کنید:
/videos_global
/videos_kpop
/videos_memes
/search [هشتگ]
    """
    await update.message.reply_text(welcome_text)

async def videos_global_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 درحال جستجو...")
    videos = video_bot.get_trending_from_hashtags(TREND_CATEGORIES["global"], 6)
    await send_videos_message(update, videos, "🌍 Global Trends")

async def videos_kpop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 درحال جستجو...")
    videos = video_bot.get_trending_from_hashtags(TREND_CATEGORIES["kpop"], 6)
    await send_videos_message(update, videos, "🎵 K-Pop Trends")

async def videos_memes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤪 درحال جستجو...")
    videos = video_bot.get_trending_from_hashtags(TREND_CATEGORIES["memes"], 6)
    await send_videos_message(update, videos, "🤪 Meme Trends")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("لطفا هشتگ را وارد کنید: /search cat")
        return
    hashtag = context.args[0]
    await update.message.reply_text(f"🔍 جستجو در #{hashtag}...")
    videos = video_bot.search_trending_videos(hashtag, 8)
    await send_videos_message(update, videos, f"نتایج #{hashtag}")

async def send_videos_message(update, videos, title):
    if not videos:
        await update.message.reply_text("ویدیو پیدا نشد.")
        return
    
    message = f"**{title}**:\n\n"
    for i, video in enumerate(videos, 1):
        message += f"{i}. 🎥 @{video['owner']}\n"
        message += f"📝 {video['caption']}\n"
        message += f"🔗 {video['url']}\n\n"
        
    await update.message.reply_text(message)

def main():
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not set")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("videos_global", videos_global_command))
    application.add_handler(CommandHandler("videos_kpop", videos_kpop_command))
    application.add_handler(CommandHandler("videos_memes", videos_memes_command))
    application.add_handler(CommandHandler("search", search_command))

    if WEBHOOK_URL:
        full_webhook_url = f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
        print(f"Starting Webhook: {full_webhook_url}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_TOKEN,
            webhook_url=full_webhook_url
        )
    else:
        print("Starting Polling...")
        application.run_polling()

if __name__ == "__main__":
    main()
