import asyncio
import logging
import aiohttp
import sqlite3
from datetime import timedelta
from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_polling

GROUP_ID = GROUP_ID
API_TOKEN = API_TOKEN
PROXY_URL = 'http://...:...'

# работа с базой данной
conn = sqlite3.connect("ban_dict.db")
cursor = conn.cursor()

# эта часть нужна только в случае частого переноса кода или удаления базы данных дабы не создавать её отдельно
try:
    cursor.execute("""CREATE TABLE dict_of_ban
                  (id integer)
                   """)
except sqlite3.OperationalError:
    pass

logging.basicConfig(level=logging.INFO)
loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop, proxy=PROXY_URL)
dp = Dispatcher(bot)


# соединение с базой данных
async def fetch(url, proxy=None, proxy_auth=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxy, proxy_auth=proxy_auth) as response:
            return await response.text()


@dp.message_handler(func=lambda message: message.entities is not None and message.chat.id == GROUP_ID)
async def cmd_start(message):
    for entity in message.entities:

        # запись username для дальнейшего обращения к нему
        if message.from_user.username is None:
            username = message.from_user.first_name
        else:
            username = "@" + message.from_user.username

        # определения времени бана, в моём случае это 31 день
        time = timedelta(days=31)

        # проверка на наличие ссылки
        if entity.type in ("url", "text_link"):

            # получение данных о участнике(id и информацию о нём)
            userid = message.from_user.id
            chat_member = await bot.get_chat_member(message.chat.id, userid)

            # проверка статуса участника
            if (chat_member.status == "administrator") or (chat_member.status == "creator"):
                pass
            else:

                # проверка на наличие id в базе данных
                sql = "SELECT * FROM dict_of_ban WHERE id=?"
                cursor.execute(sql, [userid])
                all_id = cursor.fetchone()

                # предупреждение в случае отсутствия в базе
                if userid not in all_id:
                    await bot.send_message(text="%s, не надо сюда кидать рекламу)" % username, chat_id=message.chat.id)
                    cursor.execute("INSERT INTO dict_of_ban VALUES ('%s')" % userid)
                    conn.commit()

                # бан на заранее обозначенный срок в случае наличия в базе
                else:
                    sql = "DELETE FROM dict_of_ban WHERE ('%s')" % userid
                    cursor.execute(sql)
                    conn.commit()
                    await bot.send_message(text="%s, я предупреждал)" % username, chat_id=message.chat.id)
                    await bot.kick_chat_member(message.chat.id, message.from_user.id, until_date=time)
                await bot.delete_message(message.chat.id, message.message_id)
        else:
            return

# закрытия соединения с базой данных нет
if __name__ == '__main__':
    start_polling(dp, loop=loop, skip_updates=True)
