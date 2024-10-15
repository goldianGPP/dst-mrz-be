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
import re

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

        formatted_time = datetime.fromtimestamp(start_time).strftime(
            "%Y_%m_%d_%H_%M_%S"
        )
        self.s3StorageService.put_object(base64, self.bucket_id, f"image_{formatted_time}.jpeg")

        after_storing_time = time.time()
        logger.info(f"S3 Store time: {after_storing_time - start_time} seconds")

        result = self.extractTextService.extract_from_base64(base64)
        after_extraction_time = time.time()
        logger.info(
            f"After extraction: {after_extraction_time - after_storing_time} seconds"
        )

        try:
            mrz = OcrMrzService.paddle_result_to_mrz(result)
            logger.info("\n")
            logger.info(f"MRZ string: {mrz}")
            
            mrz_result = self.mrzService.extractTD3(mrz)
            after_formation_time = time.time()
            logger.info(
                f"After formation: {after_formation_time - after_extraction_time} seconds"
            )

            dto = self.to_dto(mrz_result)
            after_conversion_time = time.time()
            logger.info(
                f"After conversion: {after_conversion_time - after_formation_time} seconds"
            )

            return dto
        except Exception as e:
            raise BusinessException("MRZ Data not found", "MRZ-00003")

    @staticmethod
    def paddle_result_to_mrz(result):

        expected_mrz = []
        for text in result:
            logger.info(f"TEXT FROM: {text}")
            text = re.sub(r"[^a-zA-Z0-9<]", "", text)
            text = text.replace(" ", "<")  # Replace spaces with '<'
            text_len = len(text)
            if text_len < 44:
                # Calculate the number of '<' needed
                need_len = 44 - text_len

                # Find the position of "<<<" in the text to insert additional '<'
                triple_chevron_index = text.find("<<<")
                if triple_chevron_index != -1:
                    # Split the text around the "<<<" and insert the additional '<'
                    before = text[: triple_chevron_index + 3]
                    after = text[triple_chevron_index + 3 :]
                    text = before + ("<" * need_len) + after
                else:
                    # If "<<<" is not found, pad at the end
                    text = text + ("<" * need_len)
            elif text_len > 44:
                # Find the position of "<<<" in the text to remove excess characters
                excess_len = text_len - 44
                triple_chevron_index = text.find("<<<")
                if triple_chevron_index != -1:
                    before = text[: triple_chevron_index + 3]
                    after = text[
                        triple_chevron_index + 3 + excess_len :
                    ]  # Remove excess characters
                    text = before + after
                else:
                    # If "<<<" is not found, trim the end
                    text = text[:44]

            # Add text to MRZ with a newline
            logger.info(f"TEXT TO: {text}")
            expected_mrz.append(text)

        end_idx = len(expected_mrz)
        mrz = expected_mrz[end_idx - 2] + "\n" + expected_mrz[end_idx - 1]
        mrz = mrz.rstrip("\n").upper()
        return mrz

    def to_dto(self, mrz_result):
        if mrz_result is False:
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

        dto["fullName"] = (f"{mrz_result.name}  {mrz_result.surname}").strip()
        try:
            dto["identityNo"] = mrz_result.document_number
        except Exception as e:
            validation_count = validation_count + 1
            dto["identityNo"] = ""

        try:
            dto["dateOfBirth"] = self.convert_date(mrz_result.birth_date)
        except Exception as e:
            logger.info(f"Failed extracting date of birth")
            validation_count = validation_count + 1
            dto["dateOfBirth"] = ""

        try:
            dto["expiryDate"] = self.convert_date(mrz_result.expiry_date)
        except Exception as e:
            logger.info(f"Failed extracting expiry date")
            validation_count = validation_count + 1
            dto["expiryDate"] = ""

        if gender is not None:
            dto["genderCode"] = gender.code
            dto["genderValue"] = gender.name
        else:
            dto["genderCode"] = ""
            dto["genderValue"] = ""

        if country is not None:
            dto["nationalityValue"] = country.description
            dto["nationalityId"] = country.code
        else:
            dto["nationalityValue"] = ""
            dto["nationalityId"] = ""

        dto["issuedCountryCode"] = mrz_result.country

        if validation_count >= validation_threshold:
            logger.info(f"validation_count {validation_count} > validation_threshold {validation_threshold}")
            raise BusinessException("Unsupported MRZ Type", "MRZ-00002")

        return dto

    def convert_date(self, input_date):
        input_date = str(input_date)
        date_object = datetime.strptime(input_date, "%y%m%d")
        formatted_date = date_object.strftime("%d/%m/%Y")

        return formatted_date
