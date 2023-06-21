from misc.logger import Logger
import datetime

DEBUG_MODE = False
LOGGER = Logger()

MAIN_HOST = '192.168.0.9'
MAIN_PORT = 7050
DECODE = 'cp1251'

RELOAD_ISSUES = 1200

CARD_NUMBERS_ISSUE = []

ENTER_WORDS = ['ВХОД', 'ВЪЕЗД', "ПОДЪЕЗД"]
EXIT_WORDS = ['ВЫХОД', 'ВЫЕЗД', 'КАРТОПРИЕМНИК']
ENTER_INT = 5  # Вход осуществлён
EXIT_INT = 6  # Выход осуществлён


class ConstsControlClass:
    @staticmethod
    def change_log_path(path: str):
        global LOGGER
        LOGGER.log_path = path

    @staticmethod
    def change_reload_issues(reload_issues: int):
        global RELOAD_ISSUES
        RELOAD_ISSUES = int(reload_issues)

    @staticmethod
    def change_main_host_port(host, port):
        global MAIN_HOST
        global MAIN_PORT

        MAIN_PORT = int(port)
        MAIN_HOST = str(host)


class TPassClass:
    """ Вид структуры из буфера """
    chTypePass: str  # 64 байта
    chObjName: str  # 64 байта
    chHolderName: str  # 64 байта
    dwCardNumber: int  # 4 байта
    # UnknownType: неизвестные данные 4 байта
    dtRealTimePass: datetime.datetime  # 8 байта

    def __str__(self):
        return f"=================================================\n" \
               f"DateTime: {datetime.datetime.now()}\n" \
                f"- chTypePass: {self.chTypePass}\n" \
                f"- chObjName: {self.chObjName}\n" \
                f"- chHolderName: {self.chHolderName}\n" \
                f"- dwCardNumber: {self.dwCardNumber}\n" \
                f"- dtRealTimePass: {self.dtRealTimePass}"
