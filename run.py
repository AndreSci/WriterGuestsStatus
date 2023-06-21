from misc.utility import SettingsIni
import ctypes
import asyncio
from misc.consts import ConstsControlClass


def main():

    # Подгружаем данные из settings.ini
    settings = SettingsIni()
    result = settings.create_settings()

    fail_col = '\033[91m'
    # end_c = '\033[0m'

    # Проверка успешности загрузки данных
    if not result["result"]:
        print(f"{fail_col}")
        print(f"Ошибка запуска сервиса - {result['desc']}")
        input()
        raise Exception("Service error")

    # Обновляем константы host, port и путь для логирования для socket
    main_host, main_port = settings.take_main_host_port()
    ConstsControlClass.change_main_host_port(main_host, main_port)
    ConstsControlClass.change_log_path(settings.take_log_path())
    ConstsControlClass.change_reload_issues(settings.take_reload_issues())

    # Меняем имя терминала
    ctypes.windll.kernel32.SetConsoleTitleW(f"WriterGuestsStatus (ver. win64 async)")

    # Для обновления констант в файле misc.consts.py
    from main import start

    # ЗАПУСК СЕРВИСА
    asyncio.run(start())


if __name__ == '__main__':
    main()
