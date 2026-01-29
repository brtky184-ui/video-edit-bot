import os, subprocess, time, threading, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Ayarlar
TOKEN = "8030105235:AAHCN3kX97OOagbTCVgnIZ1u3JNQB8upayY"
user_files = {}

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user_files[u.effective_user.id] = {}
    await u.message.reply_text("👋 Selam Şervan! Videoyu, sesi ve altyazıyı gönder, sonra /birlestir yaz.")

async def catch(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if uid not in user_files: user_files[uid] = {}
    
    msg = u.message
    f = await (msg.video or msg.audio or msg.voice or msg.document).get_file()
    ext = f.file_path.split('.')[-1].lower()
    path = f"{uid}_{int(time.time())}.{ext}"
    await f.download_to_drive(path)

    # Dosya türünü belirle
    if ext in ['mp4', 'mov', 'avi']: user_files[uid]['v'] = path
    elif ext in ['mp3', 'wav', 'm4a']: user_files[uid]['a'] = path
    else: user_files[uid]['s'] = path
    await u.message.reply_text(f"✅ {ext.upper()} kaydedildi.")

async def merge(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    d = user_files.get(uid, {})
    if not all(k in d for k in ['v', 'a', 's']):
        await u.message.reply_text("❌ Eksik dosya var!")
        return

    await u.message.reply_text("⏳ İşleniyor...")
    out = f"final_{uid}.mp4"
    # Altyazıyı gömme komutu
    cmd = ['ffmpeg', '-y', '-i', d['v'], '-i', d['a'], '-vf', f"subtitles={d['s']}", '-shortest', out]
    
    try:
        subprocess.run(cmd, check=True)
        await u.message.reply_document(document=open(out, 'rb'))
    except Exception as e:
        await u.message.reply_text(f"Hata: {e}")

def run():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("birlestir", merge))
    app.add_handler(MessageHandler(filters.ALL, catch))
    app.run_polling(drop_pending_updates=True)

threading.Thread(target=run, daemon=True).start()
# Render'ın kapanmaması için çok basit bir server
import gradio as gr
with gr.Blocks() as d: gr.Markdown("Aktif")
d.launch(server_name="0.0.0.0", server_port=10000)
