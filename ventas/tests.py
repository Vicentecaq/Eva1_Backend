from django.test import TestCase, Client
from django.urls import reverse
from ventas.models import Producto, Cliente, Venta, DetalleVenta

class VentasSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.producto1 = Producto.objects.create(
            codigo="TEST-001",
            nombre="Bebida Cola 1.5L",
            cantidad=20,
            precio=1500.00
        )
        self.producto2 = Producto.objects.create(
            codigo="TEST-002",
            nombre="Galletas Vainilla",
            cantidad=4, # Bajo stock (<= 5)
            precio=800.00
        )
        self.producto_agotado = Producto.objects.create(
            codigo="TEST-003",
            nombre="Pan Baguette",
            cantidad=0, # Agotado
            precio=1200.00
        )

    def test_dashboard_view(self):
        response = self.client.get(reverse('lista_productos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TEST-001")
        self.assertContains(response, "Bebida Cola 1.5L")
        self.assertEqual(response.context['total_productos'], 3)
        self.assertEqual(response.context['total_stock'], 24)
        self.assertEqual(response.context['productos_bajo_stock'].count(), 1)
        self.assertEqual(response.context['productos_agotados'].count(), 1)

    def test_crear_producto(self):
        response = self.client.post(reverse('crear_producto'), {
            'codigo': 'NUEVO-001',
            'nombre': 'Jugo Durazno 1L',
            'cantidad': '15',
            'precio': '1290'
        })
        self.assertEqual(response.status_code, 302)
        prod = Producto.objects.filter(codigo='NUEVO-001').first()
        self.assertIsNotNone(prod)
        self.assertEqual(prod.nombre, 'Jugo Durazno 1L')
        self.assertEqual(prod.cantidad, 15)

    def test_editar_producto(self):
        response = self.client.post(reverse('editar_producto', args=[self.producto1.id]), {
            'codigo': 'TEST-001',
            'nombre': 'Bebida Cola 1.5L Zero',
            'cantidad': '25',
            'precio': '1600'
        })
        self.assertEqual(response.status_code, 302)
        self.producto1.refresh_from_db()
        self.assertEqual(self.producto1.nombre, 'Bebida Cola 1.5L Zero')
        self.assertEqual(self.producto1.cantidad, 25)

    def test_eliminar_producto(self):
        prod_id = self.producto_agotado.id
        response = self.client.post(reverse('eliminar_producto', args=[prod_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Producto.objects.filter(id=prod_id).exists())

    def test_registrar_venta_success(self):
        stock_inicial = self.producto1.cantidad
        response = self.client.post(reverse('registrar_venta'), {
            'rut': '12.345.678-9',
            'es_habitual': 'on',
            'nombre': 'Carlos Santander',
            'productos': [str(self.producto1.id), str(self.producto2.id)],
            'cantidades': ['2', '1']
        })
        # Verifica redirección a detalle de venta
        self.assertEqual(response.status_code, 302)
        
        # Verifica creación de venta
        venta = Venta.objects.latest('id')
        self.assertEqual(venta.rut_boleta, '12.345.678-9')
        self.assertIsNotNone(venta.cliente)
        self.assertEqual(venta.cliente.nombre, 'Carlos Santander')
        
        # Total esperado: (1500 * 2) + (800 * 1) = 3800
        self.assertEqual(venta.total, 3800)
        
        # Verifica descuento de stock
        self.producto1.refresh_from_db()
        self.assertEqual(self.producto1.cantidad, stock_inicial - 2)

    def test_historial_y_detalle_venta(self):
        # Crear venta
        venta = Venta.objects.create(rut_boleta='99.999.999-9', total=1500)
        DetalleVenta.objects.create(
            venta=venta,
            producto=self.producto1,
            cantidad=1,
            precio_unitario=self.producto1.precio
        )
        
        # Test lista ventas
        res_list = self.client.get(reverse('lista_ventas'))
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, '99.999.999-9')

        # Test detalle venta
        res_det = self.client.get(reverse('detalle_venta', args=[venta.id]))
        self.assertEqual(res_det.status_code, 200)
        self.assertContains(res_det, f'BOLETA #{venta.id}')
        self.assertContains(res_det, 'Bebida Cola 1.5L')
