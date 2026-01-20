from django.db.models import F
from home.models import Blog


class BlogViewCounterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.resolver_match and request.resolver_match.url_name == "blog_detail":
            slug = request.resolver_match.kwargs.get("slug")
            Blog.objects.filter(slug=slug).update(views=F("views") + 1)

        return response
