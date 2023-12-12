from django.urls import path
from . import views


app_name = 'product'
urlpatterns = [
    path('create_product/', views.create_product, name='create_product'),
    path('create_category/', views.create_category, name='create_category'),
    path('products/', views.products, name='products'),
    path('edit_category/<int:category_id>/',
         views.edit_category, name='edit_category'),
    path('delete_category/<int:category_id>/',
         views.delete_category, name='delete_category'),
    path('edit_product/<int:product_id>/',
         views.edit_product, name='edit_product'),
    # Delete Product
    path('delete_product/<int:product_id>/',
         views.delete_product, name='delete_product'),
    path('stock/', views.stock, name='stock'),
    path('low_stock/', views.low_stock, name='low_stock'),
    path('out_of_stock/', views.out_of_stock, name='out_of_stock'),
    path('create_stock_take/', views.create_stock_take, name='create_stock_take'),
    path('stocks/', views.stocks, name='stocks'),
    path('stock_detail/<int:stock_take_id>/',
         views.stock_detail, name='stock_detail'),
    path('stock_take/<int:stock_take_id>/update/<int:stock_take_item_id>/',
         views.update_stock_take_item, name='update_stock'),
    path('stockmovement/', views.stock_movement, name='stock_movement'),
    path('suppliers/', views.suppliers, name='suppliers'),
    path('supplier_create/', views.supplier_create, name='supplier_create'),
    path('receivings/', views.receivings, name='receivings'),
    path('dispatches/', views.dispatches, name='dispatches'),
    path('dispatch/', views.dispatch, name='dispatch'),
    path('export_stock/', views.export_stock, name='export_stock'),
    path('p_promotion/', views.product_promotion, name='p_promotion'),
    path('p_promotion/<int:product_id>/', views.promotion, name='promotion'),
    path('promotions/', views.promotions, name='promotions'),
    path('edit_promotion/<int:promotion_id>/',
         views.edit_promotion, name='edit_promotion'),
    path('delete_promotion/<int:promotion_id>/',
         views.delete_promotion, name='delete_promotion'),
    path('stock_update/<int:stocktake_id>/',
         views.stock_update, name='stock_update'),
    path('supplier/edit/<int:pk>/', views.supplier_edit, name='supplier_edit'),
    path('supplier/delete/<int:pk>/',
         views.supplier_delete, name='supplier_delete'),



]
