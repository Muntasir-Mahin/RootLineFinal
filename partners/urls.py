from django.urls import path

from . import views

app_name = 'partners'
urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.partner_login, name='login'),
    path('terms/', views.terms, name='terms'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/profile/', views.profile_edit, name='profile_edit'),
    path('dashboard/assets/<str:kind>/', views.asset_list, name='asset_list'),
    path('dashboard/assets/<str:kind>/add/', views.asset_edit, name='asset_add'),
    path('dashboard/assets/<str:kind>/<int:pk>/edit/', views.asset_edit, name='asset_edit'),
    path('dashboard/assets/<str:kind>/<int:pk>/delete/', views.asset_delete, name='asset_delete'),
]
