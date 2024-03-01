from django.urls import path
from . import views


app_name = 'pos'
urlpatterns = [
    path('', views.index, name='index'),
    path('add_cart/<int:product_id>/', views.add_to_cart, name='add_cart'),
    path('cart/', views.cart, name='cart'),
    path('cart/increment/<int:item_id>/',
         views.increment_cart_item, name='increment_cart_item'),
    path('cart/decrement/<int:item_id>/',
         views.decrement_cart_item, name='decrement_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('remove_cart_item/<int:item_id>/',
         views.remove_cart_item, name='remove_cart_item'),
    path('sales/', views.sales, name='sales'),
    path('sale/<int:sale_id>/', views.sale, name='sale'),
    path('sales_h/', views.sales_h, name='sales_h'),
    path('toggle_vat/', views.toggle_add_vat, name='toggle_vat'),
    path('update_discount/', views.update_discount, name='update_discount'),
    path('eshop/inventory/', views.menu, name='menu'),
    path('eshop/expiring/', views.expiring, name='expiring'),
    path('eshop/receivings/', views.receivings, name='received'),
    path('eshop/supplies/', views.supplies, name='supplies'),
    path('eshop/about/', views.about, name='about'),
     path('eshop/cataloque/', views.cataloque, name='cataloque'),
     path('cataloque/<int:cataloque_id>/', views.cataloque_detail, name='cataloque_detail'),
     path('export_cataloque/<int:cataloque_id>/', views.export_cataloque, name='export_cataloque'),
      path('eshop/mails/', views.mails, name='mails'),
       path('eshop/create_mails/', views.create_mail, name='create_mails'),
]
