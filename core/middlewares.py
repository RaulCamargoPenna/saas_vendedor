from django.shortcuts import redirect
from django.contrib import messages

class DemoReadOnlyMiddleware:
    WRITE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}

    ALLOWED_PATHS = {
        'saas/conta/logout/',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and request.user.is_demo
            and request.method in self.WRITE_METHODS
            and request.path not in self.ALLOWED_PATHS
        ):
            messages.warning(
                request,
                'A conta de demonstração é somente para visualização.'
            )

            return redirect(request.META.get('HTTP_REFERER', '/'))

        return self.get_response(request)
    
class SaaSDomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0]

        if host == "saas.raulcamargo.com.br":
            if not request.path.startswith("/saas/"):
                request.path_info = "/saas" + request.path_info

        response = self.get_response(request)

        return response