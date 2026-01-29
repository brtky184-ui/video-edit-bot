import os, subprocess, time, asyncio, threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8030105235:AAHCN3kX97OOagbTCVgnIZ1u3JNQB8upayY"
user_files = {}

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user_files[u.effective_user.id] = {'v': None, 'a': None, 's': None}
    await u.message.reply_text("📱 Dikey format ayarlandı! Artık altyazılar videoyu kaplamayacak. Gönder bakalım.")

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
        path = f"{uid}_{ts}_v.mp4"
        user_files[uid]['v'] = path
    elif any(x in orig_name or msg.voice or msg.audio for x in ['.mp3', '.wav', '.m4a']):
        path = f"{uid}_{ts}_a.mp3"
        user_files[uid]['a'] = path
    else:
        path = f"{uid}_{ts}_s.srt" 
        user_files[uid]['s'] = path
    await f_obj.download_to_drive(path)
    await u.message.reply_text(f"✅ Kaydedildi.")

async def merge(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    d = user_files.get(uid, {})
    if not all([d.get('v'), d.get('a'), d.get('s')]):
        await u.message.reply_text("❌ Dosyalar eksik!")
        return
    m = await u.message.reply_text("⏳ Dikey formatta renderlanıyor...")
    out = f"final_{uid}_{int(time.time())}.mp4"
    sub_path = os.path.abspath(d['s'])
    
    # DİKEY VİDEO AYARI: Fontu 12'ye çektik (yarı yarıya küçüldü), MarginV ile biraz yukarı kaldırdık
    style = "FontSize=12,PrimaryColour=&H00FFFF&,OutlineColour=&H000000&,BorderStyle=1,Outline=1,Bold=1,MarginV=30"
    
    cmd = [
        'ffmpeg', '-y', '-i', d['v'], '-i', d['a'], 
        '-vf', f"subtitles='{sub_path}':force_style='{style}'", 
        '-c:v', 'libx264', '-c:a', 'aac', '-map', '0:v:0', '-map', '1:a:0', '-shortest', out
    ]
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0: raise Exception(process.stderr)
        await u.message.reply_document(document=open(out, 'rb'), caption="İşte dikey formatta hazır! 🔥")
    except Exception as e:
        await u.message.reply_text(f"Hata: {str(e)[:50]}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("birlestir", merge))
    app.add_handler(MessageHandler(filters.ALL, catch))
    import gradio as gr
    threading.Thread(target=lambda: gr.Interface(fn=lambda: "OK", inputs=[], outputs="text").launch(server_name="0.0.0.0", server_port=10000), daemon=True).start()
    app.run_polling(drop_pending_updates=True, stop_signals=None)
