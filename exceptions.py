class InvalidHttpStatus(Exception):
    """Статут ответа от API Яндекс.Практикума отличный от 200."""    
    pass


class ServerError(Exception):
    """Ошибка при подключении к серверу Яндекс."""
    pass

class TelegramSendingError(Exception):
    """Ошибка отправки сообщения в телеграмм."""
    pass

class HomeworkOrTimestampIsEmpty(Exception):
    """Ошибка при отсутствии домашних работ или timestamp."""
    pass

class UnknownStatusOfWork(Exception):
    """Ошибка при неизвестном статусе домашней работы."""
    pass