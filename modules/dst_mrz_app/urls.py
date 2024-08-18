from django.urls import path
from .controller.ocr_mrz_controller import OcrMrzController

mapping = "v1/passport"
urlpatterns = [
    path(f"{mapping}", OcrMrzController.as_view(), name='mrz-object'),
]