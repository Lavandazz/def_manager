import logging
import os

from colorlog import ColoredFormatter


class BaseLogger:
    """ Базовый класс логгера """

    def __init__(self, name: str, log_file: str, logging_level=logging.INFO):
        self.name = name
        self.log_file = log_file
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging_level)  # настройка уровня логирования

        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """ Настройка обработчиков """
        # 1. Цветной вывод в консоль
        console_handler = logging.StreamHandler()
        console_formatter = ColoredFormatter(
            '%(log_color)s%(levelname)-8s%(reset)s %(asctime)s [%(name)s] '
            '(%(filename)s).%(funcName)s(%(lineno)d) %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(console_formatter)

        # 2. Простой вывод в файл (без цветов)
        file_handler = logging.FileHandler(self.log_file, mode='a')
        file_formatter = logging.Formatter(
            '%(levelname)-8s %(asctime)s [%(name)s] '
            '(%(filename)s).%(funcName)s(%(lineno)d) %(message)s'
        )
        file_handler.setFormatter(file_formatter)

        # Добавляем обработчики
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.propagate = False  # чтобы aiogram не перекрывал логи, иначе видно только логи мидлваров

        # Логируем успешную настройку
        self.logger.info(f"Логирование для '{self.name}' настроено успешно.")

    def get_logger(self):
        """Возвращает настроенный логгер"""
        return self.logger


class RegisterLogger(BaseLogger):
    """Логгер для бота"""

    def __init__(self):
        log_folder = "logs"
        os.makedirs(log_folder, exist_ok=True)
        log_file = os.path.join(log_folder, "bot_logs.log")
        super().__init__(name="register_logger", log_file=log_file, logging_level=logging.DEBUG)


class AdminLogger(BaseLogger):
    """ Логгер для аи генератора"""
    def __init__(self):
        log_folder = "logs"
        os.makedirs(log_folder, exist_ok=True)
        log_file = os.path.join(log_folder, "phrase_logs.log")
        super().__init__(name="admin_logger", log_file=log_file, logging_level=logging.DEBUG)


class ProfileLogger(BaseLogger):
    """ Логгер для базы """
    def __init__(self):
        log_folder = "logs"
        os.makedirs(log_folder, exist_ok=True)
        log_file = os.path.join(log_folder, "db_logs.log")
        super().__init__(name="user_logger", log_file=log_file)


class DBLogger(BaseLogger):
    """ Логгер для базы """
    def __init__(self):
        log_folder = "logs"
        os.makedirs(log_folder, exist_ok=True)
        log_file = os.path.join(log_folder, "db_logs.log")
        super().__init__(name="user_logger", log_file=log_file)


class PostLogger(BaseLogger):
    """ Логгер для базы """
    def __init__(self):
        log_folder = "logs"
        os.makedirs(log_folder, exist_ok=True)
        log_file = os.path.join(log_folder, "db_logs.log")
        super().__init__(name="user_logger", log_file=log_file)


reg_logger = RegisterLogger().get_logger()
admin_logger = AdminLogger().get_logger()
profile_logger = ProfileLogger().get_logger()
db_logger = DBLogger().get_logger()
post_logger = PostLogger().get_logger()
