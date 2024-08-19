import gc
import threading
import base64
import numpy as np
from io import BytesIO
from PIL import Image
from paddleocr import PaddleOCR
import logging

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
            use_angle_cls=True,
            lang='en',
            rec_model_dir='ch_PP-OCRv4_rec_infer',
            det_model_dir='ch_PP-OCRv4_det_infer',
            cls_model_dir='ch_ppocr_mobile_v2.0_cls_infer'
        )
        self.lock = threading.Lock()

    def extract_from_base64(self, imageBase64):
        with self.lock:
            image_data = base64.b64decode(imageBase64)
            image = Image.open(BytesIO(image_data))
            
            image_np = np.array(image)
            
            try:
                result = self.ocr_model.ocr(image_np, cls=True)
            except Exception as e:
                logging.error(f"Error processing OCR: {e}")
                result = None
            finally: 
                del image_np
                gc.collect()
            
            return result
