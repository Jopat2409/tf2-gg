from __future__ import annotations
from typing import Optional, Any, Union

import json as js
import os
import io

from utils.logger import Logger

file_logger = Logger.get_logger()

def read_or_create( file: str,
                    default: dict = {},
                    cls: js.JSONDecoder = None) -> None:
    try:
        with open(file, "r", encoding='utf-8') as f:
            return js.load(f, cls=cls)
    except FileNotFoundError:
        with open(file, "w", encoding='utf-8') as f:
            js.dump(default, f)
    return default

def read_required(  file: str,
                    warn_not_exists: str = "",
                    warn_io_error: str = "",
                    json: bool = False,
                    encoding='utf-8',
                    throws: bool = False) -> Optional[str]:
    """
    Reads data from a `file` that MUST exist at read-time. Performs all necessary checks and error handling

    Args:
        file (str): the path to the file.
        warn_not_exists (str): message to log if the file does not exist.
        warn_io_error (str): message to log if the program encounters an error when reading.
        json (bool): whether to return the file as a json object. (defaults to str)
        encoding (str): file encoding. (default utf-8)
        throws (bool): whether this function should raise an exception on error or not.

    Returns:
        Optional[str]: The file data as a string, or as a json object if the `json` parameter is specified
    """

    if not os.path.isfile(file):
        file_logger.log_error(warn_not_exists or f"Error: File {file} does not exist")
        return None

    try:
        with open(file, 'r', encoding=encoding) as f:
            return js.load(f) if json else f.read()
    except Exception as e:
        file_logger.log_error(warn_io_error or f"""Error opening file "{file}", stacktrace:""")
        file_logger.log_error(e)
        if throws:
            raise e
    return None


def write_to_file(  path: str,
                    data: Any,
                    create: bool = True,
                    json: bool = False,
                    encoding='utf-8',
                    cls: js.JSONEncoder = js.JSONEncoder) -> None:

    if not os.path.isfile(path):
        if not create:
            file_logger.log_warn(f"Could not write data to file {path}, as file does not exist. If you want this file to be created, specify the create parameter")
            return
        with open(path, "x", encoding=encoding) as f:
            pass

    try:
        with open(path, "w", encoding=encoding) as f:
            js.dump(data, f, cls=cls) if json else f.write(str(data))
            f.truncate()
    except OSError as e:
        file_logger.log_error(f"Error when saving data to file {path}")
        file_logger.log_error(e)

def io_function(input_file: str = "",
                output_file: str = "",
                default_return: Any = 0,
                json: bool = True):
    """

    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            input_data = read_required(input_file, json=json)
            if input_data is None:
                return default_return
            return func(*args, input_data = input_data, output_path = output_file, **kwargs)
        return wrapper
    return decorator

class BaseFile:
    def __init__(self, path: str) -> None:
        self._path = path

    def get_path(self) -> str:
        return self._path

    def open(self, mode: str) -> io.TextIOWrapper:
        return open(self._path, mode)

    def read(self, json: bool = False) -> Union[str, Union[list, dict, None]]:
        return read_required(self._path, json=json)

    def write(self, contents: str, json: bool = False) -> None:
        return write_to_file(self._path, contents, create=False, json=json)


class TempFile(BaseFile):
    def __init__(self, path: str) -> None:
        super().__init__(path)

    def __enter__(self) -> TempFile:
        if os.path.isfile(self._path):
            raise FileExistsError(f"{self._path} is already a file")

        # Create file
        f = open(self._path, "a")
        f.close()

        return self

    def __exit__(self, exception_type, exception_value, exception_traceback) -> None:
        os.remove(self._path)


class ConstFile(BaseFile):
    def __init__(self, path: str) -> None:
        super().__init__(path)
        self.data = None

    def __enter__(self) -> ConstFile:
        if not os.path.isfile(self._path):
            raise FileNotFoundError(f"No such file: {self._path}")

        self.data = self.read()
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback) -> None:
        self.write(self.data)
