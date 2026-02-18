from django.http import JsonResponse

from .versioning import SUPPORTED_API_VERSIONS

class VersioningMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Determine version from resolver_match (set by namespace in urls.py)
        if request.resolver_match and request.resolver_match.namespace:
            ns = request.resolver_match.namespace
            if ns in SUPPORTED_API_VERSIONS:
                 request.version = ns
            elif ns.startswith("api_") and ns[4:] in SUPPORTED_API_VERSIONS:
                 request.version = ns[4:]
            else:
                 # Default to the first supported version if namespace doesn't match a version
                 request.version = SUPPORTED_API_VERSIONS[0]
        else:
            # Fallback for requests without a resolver match (e.g. 404s, some static files)
            request.version = SUPPORTED_API_VERSIONS[0]
        return None
