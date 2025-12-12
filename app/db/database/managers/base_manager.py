from abc import ABC
from ..connection import get_database
from pymongo.database import Database
from utils.logging_info import get_logger


class BaseManager(ABC):
    """Base Manager interface"""

    def __init__(self, db: Database = None):
        self.db = db if db is not None else get_database()
        self.logger = get_logger()
