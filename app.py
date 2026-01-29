import os, subprocess, time, asyncio, threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8030105235:AAHCN3kX97OOagbTCVgnIZ1u3JNQB8upayY"
user_files = {}

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user_files[u.effective_user.id] = {}
    await u.message.reply_text("👋 Selam Şervan! Altyazı, ses ve videoyu gönder, sonra /birlestir yaz.")

async def catch(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if uid not in user_files: user_files[uid] = {}
    
    msg = u.message
    file = (msg.video or msg.audio or msg.voice or msg.document)
    if not file: return
    
    f_obj = await file.get_file()
    # Dosya ismini temizle ve uzantıyı al
    orig_name = f_obj.file_path.split('/')[-1].lower()
    
    if any(x in orig_name for x in ['.mp4', '.mov', '.avi']):
        path = f"{uid}_video.mp4"
        user_files[uid]['v'] = path
    elif any(x in orig_name for x in ['.mp3', '.wav', '.m4a']):
        path = f"{uid}_audio.mp3"
        user_files[uid]['a'] = path
    else:
        # Metin/Altyazı dosyası ise mutlaka .srt yapıyoruz
        path = f"{uid}_sub.srt" 
        user_files[uid]['s'] = path
        
    await f_obj.download_to_drive(path)
    await u.message.reply_text(f"✅ Dosya hazır: {path}")

async def merge(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    d = user_files.get(uid, {})
    if not all(k in d for k in ['v', 'a', 's']):
        await u.message.reply_text("❌ Dosyalar eksik!")
        return

    m = await u.message.reply_text("⏳ Render başladı...")
    out = f"final_{uid}.mp4"
    
    # Altyazı dosyasını ffmpeg'in okuyabileceği mutlak yola çevir
    sub_path = os.path.abspath(d['s'])
    
    # FFmpeg komutu - Altyazı hatasını önlemek için basitleştirildi
    cmd = ['ffmpeg', '-y', '-i', d['v'], '-i', d['a'], '-vf', f"subtitles='{sub_path}'", '-shortest', out]
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0:
            raise Exception(process.stderr)
        await u.message.reply_document(document=open(out, 'rb'), caption="İşlem tamam! 🎉")
    except Exception as e:
        await u.message.reply_text(f"Hata: Altyazı formatı geçersiz olabilir. Lütfen SRT formatında olduğundan emin ol.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("birlestir", merge))
    app.add_handler(MessageHandler(filters.ALL, catch))
    
    # Render'ın kapanmaması için basit bir web server
    import gradio as gr
    def dummy(): return "Aktif"
    threading.Thread(target=lambda: gr.Interface(fn=dummy, inputs=[], outputs="text").launch(server_name="0.0.0.0", server_port=10000), daemon=True).start()
    
    app.run_polling(drop_pending_updates=True, stop_signals=None)
