import exceptions
import logging
import os
import sys
import telegram
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

logging.basicConfig(
    handlers=[logging.FileHandler(filename='./project7.log',
                                  encoding='utf-8', mode='w'),
              logging.StreamHandler(stream=sys.stdout)],
    format='%(asctime)s, %(levelname)s, %(message)s, %(funcName)s, %(lineno)s',
    level=logging.INFO
)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        logging.info(f'Отправка сообщения в {TELEGRAM_CHAT_ID}: {message}')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f'Сообщение отправлено в {TELEGRAM_CHAT_ID}: {message}')
    except telegram.error.TelegramError():
        raise exceptions.TelegramSendingError(
            f'Ошибка отправки сообщения в телеграм {TELEGRAM_CHAT_ID}'
        )


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-Яндекса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    logging.info('Подключение к API яндекса')
    try:
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS,
                                         params=params)
    except Exception:
        raise exceptions.ServerError(
            f'Ошибка подключения к API Яндекса: {ENDPOINT}'
            f'с параметрами: {params}'
        )
    if homework_statuses.status_code != HTTPStatus.OK:
        status_code = homework_statuses.status_code
        raise exceptions.InvalidHttpStatus(
            f'Ошибка при обращении к API Яндекса: {status_code}'
        )
    return homework_statuses.json()


def get_current_date(response, current_timestamp):
    """Проверяет current_date в ответе API."""
    if 'current_date' not in response:
        raise exceptions.HomeworkOrTimestampIsEmpty('Отсутствует current_date')
    return response.get('current_date', current_timestamp)


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError(f'Неизвестный ответ API типа {type(response)}')
    if 'homeworks' in response:
        list_works = response['homeworks']
    else:
        raise exceptions.HomeworkOrTimestampIsEmpty('В ответе нет homeworks')
    if len(list_works):
        return list_works[0]
    else:
        raise IndexError('Нет проверенных проектов')


def parse_status(homework):
    """Извлекает статус домашней работы из информации о ней."""
    if 'homework_name' not in homework:
        raise KeyError('В ответе нет ключа homeworks_name')
    if 'status' not in homework:
        raise KeyError('В ответе нет ключа status')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise exceptions.UnknownStatusOfWork(
            f'Неизвестный статус работы: {homework_status}'
        )
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Главный модуль работы бота."""
    if not check_tokens():
        logging.critical('Отсутствуют одна или несколько переменных окружения')
        sys.exit('Отсутствуют одна или несколько переменных окружения')

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    prev_status = ''
    error_cache_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = get_current_date(response, current_timestamp)
            message = parse_status(check_response(response))
            if message != prev_status:
                send_message(bot, message)
                prev_status = message
        except Exception as error:
            logging.error(error)
            message_t = str(error)
            if message_t != error_cache_message:
                send_message(bot, message_t)
                error_cache_message = message_t
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
