import os, subprocess, time, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Ayarlar
TOKEN = "8030105235:AAHCN3kX97OOagbTCVgnIZ1u3JNQB8upayY"
user_files = {}

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user_files[u.effective_user.id] = {}
    await u.message.reply_text("👋 Selam Şervan! Sonunda buradayım. Videoyu, sesi ve metni gönder, sonra /birlestir yaz.")

async def catch(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if uid not in user_files: user_files[uid] = {}
    
    msg = u.message
    # Gelen ne olursa olsun (video, ses, döküman) yakala
    file = (msg.video or msg.audio or msg.voice or msg.document)
    if not file: return
    
    f_obj = await file.get_file()
    ext = f_obj.file_path.split('.')[-1].lower()
    path = f"{uid}_{int(time.time())}.{ext}"
    await f_obj.download_to_drive(path)

    # Dosya türünü isminden anla
    if ext in ['mp4', 'mov', 'avi', 'mkv']: user_files[uid]['v'] = path
    elif ext in ['mp3', 'wav', 'm4a', 'ogg']: user_files[uid]['a'] = path
    else: user_files[uid]['s'] = path
    await u.message.reply_text(f"✅ {ext.upper()} kaydedildi.")

async def merge(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    d = user_files.get(uid, {})
    if not all(k in d for k in ['v', 'a', 's']):
        await u.message.reply_text("❌ Dosyalar eksik! Video, Ses ve Altyazı gönderdiğinden emin ol.")
        return

    m = await u.message.reply_text("⏳ İşlem başladı, 1-2 dakika sürebilir...")
    out = f"final_{uid}.mp4"
    # FFmpeg komutu
    cmd = ['ffmpeg', '-y', '-i', d['v'], '-i', d['a'], '-vf', f"subtitles={d['s']}", '-shortest', out]
    
    try:
        subprocess.run(cmd, check=True)
        await u.message.reply_document(document=open(out, 'rb'), caption="İşlem tamam! 🎉")
    except Exception as e:
        await u.message.reply_text(f"Hata oluştu: {e}")

if __name__ == '__main__':
    # Render'da sinyal hatalarını önlemek için stop_signals=None ekledik
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("birlestir", merge))
    app.add_handler(MessageHandler(filters.ALL, catch))
    
    print("🚀 Bot başlatılıyor...")
    app.run_polling(drop_pending_updates=True, stop_signals=None)
