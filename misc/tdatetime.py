import struct
import datetime

DELPHI_EPOCH = datetime.datetime(1899, 12, 30)


def datetime_from_delphi(d_value):
    return DELPHI_EPOCH + datetime.timedelta(days=d_value)


class DateTimeConverter:

    @staticmethod
    def convert_datetime(byte_code):
        """ Конвертирует байт-код в полноценную дату по типу datetime """
        d_value = struct.unpack('d', byte_code)[0]

        return datetime_from_delphi(d_value)
