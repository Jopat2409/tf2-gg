"""Custom helper functions, classes and decorators that are reused throught the backend
"""
from utils.logger import Logger
from utils.file import TempFile, ConstFile
from datetime import datetime

__all__ = [Logger, TempFile, ConstFile]

def epoch_from_timestamp(_time: str) -> float:
  if not _time:
    return 0
  dt = datetime.strptime(_time, "%Y-%m-%dT%H:%M:%S.%fZ")
  return (dt - datetime(1970, 1, 1)).total_seconds()
