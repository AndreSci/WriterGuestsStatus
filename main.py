import asyncio
import socket
import queue
import time

from misc.consts import MAIN_PORT, MAIN_HOST, DECODE, LOGGER, TPassClass, RELOAD_ISSUES, ENTER_INT
from misc.tdatetime import DateTimeConverter
from database.requests.guests import GuestClass


TPASS_QUEUE = queue.Queue()
TPASS_ALL_DB = list()


async def get_buffer(socket_main: socket) -> bool:
    """ Метод выгрузки данных из буфера и структурирования """
    global TPASS_QUEUE

    t_pass = TPassClass()

    try:
        # Выгружаем буфер сокета
        data1 = socket_main.recv(64)
        data2 = socket_main.recv(64)
        data3 = socket_main.recv(64)
        data4 = socket_main.recv(4)
        data5 = socket_main.recv(4)
        data6 = socket_main.recv(8)

        # Заполняем структуру с манипуляциями данных из буфера
        t_pass.chTypePass = data1.decode(DECODE).strip().strip('\x00')  # Убираем нулевые данные

        if "TAp" != t_pass.chTypePass[:3]:
            # Если не равно есть вероятность, что произошло смещение получение из буфера
            # возвращаем False для переподключения к Socket.
            LOGGER.add_log(f"WARNING\tget_buffer\tДанные: {t_pass.chTypePass}")
            return False

        if "Access_Granted" in t_pass.chTypePass:
            t_pass.chObjName = data2.decode(DECODE).strip().strip('\x00')  # Убираем нулевые данные
            t_pass.chHolderName = data3.decode(DECODE).strip().strip('\x00')  # Убираем нулевые данные

            data4 = bytearray(data4)
            data4.reverse()
            data4 = bytes(data4)

            t_pass.dwCardNumber = int.from_bytes(data4, byteorder='big')  # Приобразуем байт значение в число
            t_pass.dtRealTimePass = \
                DateTimeConverter.convert_datetime(data6)  # Получаем из double(дельта от 1899\12\30)

            # Добавляем в очередь для дальнейшей обработки.
            TPASS_QUEUE.put(t_pass)

        await asyncio.sleep(0.03)

    except Exception as ex:
        print(f"EXCEPTION\tmain.get_buffer()\tОшибка получения данных из буфера: {ex}")
        return False

    return True


async def update_issue(do_once=False):
    """ Обновляем список существующих заявок из БД """
    global TPASS_ALL_DB
    while True:

        result = await GuestClass.take_all_issue_as(LOGGER)

        if result['RESULT'] == "SUCCESS":
            print(f"=================================================\n"
                  f"Частота обновления списка раз в {RELOAD_ISSUES / 60} мин.\n"
                  f"Получены новые записи из БД: кол-во {len(result['DATA'])}")
            TPASS_ALL_DB = result['DATA']
        # elif result['RESULT'] == "WARNING":
        #     print(f"=================================================\n"
        #           f"{result['DESC']}")
        # else:
        #     print(result)

        if do_once:
            break

        await asyncio.sleep(RELOAD_ISSUES)


async def update_database():
    """ Метод получения данных из БД для быстрого поиска пропуска """
    global TPASS_QUEUE
    global TPASS_ALL_DB

    while True:
        if TPASS_QUEUE.qsize() > 0:
            t_pass = TPASS_QUEUE.get()
            # print(t_pass)
            if TPASS_ALL_DB.count(t_pass.dwCardNumber):
                print(t_pass)
                ret_1 = await GuestClass.take_id_request_async(t_pass.dwCardNumber, LOGGER)

                if ret_1['RESULT'] == "SUCCESS":
                    id_request = ret_1['DATA']

                    ret_2 = await GuestClass.add_status_async(id_request, t_pass, LOGGER)

                    if ret_2['RESULT'] == "SUCCESS":
                        status_name = "Выход осуществлён"
                        if ret_2['DATA']['status'] == ENTER_INT:
                            status_name = "Вход осуществлён"

                        print(f"Статус добавлен в БД: {t_pass.dwCardNumber} - {status_name}")

        # Даем другим в очереди пройди
        await asyncio.sleep(0.001)


async def connection_socket():
    """ Функция подключения и получения данных из сокета """
    while True:
        try:
            LOGGER.add_log(f"EVENT\tmain.connection_socket\t"
                           f"Попытка подключения к Socket: host({MAIN_HOST}) port({MAIN_PORT})")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_main:

                socket_main.connect_ex((MAIN_HOST, MAIN_PORT))

                LOGGER.add_log(f"EVENT\tmain.connection_socket\tУспешное подключение к Socket.")

                while True:
                    # Выгружаем буфер если False завершаем цикл и пере-подключаемся
                    if not await get_buffer(socket_main):
                        break

        except Exception as ex:
            LOGGER.add_log(f"EXCEPTION\tmain.connection_socket\t"
                            f"Ошибка при работе с буфером: {ex}")
            time.sleep(2)


async def start():
    """ Создаем асинхронное ядро программы """
    await update_issue(True)
    await asyncio.gather(update_issue(), update_database(), connection_socket())

    print("НЕ МОЖЕТ БЫТЬ, ПО КАКОЙ ТО ПРИЧИНЕ ОСТАНОВИЛСЯ ОСНОВНОЙ ЦИКЛ В ПРОГРАММЕ!!!")

if __name__ == "__main__":
    asyncio.run(start())
