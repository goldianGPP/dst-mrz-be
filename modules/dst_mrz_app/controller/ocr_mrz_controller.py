from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from ..service.ocr_mrz_service import OcrMrzService


class OcrMrzController(generics.CreateAPIView):

    def __init__(self):
        self.ocrMrzService = OcrMrzService()

    def post(self, request, *args, **kwargs):
        request_body = request.data
        result = self.ocrMrzService.extract(request_body.get("image1"))

        if result:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response({"error": "failed"}, status=status.HTTP_400_BAD_REQUEST)
