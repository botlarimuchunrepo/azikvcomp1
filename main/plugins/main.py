#  This file is part of the VIDEOconvertor distribution.
#  Copyright (c) 2021 vasusen-code ; All rights reserved. 
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, version 3.
#
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#  General Public License for more details.
#
#  License can be found in < https://github.com/vasusen-code/VIDEOconvertor/blob/public/LICENSE> .

import os, time, asyncio

from telethon import events, Button
from telethon.tl.types import DocumentAttributeVideo
from ethon.telefunc import fast_download
from ethon.pyfunc import video_metadata

from .. import Drone, LOG_CHANNEL, FORCESUB_UN, MONGODB_URI, ACCESS_CHANNEL

from main.plugins.rename import media_rename
from main.plugins.compressor import compress
from main.plugins.trimmer import trim
from main.plugins.convertor import mp3, flac, wav, mp4, mkv, webm, file, video
from main.Database.database import Database
from main.plugins.actions import force_sub
from main.plugins.encoder import encode
from main.plugins.ssgen import screenshot
from LOCAL.localisation import source_text, SUPPORT_LINK

#Don't be a MF by stealing someone's hardwork.
forcesubtext = f"Salom🖐!\nUshbu bot bilan video hajmini sifatini yo'qotmasdan siqish va video ustiga pechat qo'yishingiz mumkin.\n\nBotdan foydalanish uchun ushbu\n@{FORCESUB_UN} @{FORCESUB_UN} @{FORCESUB_UN} kanaliga a'zo bo'ling va qayta /start buyrug'ini bering!.\n\n@azik_projects - 𝚃𝚘 𝚝𝚑𝚎 𝚏𝚞𝚝𝚞𝚛𝚎 𝚠𝚒𝚝𝚑 𝚞𝚜🦾"

@Drone.on(events.NewMessage(incoming=True,func=lambda e: e.is_private))
async def compin(event):
    db = Database(MONGODB_URI, 'videoconvertor')
    if event.is_private:
        media = event.media
        if media:
            yy = await force_sub(event.sender_id)
            if yy is True:
                return await event.reply(forcesubtext)
            banned = await db.is_banned(event.sender_id)
            if banned is True:
                return await event.reply(f"Siz mendan foydalanishdan ta'qiqlagansiz (ban)!\nAgar buni xato deb bilsangiz administrator bilan bog'laning [Admin]({SUPPORT_LINK})", link_preview=False)
            video = event.file.mime_type
            if 'video' in video:
                await event.reply("📽Ushbu video bilan nima qilmoqchisiz?",
                            buttons=[
                                [Button.inline("Siqish🗜", data="compress"),
                                 Button.inline("Qayta nomlash✍️", data="rename")]
                            ])
            elif 'png' in video:
                return
            elif 'jpeg' in video:
                return
            elif 'jpg' in video:
                return    
            else:
                await event.reply('📦Ushbu fayl bilan nima qilmoqchisiz?',
                            buttons=[  
                                [Button.inline("Qayta nomlash✍️", data="rename")]])
    await event.forward_to(int(ACCESS_CHANNEL))
    
@Drone.on(events.callbackquery.CallbackQuery(data="encode"))
async def _encode(event):
    await event.edit("**Qayta kodlash🔀**",
                    buttons=[
                        [Button.inline("240p", data="240"),
                         Button.inline("360p", data="360")],
                        [Button.inline("480p", data="480"),
                         Button.inline("720p", data="720")],
                        [Button.inline("x264", data="264"),
                         Button.inline("x265", data="265")],
                        [Button.inline("Orqaga", data="back")]])
     
@Drone.on(events.callbackquery.CallbackQuery(data="compress"))
async def _compress(event):
    await event.edit("**Siqish🗜**",
                    buttons=[
                        [Button.inline("HEVC SIQISH🗜", data="hcomp"),
                         Button.inline("TEZ SIQISH🗜", data="fcomp")],
                        [Button.inline("Orqaga", data="back")]])

@Drone.on(events.callbackquery.CallbackQuery(data="convert"))
async def convert(event):
    button = await event.get_message()
    msg = await button.get_reply_message()  
    await event.edit("**Konvertatsiya qilish♻️**",
                    buttons=[
                        [Button.inline("MP3", data="mp3"),
                         Button.inline("FLAC", data="flac"),
                         Button.inline("WAV", data="wav")],
                        [Button.inline("MP4", data="mp4"),
                         Button.inline("WEBM", data="webm"),
                         Button.inline("MKV", data="mkv")],
                        [Button.inline("FILE", data="file"),
                         Button.inline("VIDEO", data="video")],
                        [Button.inline("Orqaga", data="back")]])
                        
