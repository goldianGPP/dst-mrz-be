from django.apps import AppConfig


class MrzReaderConfig(AppConfig):
    name = 'modules.mrz_reader'

    def ready(self):
        from .service.mrz_service import MrzService
        self.mrzService = MrzService()
        MrzReaderConfig.mrzService_instance = self.mrzService
        print("MrzService instance is ready!")
