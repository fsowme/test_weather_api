from django.http.response import HttpResponse


def weather_test(request):
    return HttpResponse("Weather ok")
