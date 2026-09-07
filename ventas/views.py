from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from .models import Producto, Cliente, Venta, DetalleVenta

def lista_productos(request):
    productos = Producto.objects.all().order_by('nombre')
    
    # Métricas en tiempo real para el Dashboard administrativo
    total_productos = productos.count()
    total_stock = productos.aggregate(total=Sum('cantidad'))['total'] or 0
    productos_bajo_stock = productos.filter(cantidad__lte=5, cantidad__gt=0)
    productos_agotados = productos.filter(cantidad=0)
    
    total_ventas_monto = Venta.objects.aggregate(total=Sum('total'))['total'] or 0
    total_ventas_count = Venta.objects.count()
    
    hoy = timezone.now().date()
    ventas_hoy_qs = Venta.objects.filter(fecha__date=hoy)
    total_ventas_hoy = ventas_hoy_qs.aggregate(total=Sum('total'))['total'] or 0
    ventas_hoy_count = ventas_hoy_qs.count()
    
    unidades_vendidas = DetalleVenta.objects.aggregate(total=Sum('cantidad'))['total'] or 0
    ventas_recientes = Venta.objects.select_related('cliente').order_by('-fecha')[:6]
    
    context = {
        'productos': productos,
        'total_productos': total_productos,
        'total_stock': total_stock,
        'productos_bajo_stock': productos_bajo_stock,
        'productos_agotados': productos_agotados,
        'total_ventas_monto': total_ventas_monto,
        'total_ventas_count': total_ventas_count,
        'total_ventas_hoy': total_ventas_hoy,
        'ventas_hoy_count': ventas_hoy_count,
        'unidades_vendidas': unidades_vendidas,
        'ventas_recientes': ventas_recientes,
    }
    return render(request, 'ventas/lista_productos.html', context)

def crear_producto(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        cantidad = request.POST.get('cantidad', '0').strip()
        precio = request.POST.get('precio', '0').strip()
        
        if not codigo or not nombre:
            messages.error(request, "El código y el nombre del producto son campos obligatorios.")
            return render(request, 'ventas/form_producto.html')
            
        if Producto.objects.filter(codigo=codigo).exists():
            messages.error(request, f"Ya existe un producto con el código '{codigo}'. Por favor usa otro código.")
            return render(request, 'ventas/form_producto.html')
            
        try:
            prod = Producto.objects.create(
                codigo=codigo, 
                nombre=nombre, 
                cantidad=int(cantidad), 
                precio=float(precio)
            )
            messages.success(request, f"Producto '{prod.nombre}' creado exitosamente en el inventario.")
            return redirect('lista_productos')
        except Exception as e:
            messages.error(request, f"Error al guardar el producto: {str(e)}")
            return render(request, 'ventas/form_producto.html')
            
    return render(request, 'ventas/form_producto.html')

def editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        cantidad = request.POST.get('cantidad', '0').strip()
        precio = request.POST.get('precio', '0').strip()
        
        if Producto.objects.filter(codigo=codigo).exclude(id=id).exists():
            messages.error(request, f"El código '{codigo}' ya está siendo utilizado por otro producto.")
            return render(request, 'ventas/form_producto.html', {'producto': producto})
            
        try:
            producto.codigo = codigo
            producto.nombre = nombre
            producto.cantidad = int(cantidad)
            producto.precio = float(precio)
            producto.save()
            messages.success(request, f"Producto '{producto.nombre}' actualizado correctamente.")
            return redirect('lista_productos')
        except Exception as e:
            messages.error(request, f"Error al actualizar el producto: {str(e)}")
            return render(request, 'ventas/form_producto.html', {'producto': producto})
            
    return render(request, 'ventas/form_producto.html', {'producto': producto})

def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f"El producto '{nombre}' ha sido eliminado definitivamente del inventario.")
        return redirect('lista_productos')
    return render(request, 'ventas/eliminar_producto.html', {'producto': producto})

def registrar_venta(request):
    productos = Producto.objects.filter(cantidad__gt=0).order_by('nombre')
    if request.method == 'POST':
        rut = request.POST.get('rut', '').strip()
        es_habitual = request.POST.get('es_habitual') == 'on'
        nombre = request.POST.get('nombre', '').strip()
        
        cliente = None
        rut_boleta = rut if rut else "Consumidor Final"
        if es_habitual and rut:
            cliente, created = Cliente.objects.get_or_create(
                rut=rut, 
                defaults={'nombre': nombre if nombre else f"Cliente {rut}"}
            )
            if not created and nombre and cliente.nombre != nombre:
                cliente.nombre = nombre
                cliente.save()
        
        producto_ids = request.POST.getlist('productos')
        cantidades = request.POST.getlist('cantidades')
        
        items_a_vender = []
        for p_id, cant_str in zip(producto_ids, cantidades):
            try:
                cant = int(cant_str)
            except (ValueError, TypeError):
                continue
                
            if cant > 0:
                prod = get_object_or_404(Producto, id=p_id)
                if prod.cantidad < cant:
                    messages.error(
                        request, 
                        f"Stock insuficiente para '{prod.nombre}'. Disponible: {prod.cantidad}, Solicitado: {cant}."
                    )
                    return render(request, 'ventas/registrar_venta.html', {'productos': productos})
                items_a_vender.append((prod, cant))
                
        if not items_a_vender:
            messages.error(request, "Debes seleccionar al menos un producto con cantidad válida para procesar la venta.")
            return render(request, 'ventas/registrar_venta.html', {'productos': productos})

        venta = Venta.objects.create(cliente=cliente, rut_boleta=rut_boleta)
        total = 0
        for prod, cant in items_a_vender:
            DetalleVenta.objects.create(
                venta=venta, producto=prod, cantidad=cant, precio_unitario=prod.precio
            )
            prod.cantidad -= cant
            prod.save()
            total += prod.precio * cant
            
        venta.total = total
        venta.save()
        messages.success(request, f"¡Venta #{venta.id} realizada con éxito! Total: ${int(total):,}")
        return redirect('detalle_venta', id=venta.id)
        
    return render(request, 'ventas/registrar_venta.html', {'productos': productos})

def lista_ventas(request):
    ventas = Venta.objects.select_related('cliente').prefetch_related('detalles').order_by('-fecha')
    total_recaudado = ventas.aggregate(total=Sum('total'))['total'] or 0
    total_transacciones = ventas.count()
    return render(request, 'ventas/lista_ventas.html', {
        'ventas': ventas,
        'total_recaudado': total_recaudado,
        'total_transacciones': total_transacciones
    })

def detalle_venta(request, id):
    venta = get_object_or_404(
        Venta.objects.select_related('cliente').prefetch_related('detalles__producto'), 
        id=id
    )
    return render(request, 'ventas/detalle_venta.html', {'venta': venta})
