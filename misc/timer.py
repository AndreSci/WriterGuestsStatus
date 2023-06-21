import datetime
from misc.consts import DEBUG_MODE


def timer_function_async(function):
    """ Декоратор для подсчета времени выполнения функции.\n
    Не забывает учитывать тот факт, что функции в асинхронном стиле\n
    могут ждать свою очередь на выполнение, от чего может быть\n
    завышенное время выполнения."""

    async def wrapped(*args):
        if DEBUG_MODE:
            start_time = datetime.datetime.now()
            res = await function(*args)

            end_time = datetime.datetime.now()
            delta_time = (end_time - start_time).total_seconds()
            print(f"Скорость работы функции {function.__name__}: {delta_time} секунд.")
        else:
            res = await function(*args)

        return res

    return wrapped


def timer_function(function):
    """ Декоратор для подсчета времени выполнения функции """

    def wrapped(*args):
        if DEBUG_MODE:
            start_time = datetime.datetime.now()
            res = function(*args)

            end_time = datetime.datetime.now()
            delta_time = (end_time - start_time).total_seconds()
            print(f"Скорость работы функции {function.__name__}: {delta_time} секунд.")
        else:
            res = function(*args)

        return res

    return wrapped
