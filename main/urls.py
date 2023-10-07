from django.urls import path
from . import views



app_name = 'main'
urlpatterns = [
    path("", views.index, name="index"),
    path('buyers/', views.buyers, name='buyers'),
    path('create_buyer/', views.create_buyer, name='create_buyer'),
]