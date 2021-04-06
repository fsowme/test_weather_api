from django.http.response import HttpResponse


def api_test(request):
    return HttpResponse("API ok")
