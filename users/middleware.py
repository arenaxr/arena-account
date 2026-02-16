from users.mqtt import TOPIC_SUPPORTED_API_VERSIONS

class VersioningMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Determine version from resolver_match (set by namespace in urls.py)
        if request.resolver_match and request.resolver_match.namespace:
            if request.resolver_match.namespace in TOPIC_SUPPORTED_API_VERSIONS:
                 request.version = request.resolver_match.namespace
            else:
                 # Default to the first supported version if namespace doesn't match a version
                 # or maybe we want to be strict? For now, let's replicate "default versioning"
                 request.version = TOPIC_SUPPORTED_API_VERSIONS[0]
        else:
            # Fallback for requests without a resolver match (e.g. 404s, some static files)
            request.version = TOPIC_SUPPORTED_API_VERSIONS[0]

        response = self.get_response(request)
        return response
