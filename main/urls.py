from django.urls import path
from . import views


app_name = 'main'
urlpatterns = [
    path("", views.index, name="index"),
    path('buyers/', views.buyers, name='buyers'),
    path('create_buyer/', views.create_buyer, name='create_buyer'),
    path('print/', views.print_and_cut, name='print'),
    path('create_about/', views.create_about, name='create_about'),

]
