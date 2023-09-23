from django.urls import path
from . import views



app_name = 'pos'
urlpatterns = [
    path('', views.index, name='index'),
    path('add_cart/<int:product_id>/', views.add_to_cart, name='add_cart'),
    path('cart/', views.cart, name='cart'),
    path('cart/increment/<int:item_id>/', views.increment_cart_item, name='increment_cart_item'),
    path('cart/decrement/<int:item_id>/', views.decrement_cart_item, name='decrement_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('remove_cart_item/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('sales/', views.sales, name='sales'),
    path('sale/<int:sale_id>/', views.sale, name='sale'),
    path('sales_h/', views.sales_h, name='sales_h'),

]