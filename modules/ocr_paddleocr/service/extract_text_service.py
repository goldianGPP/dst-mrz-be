import gc
import threading
import base64
import numpy as np
from io import BytesIO
from paddleocr import PaddleOCR
import logging
import cv2
from PIL import Image, ImageEnhance

class ExtractTextService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ExtractTextService, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.ocr_model = PaddleOCR(
            use_angle_cls=False,
            lang='en',
            rec_model_dir='ch_PP-OCRv4_rec_infer',
            det_model_dir='ch_PP-OCRv4_det_infer',
            cls_model_dir='ch_ppocr_mobile_v2.0_cls_infer'
        )
        self.ocr_model.det_lang = "ml"
        self.lock = threading.Lock()

    def lightweight_preprocess(self, image):
        gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        _, thresh_image = cv2.threshold(gray_image, 110, 255, cv2.THRESH_BINARY)
        return thresh_image

    def extract_from_base64(self, imageBase64):
        with self.lock:
            image_data = base64.b64decode(imageBase64)
            image = Image.open(BytesIO(image_data))
            image_np = np.array(image)
            preprocessed_image = self.lightweight_preprocess(image_np)
            
            try:
                return self.ocr_model.ocr(preprocessed_image, cls=True)
            except Exception as e:
                logging.error(f"Error processing OCR: {e}")
                return None
            finally: 
                del image_np
                del preprocessed_image
                gc.collect()
