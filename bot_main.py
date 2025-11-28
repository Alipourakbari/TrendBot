import os
import random
from telegram import Update
from telegram.ext import Updater, CommandHandler, ContextTypes # تغییر: استفاده از Updater
import logging
import instaloader

# تنظیمات لاگ (گزارش‌ها)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- متغیرهای محیطی ضروری ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
PORT = int(os.environ.get('PORT', 5000)) 
WEBHOOK_URL = os.environ.get('WEBHOOK_URL') 

# ----------------------------------------

class RealVideoTrendBot:
    """کلاس اصلی برای مدیریت منطق جستجوی ویدیوهای ترند"""
    def __init__(self):
        try:
            self.L = instaloader.Instaloader(
                sleep=True, 
                max_connection_attempts=2,
                request_timeout=60,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            logger.info("✅ Instaloader initialized successfully")
        except Exception as e:
            logger.error(f"❌ Error initializing instaloader: {e}. Using fallback data.")
            self.L = None
    
    def search_trending_videos(self, hashtag, count=10):
        """جستجوی ویدیوهای ترند بر اساس هشتگ"""
        if not self.L:
            return self.get_fallback_videos(hashtag, count)
            
        try:
            logger.info(f"🔍 Searching for videos with #{hashtag}")
            posts = []
            hashtag_obj = instaloader.Hashtag.from_name(self.L.context, hashtag)
            
            for i, post in enumerate(hashtag_obj.get_posts()):
                if len(posts) >= count:
                    break
                
                # فیلتر کردن بر اساس ویدیو بودن و لایک بالا
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
                    
                    logger.info(f"✅ Found video from @{post.owner_username} with {post.likes} likes")
            
            posts.sort(key=lambda x: x['engagement'], reverse=True)
            return posts
            
        except Exception as e:
            logger.error(f"❌ Error searching #{hashtag}: {e}")
            return self.get_fallback_videos(hashtag, count)
    
    def get_trending_from_hashtags(self, hashtags, count=8):
        """دریافت ویدیوهای ترند از چند هشتگ برای دسته‌بندی‌های ثابت"""
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
        """داده‌های جایگزین (Sample Data)"""
        logger.info(f"📊 Using fallback data for {category}")
        
        fallback_data = {
            "viral": [
                { 'url': 'https://www.instagram.com/p/C1abc123/fallback', 'caption': 'ویدیو ویرال جهانی 🌍', 'likes': random.randint(50000, 500000), 'comments': random.randint(1000, 20000), 'views': random.randint(100000, 1000000), 'owner': 'viral_creator', 'engagement': random.randint(100000, 1000000), 'hashtag': 'viral' }
            ],
            "kpop": [
                { 'url': 'https://www.instagram.com/p/C2def456/fallback', 'caption': 'راکستان بلک‌پینک 💃', 'likes': random.randint(100000, 2000000), 'comments': random.randint(5000, 50000), 'views': random.randint(500000, 5000000), 'owner': 'kpop_news', 'engagement': random.randint(200000, 4000000), 'hashtag': 'kpop' }
            ]
        }
        
        category_data = fallback_data.get(category, fallback_data["viral"])
        return random.sample(category_data, min(count, len(category_data)))

video_bot = RealVideoTrendBot()

# دسته‌بندی‌های ترند
TREND_CATEGORIES = {
    "global": ["viral", "trending", "fyp", "explorepage", "popular"],
    "kpop": ["kpop", "kpopdance", "kpopedit", "blackpink", "bts"],
    "memes": ["memes", "funny", "comedy", "viralvideos", "dankmemes"],
    "dance": ["dance", "dancechallenge", "dancevideo", "trendingdance"],
    "music": ["music", "song", "artist", "newmusic", "livemusic"]
}

# --- توابع هندل‌کننده تلگرام ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ به دستور /start"""
    welcome_text = """
🤖 **Real Video Trend Bot**

🎯 **این ربات ویدیوهای واقعی ترند اینستاگرام را بر اساس شاخص Engagement (لایک + کامنت) پیدا می‌کند.**

🔍 **دستورات اصلی:**
/videos_global - ویدیوهای ترند جهانی
/videos_kpop - ویدیوهای ترند کی-پاپ
/videos_memes - ویدیوهای ممز ترند
/videos_dance - ویدیوهای دنس ترند
/videos_music - ویدیوهای موزیک ترند

🔎 **جستجو سفارشی:**
/search [هشتگ] - جستجو در هشتگ خاص (مثال: `/search catvideos`)
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def videos_global_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 درحال جستجوی ویدیوهای ترند جهانی...")
    videos = video_bot.get_trending_from_hashtags(TREND_CATEGORIES["global"], 6)
    await send_videos_message(update, videos, "🌍 ویدیوهای ترند جهانی")

async def videos_kpop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 درحال جستجوی ویدیوهای ترند کی-پاپ...")
    videos = video_bot.get_trending_from_hashtags(TREND_CATEGORIES["kpop"], 6)
    await send_videos_message(update, videos, "🎵 ویدیوهای ترند کی-پاپ")

async def videos_memes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤪 درحال جستجوی ویدیوهای ممز ترند...")
    videos = video_bot.get_trending_from_hashtags(TREND_CATEGORIES["memes"], 6)
    await send_videos_message(update, videos, "🤪 ویدیوهای ممز ترند")
    
async def videos_dance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💃 درحال جستجوی ویدیوهای دنس ترند...")
    videos = video_bot.get_trending_from_hashtags(TREND_CATEGORIES["dance"], 6)
    await send_videos_message(update, videos, "💃 ویدیوهای دنس ترند")

async def videos_music_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 درحال جستجوی ویدیوهای موزیک ترند...")
    videos = video_bot.get_trending_from_hashtags(TREND_CATEGORIES["music"], 6)
    await send_videos_message(update, videos, "🎵 ویدیوهای موزیک ترند")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ به دستور /search [هشتگ]"""
    if not context.args:
        await update.message.reply_text("⚠️ لطفاً هشتگ رو وارد کن:\n/search kpop")
        return
    
    hashtag = context.args[0]
    await update.message.reply_text(f"🔍 درحال جستجو در #{hashtag}...")
    
    videos = video_bot.search_trending_videos(hashtag, 8)
    
    await send_videos_message(update, videos, f"🔍 نتایج جستجو #{hashtag}")

async def send_videos_message(update, videos, title):
    """فرمت‌دهی و ارسال لیست ویدیوها با Markdown"""
    if not videos:
        await update.message.reply_text("❌ هیچ ویدیوی ترندی پیدا نشد! یک هشتگ دیگر را امتحان کنید.")
        return
    
    message = f"**{title}**:\n\n"
    
    for i, video in enumerate(videos, 1):
        message += f"{i}. 🎥 **@{video['owner']}**\n"
        message += f"   📝 {video['caption']}\n"
        message += f"   👁️ {video['views']:,} views\n"
        message += f"   ❤️ {video['likes']:,} | 💬 {video['comments']:,}\n"
        message += f"   🔥 Engagement: {video['engagement']:,}\n"
        message += f"   🔗 [لینک پست]({video['url']})\n\n"
    
    # اگر از داده‌های نمونه استفاده شده باشد
    if any('fallback' in str(video.get('url', '')) for video in videos):
        message += "💡 نمایش داده‌های نمونه (اتصال به اینستاگرام برقرار نشد)"
    else:
        message += "✅ داده‌های واقعی از اینستاگرام"
    
    await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)

