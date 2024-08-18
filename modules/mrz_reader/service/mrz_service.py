import logging
import threading
from mrz.checker.td1 import TD1CodeChecker
from mrz.checker.td2 import TD2CodeChecker
from mrz.checker.td3 import TD3CodeChecker

logger = logging.getLogger("dst-mrz-be")


class MrzService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(MrzService, cls).__new__(cls)
        return cls._instance
    
    def extractTD1(self, mrz):
        td1_check = TD1CodeChecker(mrz)
        fields = td1_check.fields()

        return fields
    
    def extractTD2(self, mrz):
        td1_check = TD2CodeChecker(mrz)
        fields = td1_check.fields()

        return fields
    
    def extractTD3(self, mrz):
        td1_check = TD3CodeChecker(mrz)
        fields = td1_check.fields()

        return fields
        
