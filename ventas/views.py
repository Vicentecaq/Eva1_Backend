from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto, Cliente, Venta, DetalleVenta

def lista_productos(request):
    productos = Producto.objects.all()
    return render(request, 'ventas/lista_productos.html', {'productos': productos})

def crear_producto(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        nombre = request.POST.get('nombre')
        cantidad = request.POST.get('cantidad')
        precio = request.POST.get('precio')
        Producto.objects.create(codigo=codigo, nombre=nombre, cantidad=cantidad, precio=precio)
        return redirect('lista_productos')
    return render(request, 'ventas/form_producto.html')

def editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        producto.codigo = request.POST.get('codigo')
        producto.nombre = request.POST.get('nombre')
        producto.cantidad = request.POST.get('cantidad')
        producto.precio = request.POST.get('precio')
        producto.save()
        return redirect('lista_productos')
    return render(request, 'ventas/form_producto.html', {'producto': producto})

def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        producto.delete()
        return redirect('lista_productos')
    return render(request, 'ventas/eliminar_producto.html', {'producto': producto})

def registrar_venta(request):
    productos = Producto.objects.filter(cantidad__gt=0)
    if request.method == 'POST':
        rut = request.POST.get('rut')
        es_habitual = request.POST.get('es_habitual') == 'on'
        nombre = request.POST.get('nombre')
        
        cliente = None
        rut_boleta = rut
        if es_habitual and rut:
            cliente, created = Cliente.objects.get_or_create(rut=rut, defaults={'nombre': nombre})
        
        venta = Venta.objects.create(cliente=cliente, rut_boleta=rut_boleta)
        
        total = 0
        producto_ids = request.POST.getlist('productos')
        cantidades = request.POST.getlist('cantidades')
        
        for p_id, cant in zip(producto_ids, cantidades):
            if int(cant) > 0:
                prod = get_object_or_404(Producto, id=p_id)
                if prod.cantidad >= int(cant):
                    DetalleVenta.objects.create(
                        venta=venta, producto=prod, cantidad=int(cant), precio_unitario=prod.precio
                    )
                    prod.cantidad -= int(cant)
                    prod.save()
                    total += prod.precio * int(cant)
        
        venta.total = total
        venta.save()
        return redirect('lista_productos')
    
    return render(request, 'ventas/registrar_venta.html', {'productos': productos})

