from django.apps import AppConfig


class DstMrzMaintenanceConfig(AppConfig):
    name = 'modules.dst_mrz_maintenance'

    def ready(self):
        from .service.country_service import CountryService
        self.countryService = CountryService()
        DstMrzMaintenanceConfig.countryService_instance = self.countryService
        print("CountryService instance is ready!")
        
        from .service.gender_service import GenderService
        self.genderService = GenderService()
        DstMrzMaintenanceConfig.genderService_instance = self.genderService
        print("GenderService instance is ready!")
