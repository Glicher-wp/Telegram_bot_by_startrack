import datetime
import os
import pytz


# Токен приложения трекера.
YANDEX_TOKEN = os.environ.get('YANDEX_TOKEN')

# Адрес апи трекера
api_url = 'https://st-api.yandex-team.ru/v2/'

# Фильтр возвращает задачи юзера в конкретной очереди, которые открыты.
# PCR в первой строке - это код очереди, в которой будут искаться задачи
issue_filter = 'issues?filter=queue:PCR&' \
               f'filter=assignee:me()&' \
               f'filter=status:open&'

# Задаем таймзону и время, чтобы отфильтровать новые задачи за последние 20 минут.
tz = pytz.timezone("Europe/Moscow")
twenty_min_past = datetime.datetime.now(tz) - datetime.timedelta(minutes=20)

# Фиксируем формат времени.
time_format = "%Y-%m-%dT%H:%M:%S.%f%z"

# Токен телеграмм бота.
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
