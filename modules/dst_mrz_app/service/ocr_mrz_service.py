import time
import logging
import threading
from datetime import datetime
from modules.dst_mrz_s3.service.s3_storage_service import S3StorageService
from modules.ocr_paddleocr.service.extract_text_service import ExtractTextService
from modules.mrz_reader.service.mrz_service import MrzService
from modules.dst_mrz_maintenance.service.gender_service import GenderService
from modules.dst_mrz_maintenance.service.country_service import CountryService
from dst_mrz_parent.exceptions import BusinessException
logger = logging.getLogger("dst-mrz-be")

class OcrMrzService:
    _instance = None
    _lock = threading.Lock()
    
    bucket_id = "MRZ"

    def __init__(self):
        self.s3StorageService = S3StorageService()
        self.extractTextService = ExtractTextService()
        self.mrzService = MrzService()
        self.genderService = GenderService()
        self.countryService = CountryService()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(OcrMrzService, cls).__new__(cls)
        return cls._instance

    def extract(self, base64):
        start_time = time.time()
        logger.info(f"Initial time: {start_time - start_time} seconds")

        formatted_time = datetime.fromtimestamp(start_time).strftime('%Y_%m_%d_%H_%M_%S')
        # self.s3StorageService.put_object(base64, self.bucket_id, f"image_{formatted_time}.jpeg")

        after_storing_time = time.time()
        logger.info(f"S3 Store time: {after_storing_time - start_time} seconds")
        
        result = self.extractTextService.extract_from_base64(base64)
        after_extraction_time = time.time()
        logger.info(f"After extraction: {after_extraction_time - after_storing_time} seconds")
        
        mrz = ""
        lines = []
        for line in result:
            for word_info in line:
                lines.append(word_info[-1][0])

        # Process only the last two lines
        for line in lines[-2:]:  # This will get the last two lines
            text_len = len(line)
            
            logger.info("-------------")
            logger.info(line)
            if text_len == 44:
                mrz = mrz + line + "\n"
            elif text_len < 44:
                need_len = 44 - text_len
                mrz = mrz + line + ("<" * need_len) + "\n"
            elif text_len > 44:
                need_len = text_len - 44
                for _ in range(need_len):
                    mrz = mrz.replace("<", "", 1)

        mrz = mrz.rstrip('\n').upper()
        logger.info("\n")
        logger.info(f"MRZ string: {mrz}")

        try:
            mrz_result = self.mrzService.extractTD3(mrz)
            after_formation_time = time.time()
            logger.info(f"After formation: {after_formation_time - after_extraction_time} seconds")
            
            dto = self.to_dto(mrz_result)
            after_conversion_time = time.time()
            logger.info(f"After conversion: {after_conversion_time - after_formation_time} seconds")
            
            return dto
        except Exception as e:
            raise BusinessException("MRZ Data not found", "MRZ-00003")
    

    def to_dto(self, mrz_result):
        if mrz_result is False :
            raise BusinessException("Unsupported MRZ Type", "MRZ-00002")

        dto = {}
        gender = None
        country = None
        validation_threshold = 4
        validation_count = 0
        try:
            gender = self.genderService.by_code(mrz_result.sex)
        except Exception as e:
            validation_count = validation_count + 1
            gender = None
        try:
            country = self.countryService.by_alpha3(mrz_result.nationality)
        except Exception as e:
            validation_count = validation_count + 1
            country = None

        dto['fullName'] = (f"{mrz_result.name}  {mrz_result.surname}").strip()
        try:
            dto['identityNo'] = mrz_result.document_number
        except Exception as e:
            validation_count = validation_count + 1
            dto['identityNo'] = ""
        
        try:
            dto['dateOfBirth'] = self.convert_date(mrz_result.birth_date)
        except Exception as e:
            validation_count = validation_count + 1
            dto['dateOfBirth'] = ""
        
        try:
            dto['expiryDate'] = self.convert_date(mrz_result.expiry_date)
        except Exception as e:
            validation_count = validation_count + 1
            dto['expiryDate'] = ""
        
        if gender is not None:
            dto['genderCode'] = gender.code
            dto['genderValue'] = gender.name
        else:
            dto['genderCode'] = ""
            dto['genderValue'] = ""
        
        if country is not None:
            dto['nationalityValue'] = country.description
            dto['nationalityId'] = country.code
            dto['issuedCountryCode'] = country.alpha3
        else:
            dto['nationalityValue'] = ""
            dto['nationalityId'] = ""
            dto['issuedCountryCode'] = ""

        if validation_count >= validation_threshold:
            raise BusinessException("Unsupported MRZ Type", "MRZ-00002")

        return dto
    
    def convert_date(self, input_date):
        input_date = str(input_date)
        date_object = datetime.strptime(input_date, '%y%m%d')
        formatted_date = date_object.strftime('%d/%m/%Y')

        return formatted_date
