from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = 'users'
urlpatterns = [
    path("register", views.register, name="register"),
    path('login', views.custom_login, name='login'),
    path('profile/<username>', views.profile, name='profile'),
    path('logout', views.custom_logout, name='logout'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path("password_change", views.password_change, name="password_change"),
    path("password_reset", views.password_reset_request, name="password_reset"),
    path('reset/<uidb64>/<token>', views.passwordResetConfirm,
         name='password_reset_confirm'),
    path("not_authorized/", views.not_authorized, name="not_authorized"),
    path("staffs", views.staffs, name="staffs"),
    path('delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path("not_allowed", views.not_allowed, name="not_allowed"),
    path('update/<int:user_id>/', views.update_user, name='update_staff'),

]