def main():
    """تابع اصلی اجرای ربات (با استفاده از Updater/Dispatcher)"""
    try:
        print("🚀 Starting Real Video Trend Bot...")
        
        if not TELEGRAM_TOKEN:
            logger.error("❌ TELEGRAM_TOKEN environment variable not found! Bot cannot start.")
            return

        # 1. ساخت نمونه Updater
        updater = Updater(TELEGRAM_TOKEN)
        # 2. دسترسی به Dispatcher
        dispatcher = updater.dispatcher
        
        # ثبت تمام دستورات در Dispatcher
        dispatcher.add_handler(CommandHandler("start", start_command))
        dispatcher.add_handler(CommandHandler("videos_global", videos_global_command))
        dispatcher.add_handler(CommandHandler("videos_kpop", videos_kpop_command))
        dispatcher.add_handler(CommandHandler("videos_memes", videos_memes_command))
        dispatcher.add_handler(CommandHandler("videos_dance", videos_dance_command))
        dispatcher.add_handler(CommandHandler("videos_music", videos_music_command))
        dispatcher.add_handler(CommandHandler("search", search_command))
        
        if WEBHOOK_URL:
            # حالت Webhook: برای اجرا در سرویس‌های ابری مثل Railway
            full_webhook_url = f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
            print(f"✅ Running in WEBHOOK mode on port {PORT}. URL: {full_webhook_url}")
            
            # اجرای Webhook برای دریافت پیام‌ها
            updater.start_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=TELEGRAM_TOKEN,
                webhook_url=full_webhook_url
            )
            # این خط تا زمانی که Railway ربات را فعال نگه دارد، اجرا می‌شود
            updater.idle()
        else:
            # حالت Polling: اگر WEBHOOK_URL تنظیم نشود
            print("⚠️ WEBHOOK_URL environment variable not set. Running in Polling mode (Local Test).")
            updater.start_polling()
            updater.idle()
            
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")

if __name__ == "__main__":
    main()
