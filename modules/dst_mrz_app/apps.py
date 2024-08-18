from django.apps import AppConfig


class DstMrzAppConfig(AppConfig):
    name = 'modules.dst_mrz_app'

    def ready(self):
        from .service.ocr_mrz_service import OcrMrzService
        self.ocrMrzService = OcrMrzService()
        DstMrzAppConfig.ocrMrzService_instance = self.ocrMrzService
        print("OcrMrzService instance is ready!")
