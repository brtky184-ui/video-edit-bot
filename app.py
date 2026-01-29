import gradio as gr
import os, asyncio, threading, subprocess, time, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- AYARLAR ---
TOKEN = "8030105235:AAHCN3kX97OOagbTCVgnIZ1u3JNQB8upayY"
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO)
user_data = {}

# --- BOT FONKSİYONLARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {'video': None, 'audio': None, 'subtitle': None}
    await update.message.reply_text("👋 Selam Şervan! Şimdi her şeyi (Video, Ses, Metin) sırayla gönder. Ne gönderirsen tanıyacağım.")

async def handle_any_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message
    
    # Dosyayı bulma (Video, Ses, Belge fark etmez)
    file_obj = None
    file_name = ""
    
    if msg.video:
        file_obj = await msg.video.get_file()
        file_name = msg.video.file_name or "video.mp4"
    elif msg.audio or msg.voice:
        file_obj = await (msg.audio or msg.voice).get_file()
        file_name = "audio.mp3"
    elif msg.document:
        file_obj = await msg.document.get_file()
        file_name = msg.document.file_name.lower()
    
    if file_obj:
        if user_id not in user_data: user_data[user_id] = {'video': None, 'audio': None, 'subtitle': None}
        
        # Uzantıya göre kaydetme
        path = os.path.join(DOWNLOAD_DIR, f"{user_id}_{int(time.time())}_{file_name}")
        await file_obj.download_to_drive(path)
        
        # Dosyayı tipine göre ayır
        if file_name.endswith(('.mp4', '.mov', '.avi', '.mkv')):
            user_data[user_id]['video'] = path
            await msg.reply_text("✅ Video (MP4) kaydedildi.")
        elif file_name.endswith(('.mp3', '.wav', '.m4a', '.ogg')):
            user_data[user_id]['audio'] = path
            await msg.reply_text("✅ Ses (MP3) kaydedildi.")
        else:
            user_data[user_id]['subtitle'] = path
            await msg.reply_text("✅ Altyazı (SRT/TXT) kaydedildi.")

async def merge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    d = user_data.get(user_id)
    
    if not d or not d['video'] or not d['audio'] or not d['subtitle']:
        await update.message.reply_text("❌ Eksik var! Video, Ses ve Altyazı gönderdiğinden emin ol.")
        return
    
    m = await update.message.reply_text("⏳ Render başladı, bu biraz sürebilir...")
    out = os.path.join(DOWNLOAD_DIR, f"final_{user_id}.mp4")
    
    # FFmpeg - Altyazıyı videonun içine gömme
    cmd = ['ffmpeg', '-y', '-i', d['video'], '-i', d['audio'], '-vf', f"subtitles={d['subtitle']}", '-shortest', out]
    
    try:
        subprocess.run(cmd, check=True)
        await update.message.reply_document(document=open(out, 'rb'), caption="İşlem tamam! 🎉")
    except Exception as e:
        await update.message.reply_text(f"Hata: {e}")

# --- BAŞLATICI ---
def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('birlestir', merge))
    app.add_handler(MessageHandler(filters.ALL, handle_any_file))
    app.run_polling(drop_pending_updates=True)

threading.Thread(target=run_bot, daemon=True).start()
with gr.Blocks() as demo:
    gr.Markdown("# Bot Aktif")
demo.launch(server_name="0.0.0.0", server_port=10000)
