from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin


def _variants(path):
    if path.endswith("/") and path != "/":
        return [path, path.rstrip("/")]
    if path != "/":
        return [path, f"{path}/"]
    return [path]


class LegacyRedirectMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.method not in ("GET", "HEAD"):
            return None
        from apps.redirects.models import LegacyRedirect

        match = LegacyRedirect.objects.filter(from_path__in=_variants(request.path)).first()
        if match is None or match.to_path == request.path:
            return None
        if match.status_code == 302:
            return HttpResponseRedirect(match.to_path)
        return HttpResponsePermanentRedirect(match.to_path)
