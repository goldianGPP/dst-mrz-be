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
            lang="en",
            rec_model_dir="ch_PP-OCRv4_rec_infer",
            det_model_dir="ch_PP-OCRv4_det_infer",
            cls_model_dir="ch_ppocr_mobile_v2.0_cls_infer",
        )
        self.ocr_model.det_lang = "ml"
        self.lock = threading.Lock()

    def _lightweight_preprocess(
        self, image, w_threshold=True, stretch_h=1.5, stretch_v=1.2
    ):
        try:
            # Convert the image to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            if w_threshold:
                # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gray = clahe.apply(gray)

                # Stretch the image horizontally by the specified stretch_factor
                new_width = int(gray.shape[1] * stretch_h)
                new_height = int(gray.shape[0] * stretch_v)
                stretched_image = cv2.resize(gray, (new_width, new_height))

                # Apply binary thresholding
                _, binary = cv2.threshold(
                    stretched_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
                return binary
            else:
                return gray

        finally:
            del gray
            if w_threshold:
                del binary
                del _
                del clahe
                del stretched_image

    def _get_horizontal_lines(
        self, results, height_threshold=0.5, distance_threshold=50
    ):
        # Extract text boxes and their coordinates
        boxes = [line[0] for line in results[0]]
        texts = [line[1][0] for line in results[0]]

        # Calculate the vertical center and the horizontal position of each box
        centers = [(box[0][1] + box[2][1]) / 2 for box in boxes]
        heights = [(box[2][1] - box[0][1]) for box in boxes]
        x_positions = [box[0][0] for box in boxes]

        lines = []
        current_line = []
        prev_center = centers[0]
        prev_x = x_positions[0]

        for i in range(len(texts)):
            if (
                abs(centers[i] - prev_center) <= height_threshold * heights[i]
                and abs(x_positions[i] - prev_x) <= distance_threshold
            ):
                # Same line and within distance threshold
                current_line.append(texts[i])
            else:
                # New line
                lines.append(" ".join(current_line))
                current_line = [texts[i]]
            prev_center = centers[i]
            prev_x = (
                x_positions[i] + boxes[i][2][0] - boxes[i][0][0]
            )  # Update to the end x-position

        # Append the last line
        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def extract_from_base64(self, imageBase64):
        with self.lock:
            image_data = base64.b64decode(imageBase64)
            image = Image.open(BytesIO(image_data))
            image_np = np.array(image)
            preprocessed_image = self.lightweight_preprocess(image_np)

            try:
                return self._get_horizontal_lines(
                    results=self.ocr_model.ocr(preprocessed_image, cls=True),
                )
            except Exception as e:
                logging.error(f"Error processing OCR: {e}")
                return None
            finally:
                del image_np
                del preprocessed_image
                gc.collect()
