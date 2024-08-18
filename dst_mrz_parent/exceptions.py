from rest_framework import status

class BusinessException(Exception):
    def __init__(self, message, code=None, params={}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, type="BusinessException"):
        self.message = message
        self.code = code
        self.params = params
        self.status_code = status_code
        self.type = type
        super().__init__(message)

class ResourceNotFound(BusinessException):
    def __init__(self, message):
        self.message = message
        self.status_code = status.HTTP_404_NOT_FOUND
        self.type = "ResourceNotFound"
        super().__init__(message, status_code=self.status_code, type=self.type)