from __future__ import annotations
import os
import datetime
import inspect


def resolve_caller():
    frame = inspect.stack()[2]
    return frame.filename.split("\\")[-1]


class LogFile:

    def __init__(self, path: str) -> None:
        self.write_path = path
        self.log_message_buffer = []

    def save_buffer(self) -> None:
        """
        Save buffer to file
        """
        if not self.log_message_buffer:
            return

        with open(self.write_path, "w+", encoding='utf-8') as f:
            f.write(''.join(self.log_message_buffer))

    def write_message_to_buffer(self,
                                message: str,
                                level: str,
                                calling_module: str,
                                start: chr = '',
                                end: chr = '\n') -> None:
        parsed_message = f"{start}[{level}] [{calling_module}] {message}{end}"
        if end == '\r' and "\r" in self.log_message_buffer[-1]:
            self.log_message_buffer[-1] = parsed_message
        else:
            self.log_message_buffer.append(parsed_message)

class Logger:

    loggers: dict[str, Logger] = {}
    log_file: LogFile = None
    print_to_stdout: bool = False

    @staticmethod
    def get_logger() -> Logger:
        module_caller = resolve_caller()
        if module_caller not in Logger.loggers:
            Logger.loggers.update({module_caller: Logger(module_caller)})
        return Logger.loggers[module_caller]

    @staticmethod
    def init(log_dir: str, name: str, stdout: bool = False):
        if not os.path.isdir(log_dir):
            os.mkdir(log_dir)
        Logger.log_file = LogFile(os.path.join(log_dir, name + '-log-{date:%Y-%m-%d_%H-%M-%S}.log'.format(date=datetime.datetime.now())))
        Logger.print_to_stdout = stdout

        import atexit
        atexit.register(Logger.write)

    @staticmethod
    def write() -> None:
        if Logger.log_file:
            Logger.log_file.save_buffer()

    def __init__(self, module_caller: str) -> None:
        self.caller = module_caller

    def __parse_message(self, message: str, level: str, start: chr, end: chr, color: str = "") -> None:
        if Logger.log_file:
            Logger.log_file.write_message_to_buffer(message, level, self.caller, start=start, end=end)
        if Logger.print_to_stdout:
            print(color + f"{start}[{level}] [{self.caller}] {message}" + "\033[0m", end=end)

    def log_info(self, message: str, start: chr = '', end: chr = '\n') -> None:
        self.__parse_message(message, "INFO", start, end)

    def log_warn(self, message: str, start: chr = '', end: chr = '\n') -> None:
        self.__parse_message(message, "WARN", start, end, color="\033[93m")

    def log_error(self, message: str, start: chr = '', end: chr = '\n') -> None:
        self.__parse_message(message, "ERROR", start, end, color="\033[91m")

    def describe(self, log_description: str) -> callable:
        def decorator_log(func):
            def wrapper(*args, **kwargs):
                message = log_description + f" [args: {args}, kwargs: {kwargs}]"
                self.log_info(message)
                result = func(*args, **kwargs)
                return result
            return wrapper
        return decorator_log

