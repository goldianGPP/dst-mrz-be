import threading
from ..model.models import Country
from dst_mrz_parent.exceptions import ResourceNotFound

import logging
logger = logging.getLogger("dst-mrz-be")

class CountryService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                cls._instance = super(CountryService, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def all(self):
        return Country.objects.all()

    def by_code(self, code):
        try:
            return Country.objects.get(pk=code)
        except Exception as e:
            logger.info(f"country code not found {e}")
            raise ResourceNotFound("country code not found")

    def by_alpha3(self, alpha3):
        try:
            return Country.objects.get(alpha3=alpha3)
        except Exception as e:
            logger.info(f"country alpha3 not found {e}")
            raise ResourceNotFound("country alpha3 not found")
