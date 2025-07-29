from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("Harita Projesi Anasayfası!")
def map_view(request):
    return render(request, 'map_app/map.html')