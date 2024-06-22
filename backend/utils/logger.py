"""
Custom logging utilities
"""
from __future__ import annotations

import os
import inspect
import datetime

def resolve_caller() -> str:
    """
    Resolves the module name of the python module that called the function that this function is used in.

    For example, if the function `foo` is called from module main.py, and this function is called inside of `foo`,
    then the returned value will be "main.py"
    """
    frame = inspect.stack()[2]
    return frame.filename.split("\\")[-1]

class LogFile:
    """
    Encapsulates the functionality needed to handle a custom logging file
    Implements a log buffer to ensure that only relevant messages are committed to
    the file when `save_buffer` is called
    """

    write_path: str
    log_message_buffer: list[str]

    def __init__(self, path: str) -> None:
        self.write_path = path
        self.log_message_buffer = []

    def save_buffer(self) -> None:
        """
        Write the contents of the log buffer to the log file specified
        when this `LogFile` was initialised
        """
        if not self.log_message_buffer:
            return

        with open(self.write_path, "w+", encoding='utf-8') as f:
            f.write(''.join(self.log_message_buffer))

        self.log_message_buffer = []

    def write_message_to_buffer(self,
                                message: str,
                                level: str,
                                calling_module: str,
                                start: chr = '',
                                end: chr = '\n') -> None:
        """
        Writes a single log message to the buffer. Has different behaviours depending on the format of the message.

        If the log message being added has `\\r` as its end char (as opposed to `\\n`) then, given that the top of the log buffer
        also contains a `\\r`, the top of the log buffer will be replaced with the new message, simulating how `\\r` would work
        in the console when logging verbosely

        Args:
            message (str): the log message to add to the buffer.
            level (str): the log level (INFO, DEBUG etc.) of the message.
            calling_module (str): the name of the module from which the log call originated from.
            start (char): the start character of the message.
            end (char): the end char of the message.
        """

        # Create the log message
        parsed_message = f"{start}[{level}] [{calling_module}] {message}{end}"

        # Replace the last added message if the usage of \r would naturally overwrite it
        if end == '\r' and "\r" in self.log_message_buffer[-1]:
            self.log_message_buffer[-1] = parsed_message
        else:
            self.log_message_buffer.append(parsed_message)

class Logger:
    """
    Implements static methods to
    """
    loggers: dict[str, Logger] = {}
    log_file: LogFile = None
    print_to_stdout: bool = False

    @staticmethod
    def get_logger() -> Logger:
        """
        Gets the logger corresponding to the module this function is called in\n
        For example, calling `get_logger()` in `main.py` would give you a logger that logs in the format `[INFO][main.py] <message>`

        Returns:
            (Logger): A logger that will log to the file with information about the module this function is called from
        """

        module_caller = resolve_caller()

        # Create logger if it does not already exists
        if module_caller not in Logger.loggers:
            Logger.loggers.update({module_caller: Logger(module_caller)})

        # Return the given logger
        return Logger.loggers[module_caller]

    @staticmethod
    def init(log_dir: str, name: str, stdout: bool = False) -> None:
        """Initialises the logging module to output logs to the given log directory, using the name of the log file given.
        Will also output all log messages to the standard output if the `stdout` flag

        Args:
            log_dir (str): the directory to output the log files to.
            name (str): the name of the log files to use.
            stdout (bool, optional): whether to print the log messages to the standard output (as well as to the file). Defaults to False.
        """

        # Create directory
        if not os.path.isdir(log_dir):
            os.mkdir(log_dir)

        # Initialise static attributes
        Logger.log_file = LogFile(os.path.join(log_dir, name + '-log-{date:%Y-%m-%d_%H-%M-%S}.log'.format(date=datetime.datetime.now())))
        Logger.print_to_stdout = stdout

        # Ensure that the log file is written when the program terminates
        import atexit
        atexit.register(Logger.write)

    @staticmethod
    def write() -> None:
        """Writes the contents of the currently owned `LogFile` to the file path specified when the logger
        was initialised
        """
        if Logger.log_file:
            Logger.log_file.save_buffer()

    def __init__(self, module_caller: str) -> None:
        self.caller = module_caller

    def __parse_message(self, message: str, level: str, start: chr, end: chr, color: str = "") -> None:
        """Writes the message to the log buffer if applicable, and prints to the standard output if applicable
        Also allows for the temporary changing of the print colour for things like warnings and errors

        Args:
            message (str): the message to log.
            level (str): the level (INFO, DEBUG etc).
            start (chr): the start character of the message.
            end (chr): the ending character of the message.
            color (str, optional): an optional colour value to change the display colour of the message. Defaults to "".
        """
        # Write to message buffer
        if Logger.log_file:
            Logger.log_file.write_message_to_buffer(message, level, self.caller, start=start, end=end)

        # Print to standard output if applicable
        if Logger.print_to_stdout:
            print(color + f"{start}[{level}] [{self.caller}] {message}" + "\033[0m", end=end)

    def log_info(self, message: str, start: chr = '', end: chr = '\n') -> None:
        """Logs an info message to the log file, and the standard output if applicable

        Args:
            message (str): the message to log to the buffer.
            start (chr, optional): the start character. Defaults to ''.
            end (chr, optional): the end character. Defaults to '\n'.
        """
        self.__parse_message(message, "INFO", start, end)

    def log_warn(self, message: str, start: chr = '', end: chr = '\n') -> None:
        """Logs a warning message to the log file, and the standard output if applicable

        Args:
            message (str): the message to log to the buffer.
            start (chr, optional): the start character. Defaults to ''.
            end (chr, optional): the end character. Defaults to '\n'.
        """
        self.__parse_message(message, "WARN", start, end, color="\033[93m")

    def log_error(self, message: str, start: chr = '', end: chr = '\n') -> None:
        """Logs an error message to the log file, and the standard output if applicable

        Args:
            message (str): the message to log to the buffer.
            start (chr, optional): the start character. Defaults to ''.
            end (chr, optional): the end character. Defaults to '\n'.
        """
        self.__parse_message(message, "ERROR", start, end, color="\033[91m")

    def describe(self, log_description: str) -> callable:
        """Function decorator that can be used to automatically log when a function is called, as well as the
        parameters passed into it

        Args:
            log_description (str): Description of the function to be logged each time the function is called

        Returns:
            callable: decorator function
        """
        def decorator_log(func):
            def wrapper(*args, **kwargs):
                message = log_description + f" [args: {args} kwargs: {kwargs}]"
                self.log_info(message)
                result = func(*args, **kwargs)
                return result
            return wrapper
        return decorator_log

