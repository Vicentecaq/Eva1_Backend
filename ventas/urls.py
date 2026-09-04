from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_productos, name='lista_productos'),
    path('producto/nuevo/', views.crear_producto, name='crear_producto'),
    path('producto/editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('producto/eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
    path('venta/nueva/', views.registrar_venta, name='registrar_venta'),
]

