import os, subprocess, time, asyncio, threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8030105235:AAHCN3kX97OOagbTCVgnIZ1u3JNQB8upayY"
user_files = {}

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    # Her start komutunda kullanıcının eski dosyalarını hafızadan temizle
    user_files[u.effective_user.id] = {'v': None, 'a': None, 's': None}
    await u.message.reply_text("👋 Selam Şervan! Hafıza temizlendi. Şimdi Videoyu, SESİ ve Altyazıyı gönder.")

async def catch(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if uid not in user_files: user_files[uid] = {'v': None, 'a': None, 's': None}
    
    msg = u.message
    file = (msg.video or msg.audio or msg.voice or msg.document)
    if not file: return
    
    f_obj = await file.get_file()
    orig_name = f_obj.file_path.split('/')[-1].lower()
    timestamp = int(time.time())

    # Dosyaları benzersiz isimlerle kaydet ki karışmasın
    if any(x in orig_name for x in ['.mp4', '.mov', '.avi']):
        path = f"{uid}_{timestamp}_video.mp4"
        user_files[uid]['v'] = path
    elif any(x in orig_name or msg.voice or msg.audio for x in ['.mp3', '.wav', '.m4a']):
        path = f"{uid}_{timestamp}_audio.mp3"
        user_files[uid]['a'] = path
    else:
        path = f"{uid}_{timestamp}_sub.srt" 
        user_files[uid]['s'] = path
        
    await f_obj.download_to_drive(path)
    await u.message.reply_text(f"✅ Kaydedildi: {path.split('_')[-1]}")

async def merge(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    d = user_files.get(uid, {})
    
    if not d.get('v') or not d.get('a') or not d.get('s'):
        await u.message.reply_text("❌ Hala eksik dosya var! Hepsini gönderdiğinden emin ol.")
        return

    m = await u.message.reply_text("⏳ Senin seçtiğin sesle renderlanıyor, lütfen bekle...")
    out = f"final_{uid}_{int(time.time())}.mp4"
    
    # FFmpeg komutu - Senin sesini (-i d['a']) videoya zorla ekler
    cmd = ['ffmpeg', '-y', '-i', d['v'], '-i', d['a'], '-vf', f"subtitles='{os.path.abspath(d['s'])}'", '-c:v', 'libx264', '-c:a', 'aac', '-map', '0:v:0', '-map', '1:a:0', '-shortest', out]
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0: raise Exception(process.stderr)
        await u.message.reply_document(document=open(out, 'rb'), caption="İşte senin sesinle hazır! 🎉")
    except Exception as e:
        await u.message.reply_text(f"Hata: {str(e)[:100]}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("birlestir", merge))
    app.add_handler(MessageHandler(filters.ALL, catch))
    # Render için basit web server
    import gradio as gr
    threading.Thread(target=lambda: gr.Interface(fn=lambda: "Aktif", inputs=[], outputs="text").launch(server_name="0.0.0.0", server_port=10000), daemon=True).start()
    app.run_polling(drop_pending_updates=True, stop_signals=None)
