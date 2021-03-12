import datetime
import os
import pytz


# Токен приложения трекера.
YANDEX_TOKEN = os.getenv('YANDEX_TOKEN')

# Адрес апи трекера
api_url = 'https://st-api.yandex-team.ru/v2/'

# Фильтр возвращает задачи юзера в конкретной очереди, которые открыты.
# PCR в первой строке - это код очереди, в которой будут искаться задачи
issue_filter = ('issues?filter=queue:PCR&'
                'filter=assignee:me()&'
                'filter=status:open&')

# Задаем таймзону и время, чтобы отфильтровать новые задачи за последние 20 минут.
tz = pytz.timezone("Europe/Moscow")
twenty_min_past = datetime.datetime.now(tz) - datetime.timedelta(minutes=20)

# Фиксируем формат времени.
time_format = "%Y-%m-%dT%H:%M:%S.%f%z"
comfortable_format = "%H:%M:%S %d.%m.%Y (%Z)"

# Токен телеграмм бота.
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


def time_remain(fail_data: datetime.datetime):
    """
    Получает поле date-time парсит его и воз
    """
    if fail_data.astimezone(tz) <= datetime.datetime.now(tz):
        formated_time = "Все сгорело в синем пламени"
        return formated_time
    time = fail_data.astimezone(tz) - datetime.datetime.now(tz)
    mm, ss = divmod(time.seconds, 60)
    hh, mm = divmod(mm, 60)
    if hh > 0:
        formated_time = "%s ч. %s мин. %s сек." % (hh, mm, ss)
    elif hh == 0 and mm > 0:
        formated_time = "%s мин. %s сек." % (mm, ss)
    elif hh == 0 and mm == 0:
        formated_time = "%s сек." % ss
    else:
        formated_time = "Все сгорело в синем пламени"
    return formated_time