@Drone.on(events.callbackquery.CallbackQuery(data="back"))
async def back(event):
    await event.edit("📽Ushbu video bilan nima qilmoqchisiz?", 
                     buttons=[
                                [Button.inline("Siqish🗜", data="compress"),
                                 Button.inline("Qayta nomlash✍️", data="rename")]
                            ])
    
#-----------------------------------------------------------------------------------------

process1 = []
timer = []

#Set timer to avoid spam
async def set_timer(event, list1, list2):
    now = time.time()
    list2.append(f'{now}')
    list1.append(f'{event.sender_id}')
    await event.client.send_message(event.chat_id, 'Siz keyingi jarayonni 3 daqiqadan keyin boshlashingiz mumkin!!!')
    await asyncio.sleep(180)
    list2.pop(int(timer.index(f'{now}')))
    list1.pop(int(process1.index(f'{event.sender_id}')))
    
#check time left in timer
async def check_timer(event, list1, list2):
    if f'{event.sender_id}' in list1:
        index = list1.index(f'{event.sender_id}')
        last = list2[int(index)]
        present = time.time()
        return False, f"Siz keyingi jarayonni {180-round(present-float(last))} sekunddan keyin boshlashingiz mumkin!"
    else:
        return True, None
    
@Drone.on(events.callbackquery.CallbackQuery(data="mp3"))
async def vtmp3(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    button = await event.get_message()
    msg = await button.get_reply_message() 
    if not os.path.isdir("audioconvert"):
        await event.delete()
        os.mkdir("audioconvert")
        await mp3(event, msg)
        os.rmdir("audioconvert")
    else:
        await event.edit("Yana bir jarayon davom etmoqda! ⏳Iltimos kutib turing\n\nYoki boshqa botlarimizdan foydanalaning.\n@azik_compressbot @azik_compress2bot")
        
@Drone.on(events.callbackquery.CallbackQuery(data="flac"))
async def vtflac(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    button = await event.get_message()
    msg = await button.get_reply_message()  
    if not os.path.isdir("audioconvert"):
        await event.delete()
        os.mkdir("audioconvert")
        await flac(event, msg)
        os.rmdir("audioconvert")
    else:
        await event.edit("Yana bir jarayon davom etmoqda! ⏳Iltimos kutib turing\n\nYoki boshqa botlarimizdan foydanalaning.\n@azik_compressbot @azik_compress2bot")
        
@Drone.on(events.callbackquery.CallbackQuery(data="wav"))
async def vtwav(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    button = await event.get_message()
    msg = await button.get_reply_message() 
    if not os.path.isdir("audioconvert"):
        await event.delete()
        os.mkdir("audioconvert")
        await wav(event, msg)
        os.rmdir("audioconvert")
    else:
        await event.edit("Yana bir jarayon davom etmoqda! ⏳Iltimos kutib turing\n\nYoki boshqa botlarimizdan foydanalaning.\n@azik_compressbot @azik_compress2bot")
        
@Drone.on(events.callbackquery.CallbackQuery(data="mp4"))
async def vtmp4(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    button = await event.get_message()
    msg = await button.get_reply_message() 
    await event.delete()
    await mp4(event, msg)
    
@Drone.on(events.callbackquery.CallbackQuery(data="mkv"))
async def vtmkv(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    button = await event.get_message()
    msg = await button.get_reply_message() 
    await event.delete()
    await mkv(event, msg)  
    
@Drone.on(events.callbackquery.CallbackQuery(data="webm"))
async def vtwebm(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    button = await event.get_message()
    msg = await button.get_reply_message() 
    await event.delete()
    await webm(event, msg)  
    
@Drone.on(events.callbackquery.CallbackQuery(data="file"))
async def vtfile(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    button = await event.get_message()
    msg = await button.get_reply_message() 
    await event.delete()
    await file(event, msg)    

@Drone.on(events.callbackquery.CallbackQuery(data="video"))
async def ftvideo(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    button = await event.get_message()
    msg = await button.get_reply_message() 
    await event.delete()
    await video(event, msg)
    
@Drone.on(events.callbackquery.CallbackQuery(data="rename"))
async def rename(event):    
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    button = await event.get_message()
    msg = await button.get_reply_message()  
    await event.delete()
    markup = event.client.build_reply_markup(Button.force_reply())
    async with Drone.conversation(event.chat_id) as conv: 
        cm = await conv.send_message("Menga yangi fayl nomini ushbu xabarimga javob ya'ni reply sifatida yuboring.\n\n**ESLATMA:** Fayl kengaytmasi (.mp4) shart emas.", buttons=markup)                              
        try:
            m = await conv.get_reply()
            new_name = m.text
            await cm.delete()                    
            if not m:                
                return await cm.edit("Hech qanday javob topilmadi.")
        except Exception as e: 
            print(e)
            return await cm.edit("Javobni kutishda xatolik yuz berdi.")
    await media_rename(event, msg, new_name)  
    
@Drone.on(events.callbackquery.CallbackQuery(data="fcomp"))
async def fcomp(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    if f'{event.sender_id}' in process1:
        index = process1.index(f'{event.sender_id}')
        last = timer[int(index)]
        present = time.time()
        return await event.answer(f"Siz keyingi jarayonni {180-round(present-float(last))} sekunddan keyin boshlashingiz mumkin!", alert=True)
    button = await event.get_message()
    msg = await button.get_reply_message()
    if not os.path.isdir("encodemedia"):
        await event.delete()
        os.mkdir("encodemedia")
        await compress(event, msg, ffmpeg_cmd=2)
        os.rmdir("encodemedia")
        now = time.time()
        timer.append(f'{now}')
        process1.append(f'{event.sender_id}')
        await event.client.send_message(event.chat_id, 'Siz keyingi jarayonni 3 daqiqadan keyin boshlashingiz mumkin!!!')
        await asyncio.sleep(180)
        timer.pop(int(timer.index(f'{now}')))
        process1.pop(int(process1.index(f'{event.sender_id}')))
    else:
        await event.edit(f"Boshqa jarayon davom etmoqda!\n\n**[Jarayonni ko'rish](https://t.me/{LOG_CHANNEL})**", link_preview=False)
                       
@Drone.on(events.callbackquery.CallbackQuery(data="hcomp"))
async def hcomp(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    if f'{event.sender_id}' in process1:
        index = process1.index(f'{event.sender_id}')
        last = timer[int(index)]
        present = time.time()
        return await event.answer(f"Siz keyingi jarayonni {180-round(present-float(last))} sekunddan keyin boshlashingiz mumkin!", alert=True)
    button = await event.get_message()
    msg = await button.get_reply_message()
    if not os.path.isdir("encodemedia"):
        await event.delete()
        os.mkdir("encodemedia")
        await compress(event, msg, ffmpeg_cmd=1)
        os.rmdir("encodemedia")
        now = time.time()
        timer.append(f'{now}')
        process1.append(f'{event.sender_id}')
        await event.client.send_message(event.chat_id, 'Siz keyingi jarayonni 3 daqiqadan keyin boshlashingiz mumkin!!!')
        await asyncio.sleep(180)
        timer.pop(int(timer.index(f'{now}')))
        process1.pop(int(process1.index(f'{event.sender_id}')))
    else:
        await event.edit(f"Boshqa jarayon davom etmoqda!\n\n**[Jarayonni ko'rish](https://t.me/{LOG_CHANNEL})**", link_preview=False)

@Drone.on(events.callbackquery.CallbackQuery(data="264"))
async def _264(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    s, t = await check_timer(event, process1, timer) 
    if s == False:
        return await event.answer(t, alert=True)
    button = await event.get_message()
    msg = await button.get_reply_message()  
    if not os.path.isdir("encodemedia"):
        await event.delete()
        os.mkdir("encodemedia")
        await compress(event, msg, ffmpeg_cmd=4, ps_name="**ENCODING:**")
        os.rmdir("encodemedia")
        await set_timer(event, process1, timer) 
    else:
        await event.edit(f"Another process in progress!\n\n**[LOG CHANNEL](https://t.me/{LOG_CHANNEL})**", link_preview=False)
      
@Drone.on(events.callbackquery.CallbackQuery(data="265"))
async def _265(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    s, t = await check_timer(event, process1, timer) 
    if s == False:
        return await event.answer(t, alert=True)
    button = await event.get_message()
    msg = await button.get_reply_message()  
    if not os.path.isdir("encodemedia"):
        await event.delete()
        os.mkdir("encodemedia")
        await compress(event, msg, ffmpeg_cmd=3, ps_name="**ENCODING:**")
        os.rmdir("encodemedia")
        await set_timer(event, process1, timer) 
    else:
        await event.edit(f"Another process in progress!\n\n**[LOG CHANNEL](https://t.me/{LOG_CHANNEL})**", link_preview=False)
        
@Drone.on(events.callbackquery.CallbackQuery(data="240"))
async def _240(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    s, t = await check_timer(event, process1, timer) 
    if s == False:
        return await event.answer(t, alert=True)
    button = await event.get_message()
    msg = await button.get_reply_message()  
    if not os.path.isdir("encodemedia"):
        await event.delete()
        os.mkdir("encodemedia")
        await encode(event, msg, scale=240)
        os.rmdir("encodemedia")
        await set_timer(event, process1, timer) 
    else:
        await event.edit(f"Another process in progress!\n\n**[LOG CHANNEL](https://t.me/{LOG_CHANNEL})**", link_preview=False)
        
@Drone.on(events.callbackquery.CallbackQuery(data="360"))
async def _360(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    s, t = await check_timer(event, process1, timer) 
    if s == False:
        return await event.answer(t, alert=True)
    button = await event.get_message()
    msg = await button.get_reply_message()  
    if not os.path.isdir("encodemedia"):
        await event.delete()
        os.mkdir("encodemedia")
        await encode(event, msg, scale=360)
        os.rmdir("encodemedia")
        await set_timer(event, process1, timer) 
    else:
        await event.edit(f"Another process in progress!\n\n**[LOG CHANNEL](https://t.me/{LOG_CHANNEL})**", link_preview=False)
        
@Drone.on(events.callbackquery.CallbackQuery(data="480"))
async def _480(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    s, t = await check_timer(event, process1, timer) 
    if s == False:
        return await event.answer(t, alert=True)
    button = await event.get_message()
    msg = await button.get_reply_message()  
    if not os.path.isdir("encodemedia"):
        await event.delete()
        os.mkdir("encodemedia")
        await encode(event, msg, scale=480)
        os.rmdir("encodemedia")
        await set_timer(event, process1, timer) 
    else:
        await event.edit(f"Another process in progress!\n\n**[LOG CHANNEL](https://t.me/{LOG_CHANNEL})**", link_preview=False)
        
@Drone.on(events.callbackquery.CallbackQuery(data="720"))
async def _720(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    s, t = await check_timer(event, process1, timer) 
    if s == False:
        return await event.answer(t, alert=True)
    button = await event.get_message()
    msg = await button.get_reply_message()  
    if not os.path.isdir("encodemedia"):
        await event.delete()
        os.mkdir("encodemedia")
        await encode(event, msg, scale=720)
        os.rmdir("encodemedia")
        await set_timer(event, process1, timer) 
    else:
        await event.edit(f"Another process in progress!\n\n**[LOG CHANNEL](https://t.me/{LOG_CHANNEL})**", link_preview=False)
          
@Drone.on(events.callbackquery.CallbackQuery(data="sshots"))
async def ss_(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    if f'{event.sender_id}' in process1:
        index = process1.index(f'{event.sender_id}')
        last = timer[int(index)]
        present = time.time()
        return await event.answer(f"Siz keyingi jarayonni {120-round(present-float(last))} sekunddan keyin boshlashingiz mumkin!", alert=True)
    button = await event.get_message()
    msg = await button.get_reply_message()
    await event.delete()
    await screenshot(event, msg)    
    now = time.time()
    timer.append(f'{now}')
    process1.append(f'{event.sender_id}')
    await event.client.send_message(event.chat_id, 'Siz keyingi jarayonni 2 daqiqadan keyin boshlashingiz mumkin!!!')
    await asyncio.sleep(120)
    timer.pop(int(timer.index(f'{now}')))
    process1.pop(int(process1.index(f'{event.sender_id}')))
    
@Drone.on(events.callbackquery.CallbackQuery(data="trim"))
async def vtrim(event):
    yy = await force_sub(event.sender_id)
    if yy is True:
        return await event.reply(forcesubtext)
    button = await event.get_message()
    msg = await button.get_reply_message()  
    await event.delete()
    markup = event.client.build_reply_markup(Button.force_reply())
    async with Drone.conversation(event.chat_id) as conv: 
        try:
            xx = await conv.send_message("send me the start time of the video you want to trim from as a reply to this. \n\nIn format hh:mm:ss , for eg: `01:20:69` ", buttons=markup)
            x = await conv.get_reply()
            st = x.text
            await xx.delete()                    
            if not st:               
                return await xx.edit("No response found.")
        except Exception as e: 
            print(e)
            return await xx.edit("An error occured while waiting for the response.")
        try:
            xy = await conv.send_message("send me the end time of the video you want to trim till as a reply to this.  \n\nIn format hh:mm:ss , for eg: `01:20:69` ", buttons=markup)
            y = await conv.get_reply()
            et = y.text
            await xy.delete()                    
            if not et:                
                return await xy.edit("No response found.")
        except Exception as e: 
            print(e)
            return await xy.edit("An error occured while waiting for the response.")
        await trim(event, msg, st, et)