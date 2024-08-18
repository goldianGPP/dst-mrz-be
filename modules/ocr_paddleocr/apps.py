from django.apps import AppConfig


class OcrPaddleocrConfig(AppConfig):
    name = 'modules.ocr_paddleocr'

    def ready(self):
        from .service.extract_text_service import ExtractTextService
        self.extractTextService = ExtractTextService()
        OcrPaddleocrConfig.extractTextService_instance = self.extractTextService
        print("ExtractTextService instance is ready!")
