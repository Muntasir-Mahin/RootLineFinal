from django.urls import path

from . import product_views, public_views, views

app_name = 'partners'
urlpatterns = [
    path('', public_views.directory, name='directory'),
    path('register/', views.register, name='register'),
    path('login/', views.partner_login, name='login'),
    path('terms/', views.terms, name='terms'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/profile/', views.profile_edit, name='profile_edit'),
    path('dashboard/products/', product_views.product_list, name='product_list'),
    path('dashboard/products/add/', product_views.product_edit, name='product_add'),
    path('dashboard/products/<int:pk>/edit/', product_views.product_edit, name='product_edit'),
    path('dashboard/products/<int:pk>/toggle/', product_views.product_toggle, name='product_toggle'),
    path('dashboard/products/<int:pk>/delete/', product_views.product_delete, name='product_delete'),
    path('dashboard/products/<int:pk>/images/', product_views.product_images, name='product_images'),
    path('dashboard/product-images/<int:pk>/delete/', product_views.product_image_delete, name='product_image_delete'),
    path('dashboard/assets/<str:kind>/', views.asset_list, name='asset_list'),
    path('dashboard/assets/<str:kind>/add/', views.asset_edit, name='asset_add'),
    path('dashboard/assets/<str:kind>/<int:pk>/edit/', views.asset_edit, name='asset_edit'),
    path('dashboard/assets/<str:kind>/<int:pk>/delete/', views.asset_delete, name='asset_delete'),
    path('<slug:slug>/certificates/<int:pk>/download/', public_views.certificate_download, name='certificate_download'),
    path('<slug:slug>/products/<slug:product_slug>/', public_views.product_detail, name='product_detail'),
    path('<slug:slug>/', public_views.store, name='store'),
]
