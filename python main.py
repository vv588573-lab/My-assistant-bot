import telebot
import requests
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from gtts import gTTS
import speech_recognition as sr
import subprocess

load_dotenv()

# 

bot = telebot.TeleBot(BOT_TOKEN)

def allowed(message):
    return message.from_user.id == ALLOWED

def ask_ai(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    body = {"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}]}
    try:
        r = requests.post(url, json=body, headers=headers, timeout=60)
        data = r.json()
        if "choices" not in data:
            return f"❌ Error: {str(data.get('error', {}).get('message', ''))[:100]}"
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Error: {str(e)[:100]}"

def make_voice(text, filename="reply.mp3"):
    try:
        tts = gTTS(text=text, lang='hi')
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

@bot.message_handler(commands=['start', 'help'])
def start(message):
    if not allowed(message): return
    bot.reply_to(message, "🤖 *Smart AI Assistant*\n\nAap mujhse type karein, ya *Voice Message* bhejein. Main aapko aawaz mein jawab dunga!", parse_mode='Markdown')

@bot.message_handler(content_types=['voice'])
def chat_voice(message):
    if not allowed(message): return
    bot.send_chat_action(message.chat.id, 'record_voice')
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("voice.ogg", 'wb') as new_file:
        new_file.write(downloaded_file)
    bot.reply_to(message, "🎧 Aapki aawaz sun raha hoon...")
    try:
        subprocess.run(["ffmpeg", "-y", "-i", "voice.ogg", "voice.wav"], check=True, capture_output=True)
        r = sr.Recognizer()
        with sr.AudioFile("voice.wav") as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language="hi-IN")
        bot.reply_to(message, f"🗣️ *Aapne kaha:* {text}", parse_mode='Markdown')
        reply = ask_ai(text)
        bot.reply_to(message, reply[:4000])
        bot.send_chat_action(message.chat.id, 'record_voice')
        voice_file = make_voice(reply)
        if voice_file:
            with open(voice_file, 'rb') as v:
                bot.send_voice(message.chat.id, v)
    except sr.UnknownValueError:
        bot.reply_to(message, "❌ Maaf kijiye, main aapki aawaz samajh nahi paya.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:150]}")

@bot.message_handler(func=lambda m: True, content_types=['text'])
def chat_text(message):
    if not allowed(message): return
    bot.send_chat_action(message.chat.id, 'typing')
    reply = ask_ai(message.text)
    bot.reply_to(message, reply[:4000])

print("✅ Assistant chalu...")
telebot.apihelper.CONNECT_TIMEOUT = 60
telebot.apihelper.READ_TIMEOUT = 60
bot.infinity_polling(timeout=60, long_polling_timeout=60)
