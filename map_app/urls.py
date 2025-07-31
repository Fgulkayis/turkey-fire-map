from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.map_view, name='map_page'), 
    path('firms_data/', views.get_firms_data, name='firms_data'),
]