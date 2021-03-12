from datetime import datetime, timedelta
from loguru import logger
import requests
from requests import exceptions
from config import api_url, issue_filter, twenty_min_past, time_format, tz


logger.add('logs.json', format='{time} {level} {message}',
           level='INFO', rotation='50 KB', compression='zip', serialize=True)


@logger.catch
def get_headers(token: str):
    """
    Функция принимает token пользователя и возвращает заголовок для дальнейшей работы с  api.
    """
    # Подставляем полученный от юзера токен в заголовок авторизации.
    headers = {'Authorization': f'OAuth {token}'}
    # Делаем запрос к странице пользователя, чтобы проверить ответ
    try:
        r = requests.get(api_url+'myself', headers=headers)
    except UnicodeDecodeError:
        logger.warning("Токен не декодируется. Скорее всего использованы не латинские буквы")
        return None
    # Если ответ положительный, token указан правильно и мы можем с ним работать.
    if r.status_code == 200:
        return headers
    else:
        logger.warning(f"Сервер вернул плохой статус код: {r.status_code}")
        return None


@logger.catch
def get_user_issues(headers: dict):
    """
    Функция фильтрует задачи по юзеру и возвращает список задач.
    """

    # Осуществляем запрос к api.
    try:
        res_issues = requests.get(api_url + issue_filter, headers=headers)
    except AttributeError:
        logger.exception("Неправильный формат. Адрес должен быть строкой! header - dict!")
        return None
    except exceptions.InvalidHeader:
        logger.exception("Значение заголовка должно быть строкой!")
        return None
    if res_issues.status_code == 200:
        # Переводим в формат json, чтобы легче было парсить
        response_issues = res_issues.json()
        return response_issues
    else:
        logger.warning(f"Сервер вернул плохой статус код:{res_issues.status_code}")
        logger.warning(res_issues.text)
        return None


@logger.catch
def get_list_issues(list_of_issues: list):
    """
    Функция принимает список из задача в формате json. После чего фильтрует его по нужным полям и возвращает
    пользователю.
    """
    # Пустой список в который будут помещаться отформатированные задачи
    issues_list = []
    for issue in list_of_issues:
        try:
            issue_dict = {
                            "issue": issue['summary'],
                            "deadline": datetime.strptime(issue['sla'][0]['failAt'], time_format),
                            "warnAt": datetime.strptime(issue['sla'][0]['warnAt'], time_format),
                        }
            issues_list.append(issue_dict)
        except ValueError:
            logger.exception("Невалидно значение одного из полей")
            pass
        except KeyError:
            logger.exception("Яндекс вернул json с невалидными ключами")
            pass
    return issues_list


@logger.catch
def filter_issues_by_time(list_of_issues: list):
    """
    Функция фильтрует задачи по юзеру и времени и возвращает обновления за последние 20 миинут.
    """
    try:
        filtered_issues = list(filter(
            lambda x: (
                datetime.strptime(x['createdAt'], time_format) >= twenty_min_past or
                datetime.strptime(x['updatedAt'], time_format) >= twenty_min_past) or
                datetime.strptime(x['sla'][0]['failAt'], time_format) - timedelta(hours=4) <=
                datetime.now(tz) <=
                datetime.strptime(x['sla'][0]['failAt'], time_format) - timedelta(minutes=210),
            list_of_issues
        ))
    except KeyError:
        logger.exception("Яндекс вернул json с невалидными ключами. Фмльтрация невозможна")
        filtered_issues = []
    return filtered_issues


def get_issues(token: str):
    """
    Общая функция, получающая токен и возвращающая список всех задач этого юзера.
    """
    headers = get_headers(token)
    # Проверка, что юзер был найден. Если в системе нет такого email адреса, возвращает None.
    if headers is None:
        logger.info("Функция get_header вернула None. Похоже передали невалидный токен")
        return None
    issues_list = get_user_issues(headers)
    if issues_list is None:
        logger.info("От сервера вернулся плохой ответ. Возможны проблемы на сервере")
        return None
    issues = get_list_issues(issues_list)
    return issues


def get_latest_issues(token: str):
    """
    Общая функция, получающая email и возвращающая список новых задач за последние 20 минут.
    """
    headers = get_headers(token)
    # Проверка, что юзер был найден. Если в системе нет такого email адреса, возвращает None.
    if headers is None:
        logger.info("Функция get_header вернула None. Похоже передали невалидный токен")
        return None
    issues_list = get_user_issues(headers)
    if issues_list is None:
        logger.info("От сервера вернулся плохой ответ. Возможны проблемы на сервере")
        return None
    filtered_issues = filter_issues_by_time(issues_list)
    issues = get_list_issues(filtered_issues)
    return issues
