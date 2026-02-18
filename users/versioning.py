from typing import Callable, Dict, List

from ninja import Router

# version constants
API_V1 = "v1"  # url /user/, first version
API_V2 = "v2"  # url /user/v2/, full topic structure refactor
SUPPORTED_API_VERSIONS = [API_V1, API_V2]


class VersionedRouter:
    def __init__(self, versions: List[str]):
        self.routers: Dict[str, Router] = {v: Router() for v in versions}

    def api_operation(self, methods: List[str], path: str, **kwargs):
        def decorator(view_func: Callable):
            for router in self.routers.values():
                router.api_operation(methods, path, **kwargs)(view_func)
            return view_func
        return decorator

    def get(self, path: str, **kwargs):
        return self.api_operation(["GET"], path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.api_operation(["POST"], path, **kwargs)

    def put(self, path: str, **kwargs):
        return self.api_operation(["PUT"], path, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.api_operation(["DELETE"], path, **kwargs)

    def patch(self, path: str, **kwargs):
        return self.api_operation(["PATCH"], path, **kwargs)
