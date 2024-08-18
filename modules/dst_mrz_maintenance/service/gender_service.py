import threading
from ..model.models import Gender
from dst_mrz_parent.exceptions import ResourceNotFound

import logging
logger = logging.getLogger("dst-mrz-be")

class GenderService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                cls._instance = super(GenderService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def all(self):
        return Gender.objects.all()

    def by_code(self, code):
        try:
            return Gender.objects.get(pk=code)
        except Exception as e:
            logger.info(f"gender code not found {e}")
            raise ResourceNotFound("gender code not found")

