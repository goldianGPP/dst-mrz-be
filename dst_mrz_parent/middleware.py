import traceback
from dst_mrz_parent.exceptions import BusinessException
from django.http import JsonResponse
from rest_framework import status
import logging

logger = logging.getLogger("dst-mrz-be")


class ErrorHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, e):
        if isinstance(e, BusinessException):
            logger.error(f"BusinessException :: {traceback.format_exc()}")
            response = {
                "type": e.type,
                "message": e.message,
                "code": e.code,
                "params": e.params,
                "status": e.status_code,
            }
            return JsonResponse(response, status=e.status_code)
        else:
            logger.error(f"Exception :: {traceback.format_exc()}")
            return JsonResponse(
                {
                    "error": "internal server error",
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
