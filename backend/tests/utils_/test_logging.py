import os
import shutil
from utils.logger import resolve_caller, LogFile, Logger

test_logger = Logger.get_logger()

def _func():
    return resolve_caller()

@test_logger.describe("A test function")
def _func2(test_attr):
    pass

def test_resolve_caller():
    assert resolve_caller() == "python.py"
    assert _func() == "test_logging.py"

def test_log_file():

    # Saving empty buffer causes no file to be created
    test_logfile = LogFile("tests\\test_data\\test_log.log")
    test_logfile.save_buffer()
    assert not os.path.isfile("tests\\test_data\\test_log.log")

    # Adding normal message to buffer
    test_logfile.write_message_to_buffer("test message", "INFO", "main.py")
    assert test_logfile.log_message_buffer[0] == "[INFO] [main.py] test message\n"

    # Adding returns to buffer
    test_logfile.write_message_to_buffer("test return message", "INFO", "main.py", end='\r')
    assert len(test_logfile.log_message_buffer) == 2

    test_logfile.write_message_to_buffer("test new message", "INFO", "main.py", end='\r')
    assert len(test_logfile.log_message_buffer) == 2
    assert test_logfile.log_message_buffer[-1] == "[INFO] [main.py] test new message\r"

def test_logger_object():
    assert test_logger.caller == "test_logging.py"

    Logger.init("tests\\utils\\logs", "test", False)
    assert os.path.isdir("tests\\utils\\logs")

    # Test "describes" wrapper
    _func2("hello")
    assert Logger.log_file.log_message_buffer[-1] == """[INFO] [test_logging.py] A test function [args: ('hello',) kwargs: {}]\n"""

    test_logger.write()
    shutil.rmtree("tests\\utils\\logs")
