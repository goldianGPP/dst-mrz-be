import gc
import threading
import base64
import numpy as np
from io import BytesIO
from paddleocr import PaddleOCR
import logging
import cv2
from PIL import Image

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
            lang="en",
        )
        self.lock = threading.Lock()

    def _lightweight_preprocess(self, image, w_threshold=True):
        try:
            # Convert the image to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if w_threshold:
                # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gray = clahe.apply(gray)

                # Apply binary thresholding
                _, binary = cv2.threshold(
                    gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
                return binary
            else:
                return gray

        finally:
            gray = None
            del gray
            if w_threshold:
                binary = None
                del binary
                _ = None
                del _
                clahe = None
                del clahe
            gc.collect()

    def _get_horizontal_lines(
        self, results, height_threshold=0.7, distance_threshold=500
    ):
        boxes = [line[0] for line in results[0]]
        texts = [line[1][0] for line in results[0]]
        
        centers = [(box[0][1] + box[2][1]) / 2 for box in boxes]
        heights = [(box[2][1] - box[0][1]) for box in boxes]
        
        left_positions = [box[0][0] for box in boxes]
        right_positions = [box[2][0] for box in boxes]
        
        lines = []
        current_line = []
        prev_center = centers[0]
        prev_x_left = left_positions[0] 
        prev_x_right = right_positions[0] 
        
        for i in range(len(texts)):
            if (abs(centers[i] - prev_center) <= height_threshold * heights[i] and
                abs(left_positions[i] - prev_x_right) <= distance_threshold): 
                current_line.append(texts[i])
            else:
                lines.append("".join(current_line))
                current_line = [texts[i]]
            
            prev_center = centers[i]
            prev_x_left = left_positions[i] 
            prev_x_right = right_positions[i] 
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines

    def extract_from_base64(self, imageBase64):
        with self.lock:
            image_data = base64.b64decode(imageBase64)
            image = Image.open(BytesIO(image_data))
            image_np = np.array(image)
            preprocessed_image = self._lightweight_preprocess(image_np)

            try:
                return self._get_horizontal_lines(
                    results=self.ocr_model.ocr(preprocessed_image, cls=True),
                )
            finally:
                # Release memory of temporary variables
                del image_data, image, image_np, preprocessed_image
                gc.collect()
