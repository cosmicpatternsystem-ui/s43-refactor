from .api_error import ApiError

class ApiHttpError(ApiError):
    def __init__(self, message="", status=None, body=None, headers=None, code=None, payload=None, response=None, **kwargs):
        super().__init__(message)
        self.status = status
        self.body = body
        self.headers = headers
        self.code = code
        self.payload = payload
        self.response = response
        self.extra = dict(kwargs) if kwargs else {}