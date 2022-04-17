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

from telethon import events, Button
from ethon.teleutils import mention
from ethon.mystarts import vc_menu

from .. import Drone, ACCESS_CHANNEL, AUTH_USERS

from main.plugins.actions import set_thumbnail, rem_thumbnail, heroku_restart
from LOCAL.localisation import START_TEXT as st
from LOCAL.localisation import info_text, spam_notice, help_text, DEV, source_text, SUPPORT_LINK

@Drone.on(events.NewMessage(incoming=True, pattern="/start"))
async def start(event):
    await event.reply(f'{st}', 
                      buttons=[
                              [Button.inline("Yordam🤔", data="help"),
                              Button.url("AziK ProJecTs🦾", url="https://t.me/azik_projects") ]])
    tag = f'[{event.sender.first_name}](tg://user?id={event.sender_id})'
    await Drone.send_message(int(ACCESS_CHANNEL), f'{tag} Botni ishga tushurdi. #NEWUSER')
    
@Drone.on(events.callbackquery.CallbackQuery(data="menu"))
async def menu(event):
    await vc_menu(event)
    
@Drone.on(events.callbackquery.CallbackQuery(data="info"))
async def info(event):
    await event.edit(f'**ℹ️NFO:**\n\n{info_text}',
                    buttons=[[
                         Button.inline("Menu.", data="menu")]])
    
@Drone.on(events.callbackquery.CallbackQuery(data="notice"))
async def notice(event):
    await event.answer(f'{spam_notice}', alert=True)
    
@Drone.on(events.NewMessage(incoming=True, pattern="/yordam"))
async def start(event):
    await event.reply(f'{st}', 
                      buttons=[Button.inline("Plaginlar", data="plugins"),
                         Button.inline("Qayta yuklash", data="restart")])
    
@Drone.on(events.callbackquery.CallbackQuery(data="source"))
async def source(event):
    await event.edit(source_text,
                    buttons=[[
                         Button.url("FOR PERSONAL USE", url="https://github.com/vasusen-code/videoconvertor/tree/main"),
                         Button.url("FOR YOUR CHANNEL ", url="https://github.com/vasusen-code/videoconvertor/")]])
    
    
@Drone.on(events.callbackquery.CallbackQuery(data="boshsahifa"))
async def help(event):
    await event.edit("""Salom🖖 Mendan foydalanib siz⤵️ 
    
Video hajmini siqishingiz mumkin🗜✅

Boshqa jarayon davom etayotgan bo'lsa boshqa botlarimizda sinab ko'ring👇
👉 @azik_compress2bot @azik_compress3bot 👈

Video yuboring!!
@azik_projects - 𝚃𝚘 𝚝𝚑𝚎 𝚏𝚞𝚝𝚞𝚛𝚎 𝚠𝚒𝚝𝚑 𝚞𝚜🦾""",
                    buttons=[
                              [Button.inline("Yordam🤔", data="help"),
                              Button.url("AziK ProJecTs🦾", url="https://t.me/azik_projects") ]])                         
                    
@Drone.on(events.callbackquery.CallbackQuery(data="help"))
async def help(event):
    await event.edit("**Yordam va sozlamalar👥**\n\nESLATMA: Pechat rasm qo'ysangiz u faqat Qayta nomlash✍️ bo'limida ishlaydi yoki @azik_renamerbot va siqib bo'lgan videoyingizni yuboring.\n\n👉👉Videoni siqib bo'lgandan keyin uni qayta botga yuboring va nomini o'zgartiring shunda pechat rasmingiz siqilgan videoga qo'yib beradi👈👈",
                    buttons=[[
                         Button.inline("Pechat rasm qo'yish", data="sett"),
                         Button.inline("Pechat rasm olib tashlash", data='remt')],
                     
                         [Button.url("Qo'llab quvvatlash guruhi", url=f"{SUPPORT_LINK}")],
                         [
                         Button.inline("Orqaga", data="help")]])
    
@Drone.on(events.callbackquery.CallbackQuery(data="plugins"))
async def plugins(event):
    await event.edit(f'{help_text}',
                    buttons=[[Button.inline("Menu.", data="menu")]])
                   
 #-----------------------------------------------------------------------------------------------                            
    
@Drone.on(events.callbackquery.CallbackQuery(data="sett"))
async def sett(event):    
    button = await event.get_message()
    msg = await button.get_reply_message() 
    await event.delete()
    async with Drone.conversation(event.chat_id) as conv: 
        xx = await conv.send_message("Ushbu xabarimga javob sifatida ya'ni reply qilib rasm jo'nating.\n\nVideoni siqib bo'lgandan keyin uni qayta botga yuboring va nomini o'zgartiring shunda pechat rasmingiz siqilgan videoga qo'yib beradi.")
        x = await conv.get_reply()
        if not x.media:
            xx.edit("Hech qanday mediafayl topilmadi")
        mime = x.file.mime_type
        if not 'png' in mime:
            if not 'jpg' in mime:
                if not 'jpeg' in mime:
                    return await xx.edit("Hech qanday rasm topilmadi.")
        await set_thumbnail(event, x.media)
        await xx.delete()
        
@Drone.on(events.callbackquery.CallbackQuery(data="remt"))
async def remt(event):  
    await event.delete()
    await rem_thumbnail(event)
    
@Drone.on(events.callbackquery.CallbackQuery(data="restart"))
async def res(event):
    if not f'{event.sender_id}' == f'{int(AUTH_USERS)}':
        return await event.edit("Only authorized user can restart!")
    result = await heroku_restart()
    if result is None:
        await event.edit("You have not filled `HEROKU_API` and `HEROKU_APP_NAME` vars.")
    elif result is False:
        await event.edit("An error occured!")
    elif result is True:
        await event.edit("Bot 1 daqiqada qayta yuklanadi.")
