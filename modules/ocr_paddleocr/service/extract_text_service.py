import logging
import threading
import base64
from io import BytesIO
from PIL import Image
import numpy as np
from paddleocr import PaddleOCR
logger = logging.getLogger("dst-mrz-be")

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
            lang='en')

    def extract_from_base64(self, imageBase64):
        image_data = base64.b64decode(imageBase64)
        image = Image.open(BytesIO(image_data))  # Open the image using Pillow
        
        # Convert Pillow image to numpy array
        image_np = np.array(image)
        
        result = self.ocr_model.ocr(image_np, cls=True)
        
        return result
