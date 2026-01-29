import os, subprocess, time, asyncio, threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8030105235:AAHCN3kX97OOagbTCVgnIZ1u3JNQB8upayY"
user_files = {}

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user_files[u.effective_user.id] = {'v': None, 'a': None, 's': None}
    await u.message.reply_text("⚡ Hızlı & Kalıcı Mod Aktif! Max 2 dakika içinde videon hazır.")

async def catch(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if uid not in user_files: user_files[uid] = {'v': None, 'a': None, 's': None}
    msg = u.message
    file = (msg.video or msg.audio or msg.voice or msg.document)
    if not file: return
    f_obj = await file.get_file()
    orig_name = f_obj.file_path.split('/')[-1].lower()
    ts = int(time.time())
    
    if any(x in orig_name for x in ['.mp4', '.mov', '.avi']):
        path = f"v_{uid}.mp4"
        user_files[uid]['v'] = path
    elif any(x in orig_name or msg.voice or msg.audio for x in ['.mp3', '.wav', '.m4a']):
        path = f"a_{uid}.mp3"
        user_files[uid]['a'] = path
    else:
        path = f"s_{uid}.srt" 
        user_files[uid]['s'] = path
    await f_obj.download_to_drive(path)
    await u.message.reply_text(f"✅ Alındı.")

async def merge(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    d = user_files.get(uid, {})
    if not all([d.get('v'), d.get('a'), d.get('s')]):
        await u.message.reply_text("❌ Dosyalar eksik!")
        return
    
    m = await u.message.reply_text("⏳ İşlem başladı, 1-2 dakika içinde geliyor...")
    out = f"final_{uid}.mp4"
    sub_path = os.path.abspath(d['s']).replace('\\', '/').replace(':', '\\:')
    
    # HIZLI VE KÜÇÜK ALTYAZI AYARI:
    # Fontu biraz küçülttük (10), ultrafast preset ekledik.
    style = "FontSize=10,PrimaryColour=&H00FFFF&,OutlineColour=&H000000&,BorderStyle=1,Outline=1,Bold=1,Alignment=2,MarginV=50"
    
    cmd = [
        'ffmpeg', '-y', '-i', d['v'], '-i', d['a'], 
        '-vf', f"subtitles='{sub_path}':force_style='{style}'", 
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28', '-c:a', 'aac', '-b:a', '128k',
        '-map', '0:v:0', '-map', '1:a:0', '-shortest', out
    ]
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0: raise Exception("Hata")
        await u.message.reply_document(document=open(out, 'rb'), caption="Hızlıca hazırlandı! 🔥")
    except Exception as e:
        await u.message.reply_text("Saniyeleri kontrol et, hata verdi.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("birlestir", merge))
    app.add_handler(MessageHandler(filters.ALL, catch))
    import gradio as gr
    threading.Thread(target=lambda: gr.Interface(fn=lambda: "OK", inputs=[], outputs="text").launch(server_name="0.0.0.0", server_port=10000), daemon=True).start()
    app.run_polling(drop_pending_updates=True, stop_signals=None)
