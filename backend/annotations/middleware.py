from django.http import HttpResponse


class DevCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = HttpResponse(status=204) if request.method == "OPTIONS" else self.get_response(request)
        origin = request.headers.get("Origin", "http://127.0.0.1:5173")
        allowed_origins = {"http://127.0.0.1:5173", "http://localhost:5173"}
        response["Access-Control-Allow-Origin"] = origin if origin in allowed_origins else "http://127.0.0.1:5173"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
