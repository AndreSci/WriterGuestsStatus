import asyncio
import configparser
import os
import threading

import aiomysql

from misc.logger import Logger

LOCK_TH_INI = threading.Lock()

loop = asyncio.get_event_loop()

ASYNC_CONNECTION = aiomysql.Connection()


def take_db_settings(db_name: str, logger: Logger):
    """ Функция загружает данные из settings.ini """
    conn_inf = dict()

    settings_file = configparser.ConfigParser()

    if os.path.isfile("./settings.ini"):
        try:
            with LOCK_TH_INI:  # Блокируем потоки
                settings_file.read("settings.ini", encoding="utf-8")

            conn_inf['host'] = str(settings_file[db_name]["HOST"])
            conn_inf['user'] = str(settings_file[db_name]["USER"])
            conn_inf['password'] = str(settings_file[db_name]["PASSWORD"])
            conn_inf['charset'] = str(settings_file[db_name]["CHARSET"])

        except Exception as ex:
            logger.add_log(f"ERROR\ttake_db_settings\tОшибка чтения из settings.ini: {ex}")
            conn_inf = dict()
    else:
        logger.add_log(f"ERROR\ttake_db_settings\tФайл settings.ini не найден в корне API")

    return conn_inf


# Для БД с асинхронным соединением
async def connect_db_async(logger: Logger):
    global ASYNC_CONNECTION

    if ASYNC_CONNECTION.closed:
        conn_inf = take_db_settings("DATABASE", logger)

        ASYNC_CONNECTION = await aiomysql.connect(host=conn_inf['host'],
                                                  user=conn_inf['user'],
                                                  password=conn_inf['password'],
                                                  charset=conn_inf['charset'],
                                                  loop=loop)
        logger.add_log(f"EVENT\tconnect_db_async\tУстановлено соединение с БД")
    return ASYNC_CONNECTION


# Для БД с асинхронным соединением (отдельный метод для получения списка пропусков)
# Из разных ветвей асинхронных обращений может вызвать коллизию
async def connect_db_async_for_take_all(logger: Logger):

    conn_inf = take_db_settings("DATABASE", logger)

    pool = await aiomysql.connect(host=conn_inf['host'],
                                              user=conn_inf['user'],
                                              password=conn_inf['password'],
                                              charset=conn_inf['charset'],
                                              loop=loop)

    return pool
