from django.urls import path
from . import views



app_name = 'product'
urlpatterns = [
    path('create_product/', views.create_product, name='create_product'),
    path('create_category/', views.create_category, name='create_category'),
    path('products/', views.products, name='products'),
]