from django.apps import AppConfig


class DstMrzS3Config(AppConfig):
    name = 'modules.dst_mrz_s3'

    def ready(self):
        from .service.s3_storage_service import S3StorageService
        self.s3StorageService = S3StorageService()
        DstMrzS3Config.s3StorageService_instance = self.s3StorageService
        print("S3StorageService instance is ready!")
