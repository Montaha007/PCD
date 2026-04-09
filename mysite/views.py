from django.http import JsonResponse

def test_api(request):
    data = {
        "message": "Hello from Django backend"
    }
    return JsonResponse(data)