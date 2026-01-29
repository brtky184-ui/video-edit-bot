import gradio as gr
import os
import asyncio
import threading
import subprocess
import time
import socket
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
# --- DNS BYPASS ---
def bypass_dns():
    import socket
    telegram_ip = "149.154.167.220"
    def getaddrinfo_override(*args, **kwargs):
        if args[0] == 'api.telegram.org':
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (telegram_ip, 443))]
        return socket.getaddrinfo_original(*args, **kwargs)
    if not hasattr(socket, 'getaddrinfo_original'):
        socket.getaddrinfo_original = socket.getaddrinfo
        socket.getaddrinfo = getaddrinfo_override
bypass_dns()
# --- AYARLAR ---
TOKEN = "8030105235:AAHCN3kX97OOagbTCVgnIZ1u3JNQB8upayY"
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
user_data = {}

# --- BOT FONKSİYONLARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Selam Şervan! @videoedit1_bot sonunda bağlandı. Dosyaları gönder, /birlestir de.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message
    file_obj = await (msg.video or msg.audio or msg.voice or msg.document).get_file()
    
    if user_id not in user_data: user_data[user_id] = {'video': None, 'audio': None, 'subtitle': None}
    
    ext = "mp4" if msg.video else ("mp3" if (msg.audio or msg.voice) else "srt")
    path = os.path.join(DOWNLOAD_DIR, f"{user_id}_{int(time.time())}.{ext}")
    await file_obj.download_to_drive(path)
    
    if msg.video: user_data[user_id]['video'] = path
    elif msg.audio or msg.voice: user_data[user_id]['audio'] = path
    else: user_data[user_id]['subtitle'] = path
    await msg.reply_text(f"✅ {ext.upper()} alındı.")

async def merge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    d = user_data.get(user_id)
    if not d or not all(d.values()):
        await update.message.reply_text("❌ Dosyalar eksik!")
        return
    
    out = os.path.join(DOWNLOAD_DIR, f"out_{user_id}.mp4")
    cmd = ['ffmpeg', '-y', '-i', d['video'], '-i', d['audio'], '-vf', f"subtitles={d['subtitle']}", '-shortest', out]
    
    try:
        subprocess.run(cmd, check=True)
        await update.message.reply_document(document=open(out, 'rb'), caption="İşlem tamam! 🎉")
    except Exception as e:
        await update.message.reply_text(f"Hata: {e}")

# --- İNTERNETİ ZORLAYAN BAŞLATICI ---
def run_bot_forever():
    while True:
        try:
            # DNS'i zorla dürtüyoruz
            socket.getaddrinfo('api.telegram.org', 443)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            app = ApplicationBuilder().token(TOKEN).build()
            app.add_handler(CommandHandler('start', start))
            app.add_handler(CommandHandler('birlestir', merge))
            app.add_handler(MessageHandler(filters.ALL, handle_document))
            
            print("🚀 Bot başarıyla bağlandı!")
            app.run_polling(stop_signals=None)
        except Exception as e:
            print(f"⚠️ Bağlantı bekliyor (DNS hatası olabilir)... Tekrar deniyor: {e}")
            time.sleep(10) # 10 saniye bekle ve tekrar dene

threading.Thread(target=run_bot_forever, daemon=True).start()

# --- GRADIO VİTRİNİ ---
with gr.Blocks() as demo:
    gr.Markdown("# 🤖 @videoedit1_bot Aktif\nLogları takip et, 'Başarıyla bağlandı' yazısını görünce Telegram'a geç.")
demo.launch()
