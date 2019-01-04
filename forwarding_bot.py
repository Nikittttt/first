import time
import sqlite3
import logging
import asyncio
import vk
import aiohttp
from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_polling

token_vk = token_vk
api = vk.API(vk.Session())
token_telegram = token_telegram
PROXY_URL = 'http://...:...'

logging.basicConfig(level=logging.INFO)
loop = asyncio.get_event_loop()
bot = Bot(token=token_telegram, loop=loop, proxy=PROXY_URL)
dp = Dispatcher(bot)

# работа с базой данной
conn = sqlite3.connect("time.db")
cursor = conn.cursor()

# эта часть нужна только в случае частого переноса кода или удаления базы данных дабы не создавать её отдельно
try:
    cursor.execute("""CREATE TABLE all_time
                  (delta_time integer)
                   """)
except sqlite3.OperationalError:
    pass


# соединение с proxy
async def fetch(url, proxy=None, proxy_auth=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxy, proxy_auth=proxy_auth) as response:
            return await response.text()


# запуск адомашины посредством отправки команды start секретному боту(он позже и будет отсылать сообщения из вк в тг)
@dp.message_handler(commands=['start'])
async def cmd_start(message):

    # вечный цикл для постоянного отлавливания сообщений
    while True:

        # берём данные со стены интересующего нас сообщества
        wall = api.wall.get(extended=1, owner_id='owner_id', domain='domain', count=2,
                            access_token=access_token,
                            v='5.60')

        # проверка на то закреплено ли это сообщение

        message_number = 0
        try:
            if wall['items'][0]['is_pinned'] == 1:
                message_number = 1
        except Exception:
                message_number = 0

        # сравниваем время публиказии последнего не запиненого сообщения и последнего сообщения в базе
        new_time = wall['items'][message_number]['date']
        sql = "SELECT * FROM all_time WHERE delta_time=?"
        cursor.execute(sql, [new_time])
        last_time = cursor.fetchone()

        # ожидаем до следующего нового сообщения
        if new_time in last_time:
            time.sleep(10)
        else:

            # отправляем сообщение на канал в тг и заменяем время публикации в базе
            await bot.send_message(chat_id='@chat_id', text=wall['items'][message_number]['text'])
            sql = "DELETE FROM all_time WHERE ('%s')" % last_time
            cursor.execute(sql)
            conn.commit()
            cursor.execute("INSERT INTO all_time VALUES ('%s')" % new_time)
            conn.commit()


if __name__ == '__main__':
    start_polling(dp, loop=loop, skip_updates=True)
