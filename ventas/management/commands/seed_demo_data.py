from django.core.management.base import BaseCommand
from django.utils import timezone
from ventas.models import Producto, Cliente, Venta, DetalleVenta
import random

class Command(BaseCommand):
    help = 'Pobla la base de datos con datos de prueba realistas para demostración comercial del Dashboard'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando carga de datos comerciales de demostración..."))

        # 1. Crear Productos de prueba variados (con stocks normales, bajos y agotados)
        productos_demo = [
            {"codigo": "BEB-001", "nombre": "Coca-Cola Original 1.5L", "cantidad": 24, "precio": 1990},
            {"codigo": "BEB-002", "nombre": "Jugo Naranja Andina 1L", "cantidad": 15, "precio": 1490},
            {"codigo": "BEB-003", "nombre": "Agua Mineral Vital Sin Gas 1.6L", "cantidad": 3, "precio": 990}, # Bajo stock
            {"codigo": "CAF-001", "nombre": "Café Nescafé Tradición 170g", "cantidad": 18, "precio": 4590},
            {"codigo": "LAC-001", "nombre": "Leche Colun Entera 1L", "cantidad": 30, "precio": 1150},
            {"codigo": "LAC-002", "nombre": "Yogurt Soprole Frutilla 120g", "cantidad": 2, "precio": 390}, # Bajo stock
            {"codigo": "PAN-001", "nombre": "Pan de Molde Ideal Blanco 550g", "cantidad": 0, "precio": 2290}, # Agotado
            {"codigo": "GAL-001", "nombre": "Galletas Tritón Chocolate 126g", "cantidad": 40, "precio": 890},
            {"codigo": "ABR-001", "nombre": "Arroz Tucapel Grado 1 1Kg", "cantidad": 22, "precio": 1690},
            {"codigo": "ABR-002", "nombre": "Aceite Maravilla Belmont 900ml", "cantidad": 4, "precio": 2890}, # Bajo stock
        ]

        prods_creados = []
        for p_data in productos_demo:
            p, created = Producto.objects.get_or_create(
                codigo=p_data["codigo"],
                defaults={
                    "nombre": p_data["nombre"],
                    "cantidad": p_data["cantidad"],
                    "precio": p_data["precio"]
                }
            )
            prods_creados.append(p)
            if created:
                self.stdout.write(f"  + Producto creado: {p.nombre} (Stock: {p.cantidad})")
            else:
                self.stdout.write(f"  = Producto existente: {p.nombre}")

        # 2. Crear Clientes de prueba
        clientes_demo = [
            {"rut": "18.423.901-4", "nombre": "Camila Morales Soto"},
            {"rut": "12.834.112-K", "nombre": "Gonzalo Valenzuela R."},
            {"rut": "20.192.833-2", "nombre": "Daniela Figueroa Palma"},
        ]

        clientes_creados = []
        for c_data in clientes_demo:
            c, created = Cliente.objects.get_or_create(
                rut=c_data["rut"],
                defaults={"nombre": c_data["nombre"]}
            )
            clientes_creados.append(c)

        # 3. Crear Ventas de prueba con DetalleVenta
        if Venta.objects.count() == 0:
            self.stdout.write("Generando transacciones de venta de prueba...")
            
            # Venta 1 (Cliente habitual)
            v1 = Venta.objects.create(cliente=clientes_creados[0], rut_boleta=clientes_creados[0].rut)
            p1 = prods_creados[0] # Coca-Cola
            p2 = prods_creados[7] # Galletas
            DetalleVenta.objects.create(venta=v1, producto=p1, cantidad=2, precio_unitario=p1.precio)
            DetalleVenta.objects.create(venta=v1, producto=p2, cantidad=3, precio_unitario=p2.precio)
            v1.total = (p1.precio * 2) + (p2.precio * 3)
            v1.save()

            # Venta 2 (Consumidor Ocasional)
            v2 = Venta.objects.create(cliente=None, rut_boleta="15.223.441-2")
            p3 = prods_creados[3] # Cafe
            DetalleVenta.objects.create(venta=v2, producto=p3, cantidad=1, precio_unitario=p3.precio)
            v2.total = p3.precio * 1
            v2.save()

            # Venta 3 (Cliente habitual)
            v3 = Venta.objects.create(cliente=clientes_creados[1], rut_boleta=clientes_creados[1].rut)
            p4 = prods_creados[4] # Leche
            p5 = prods_creados[8] # Arroz
            DetalleVenta.objects.create(venta=v3, producto=p4, cantidad=4, precio_unitario=p4.precio)
            DetalleVenta.objects.create(venta=v3, producto=p5, cantidad=2, precio_unitario=p5.precio)
            v3.total = (p4.precio * 4) + (p5.precio * 2)
            v3.save()

            self.stdout.write(self.style.SUCCESS("3 ventas de prueba creadas exitosamente!"))

        self.stdout.write(self.style.SUCCESS("[OK] Datos demo cargados correctamente. El dashboard esta listo para visualizacion."))
