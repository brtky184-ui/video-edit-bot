import os, subprocess, time, asyncio, threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8030105235:AAHCN3kX97OOagbTCVgnIZ1u3JNQB8upayY"
user_files = {}

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user_files[u.effective_user.id] = {'v': None, 'a': None, 's': None}
    await u.message.reply_text("🚀 Sistem Sıfırlandı! Dosyaları tekrar gönder, bu sefer altyazı kaçamayacak.")

async def catch(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    if uid not in user_files: user_files[uid] = {'v': None, 'a': None, 's': None}
    msg = u.message
    file = (msg.video or msg.audio or msg.voice or msg.document)
    if not file: return
    f_obj = await file.get_file()
    orig_name = f_obj.file_path.split('/')[-1].lower()
    ts = int(time.time())
    
    # Dosya isimlerini sabitliyoruz
    if any(x in orig_name for x in ['.mp4', '.mov', '.avi']):
        path = f"video_{uid}.mp4"
        user_files[uid]['v'] = path
    elif any(x in orig_name or msg.voice or msg.audio for x in ['.mp3', '.wav', '.m4a']):
        path = f"audio_{uid}.mp3"
        user_files[uid]['a'] = path
    else:
        path = f"sub_{uid}.srt" 
        user_files[uid]['s'] = path
    
    await f_obj.download_to_drive(path)
    await u.message.reply_text(f"✅ Alındı.")

async def merge(u: Update, c: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    d = user_files.get(uid, {})
    if not all([d.get('v'), d.get('a'), d.get('s')]):
        await u.message.reply_text("❌ Dosyalar eksik!")
        return
    
    m = await u.message.reply_text("⏳ Altyazılar videoya işleniyor...")
    out = f"final_{uid}.mp4"
    
    # Altyazı dosyasının tam yolunu al ve FFmpeg'in anlayacağı şekle getir
    sub_path = os.path.abspath(d['s']).replace('\\', '/').replace(':', '\\:')
    
    # FONT VE STİL GÜNCELLEMESİ: Fontu Arial yaptık, Outline'ı artırdık
    style = "FontSize=12,PrimaryColour=&H00FFFF&,OutlineColour=&H000000&,BorderStyle=1,Outline=2,Bold=1,MarginV=60"
    
    cmd = [
        'ffmpeg', '-y', '-i', d['v'], '-i', d['a'], 
        '-vf', f"subtitles='{sub_path}':force_style='{style}'", 
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', '-c:a', 'aac', 
        '-map', '0:v:0', '-map', '1:a:0', '-shortest', out
    ]
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0:
            print(f"FFMPEG Hata Logu: {process.stderr}") # Render loglarında görebilmek için
            raise Exception("FFmpeg hatası")
        await u.message.reply_document(document=open(out, 'rb'), caption="İşte altyazılı videon! 🔥")
    except Exception as e:
        await u.message.reply_text("Hata oluştu! Lütfen SRT dosyasının formatını ve saniyeleri kontrol et.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("birlestir", merge))
    app.add_handler(MessageHandler(filters.ALL, catch))
    # Render için dummy web sunucusu
    import gradio as gr
    threading.Thread(target=lambda: gr.Interface(fn=lambda: "OK", inputs=[], outputs="text").launch(server_name="0.0.0.0", server_port=10000), daemon=True).start()
    app.run_polling(drop_pending_updates=True, stop_signals=None)
