import re

import aiomysql

from misc.timer import timer_function_async
from misc.logger import Logger
from database.db_connection import connect_db_async, connect_db_async_for_take_all
from itertools import chain

from misc.consts import TPassClass, ENTER_WORDS, EXIT_WORDS, ENTER_INT, EXIT_INT

# Переменная хранит длину последней выгрузки из БД
LEN_TPASS_ALL_DB = 0
ASYNC_CONNECTION = None


def select_id_status(ch_obj_name: str) -> int:
    """ Функция определяет вход или выход """
    up_obj_name = ch_obj_name.upper()

    for it in ENTER_WORDS:
        if re.search(it, up_obj_name):
            return ENTER_INT

    for it in EXIT_WORDS:
        if re.search(it, up_obj_name):
            return EXIT_INT


class GuestClass:
    """ Класс отвечает за получения списка гостей, проверки его и добавление нового статуса гостя """

    @staticmethod
    @timer_function_async
    async def take_all_issue_as(logger: Logger) -> dict:
        """ Получаем список гостей """
        global LEN_TPASS_ALL_DB

        ret_value = {'RESULT': 'ERROR', 'DESC': '', 'DATA': list()}

        try:
            # Создаем подключение
            connection = await connect_db_async_for_take_all(logger)

            async with connection.cursor() as cur:

                await cur.execute(f"select count(*) from sac3.tguestcard")
                len_table = await cur.fetchone()

                if len_table[0] != LEN_TPASS_ALL_DB:

                    LEN_TPASS_ALL_DB = len_table[0]

                    # Проверяем номер на активность
                    await cur.execute(f"select FCardNumber from sac3.tguestcard group by FCardNumber")

                    result = await cur.fetchall()

                    if len(result) > 0:
                        # Получаем list(tuple()) и приобразуем его в единый список
                        ret_value['DATA'] = list(chain.from_iterable(result))
                        ret_value['RESULT'] = "SUCCESS"
                    else:
                        ret_value['DESC'] = "Сервер получил пустой список ISSUE"
                else:
                    ret_value['RESULT'] = "WARNING"
                    ret_value['DESC'] = f"Кол-во записей в таблице совпадает " \
                                        f"с кол-м последнего запроса: {LEN_TPASS_ALL_DB} == {len_table}"

            connection.close()

        except Exception as ex:
            logger.add_log(f"EXCEPTION\tGuestClass.take_all_issue_as\tИсключение вызвало: {ex}")
            ret_value['DESC'] = "Ошибка на сервере"

        return ret_value

    @staticmethod
    @timer_function_async
    async def take_id_request_async(card_number_issue: int, logger: Logger, reconnect=True) -> dict:
        """ Проверяем активность пропуска и получаем id request """

        global LEN_TPASS_ALL_DB

        ret_value = {'RESULT': 'ERROR', 'DESC': '', 'DATA': 0}

        try:
            # Создаем подключение
            connection = await connect_db_async(logger)

            async with connection.cursor() as cur:
                await cur.execute(f"select ID_Request_Issue from sac3.issue "
                                  f"where CardNumber_Issue = {card_number_issue} "
                                  f"and Active_Issue = 1 "
                                  f"order by ID_Issue desc limit 1")

                id_request_issue = await cur.fetchone()

                # Запрещаем переподключение если в дальнейшем будет ошибка
                reconnect = False

                if id_request_issue:
                    ret_value['RESULT'] = "SUCCESS"
                    ret_value['DATA'] = id_request_issue[0]

        except aiomysql.Connection.Error as wex:
            # Ошибка связана с разрывом соединения с БД, пробуем переподключиться
            logger.add_log(f"EXCEPTION\tGuestClass.take_id_request_async\t"
                           f"Исключение вызвало: {wex} (Входные данные: {card_number_issue})")

            if reconnect:
                # Запрещаем переподключение если в дальнейшем будет ошибка
                logger.add_log(f"EVENT\tGuestClass.take_id_request_async\tПопытка подключиться к БД")
                reconnect = False
                ret_value = await GuestClass.take_id_request_async(card_number_issue, logger, reconnect)

        except Exception as ex:
            logger.add_log(f"EXCEPTION\tGuestClass.take_id_request_async\tИсключение вызвало: {ex}")
            ret_value['DESC'] = "Ошибка на сервере"

        return ret_value

    @staticmethod
    @timer_function_async
    async def add_status_async(id_request: int, t_pass: TPassClass, logger: Logger, reconnect=True) -> dict:
        """ Добавляем новый статус гостя в БД """

        ret_value = {'RESULT': 'ERROR', 'DESC': '', 'DATA': {'status': 0}}

        try:
            id_request_status = select_id_status(t_pass.chObjName)
            # Создаем подключение
            connection = await connect_db_async(logger)

            async with connection.cursor() as cur:
                # Загружаем данные в базу
                await cur.execute(f"insert into sac3.requeststatus_status(ID_Request, "
                                    f"ID_RequestStatus, DateCreate) "
                                  f"values ({id_request}, {id_request_status}, '{t_pass.dtRealTimePass}')")
                await connection.commit()

                # Запрещаем переподключение если в дальнейшем будет ошибка (доп. перестраховка)
                reconnect = False

                result = cur.rowcount

                if result == 1:
                    ret_value['RESULT'] = "SUCCESS"
                    ret_value['DATA']['status'] = id_request_status

        except aiomysql.Connection.Error as wex:
            # Ошибка связана с разрывом соединения с БД, пробуем переподключиться
            logger.add_log(f"EXCEPTION\tGuestClass.change_status_async\t"
                           f"Исключение вызвало: {wex} (Входные данные: {id_request} - {t_pass})")

            if reconnect:
                logger.add_log(f"EVENT\tGuestClass.change_status_async\tПопытка подключиться к БД")
                # Запрещаем переподключение если в дальнейшем будет ошибка
                reconnect = False
                ret_value = await GuestClass.add_status_async(id_request, t_pass, logger, reconnect)

        except Exception as ex:
            logger.add_log(f"EXCEPTION\tGuestClass.change_status_async\t"
                           f"Исключение вызвало: {ex} (Входные данные: {id_request} - {t_pass})")
            ret_value['DESC'] = "Ошибка на сервере"

        return ret_value
