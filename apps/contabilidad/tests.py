from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.core.testing import crear_escenario

from .models import Cobro, Pago, TipoArancel


def crear_cobro(esc, monto='100000', dias_vencimiento=10, indice_matricula=0):
    arancel, _ = TipoArancel.objects.get_or_create(
        nombre='Mensualidad', defaults={'monto_base': Decimal('100000')})
    return Cobro.objects.create(
        matricula=esc.matriculas[indice_matricula], tipo_arancel=arancel,
        periodo=f'{esc.anio}-03', monto=Decimal(monto),
        fecha_vencimiento=timezone.localdate() + timedelta(days=dias_vencimiento))


class CobroPagoModeloTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()

    def test_cobro_unico_por_matricula_arancel_periodo(self):
        cobro = crear_cobro(self.esc)
        with self.assertRaises(IntegrityError):
            Cobro.objects.create(
                matricula=cobro.matricula, tipo_arancel=cobro.tipo_arancel,
                periodo=cobro.periodo, monto=cobro.monto,
                fecha_vencimiento=cobro.fecha_vencimiento)

    def test_pago_parcial_mantiene_pendiente_y_completo_paga(self):
        cobro = crear_cobro(self.esc)
        Pago.objects.create(cobro=cobro, monto_pagado=Decimal('40000'),
                            medio_pago='efectivo', registrado_por=self.esc.admin)
        cobro.refresh_from_db()
        self.assertEqual(cobro.estado, Cobro.Estado.PENDIENTE)
        self.assertEqual(cobro.saldo_pendiente, Decimal('60000'))

        Pago.objects.create(cobro=cobro, monto_pagado=Decimal('60000'),
                            medio_pago='transferencia', registrado_por=self.esc.admin)
        cobro.refresh_from_db()
        self.assertEqual(cobro.estado, Cobro.Estado.PAGADO)
        self.assertEqual(cobro.saldo_pendiente, Decimal('0'))

    def test_clean_rechaza_sobrepago(self):
        cobro = crear_cobro(self.esc)
        Pago.objects.create(cobro=cobro, monto_pagado=Decimal('90000'),
                            medio_pago='efectivo', registrado_por=self.esc.admin)
        pago = Pago(cobro=cobro, monto_pagado=Decimal('20000'),
                    medio_pago='efectivo', registrado_por=self.esc.admin)
        with self.assertRaises(ValidationError):
            pago.full_clean()

    def test_clean_rechaza_pago_a_condonado(self):
        cobro = crear_cobro(self.esc)
        cobro.estado = Cobro.Estado.CONDONADO
        cobro.save(update_fields=['estado'])
        pago = Pago(cobro=cobro, monto_pagado=Decimal('1000'),
                    medio_pago='efectivo', registrado_por=self.esc.admin)
        with self.assertRaises(ValidationError):
            pago.full_clean()

    def test_comando_marcar_vencidos(self):
        cobro = crear_cobro(self.esc, dias_vencimiento=-5)
        call_command('marcar_vencidos')
        cobro.refresh_from_db()
        self.assertEqual(cobro.estado, Cobro.Estado.VENCIDO)

    def test_pago_auditado_con_historial(self):
        cobro = crear_cobro(self.esc)
        pago = Pago.objects.create(cobro=cobro, monto_pagado=Decimal('100000'),
                                   medio_pago='efectivo',
                                   registrado_por=self.esc.admin)
        self.assertEqual(pago.history.count(), 1)


class ContabilidadVistasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.esc = crear_escenario()
        cls.cobro = crear_cobro(cls.esc)

    def test_profesor_y_apoderado_sin_acceso_a_contabilidad(self):
        for usuario in (self.esc.profesor, self.esc.apoderados[0].usuario):
            self.client.force_login(usuario)
            self.assertEqual(
                self.client.get('/panel/contabilidad/').status_code, 403)

    def test_admin_ve_listado_y_registra_pago(self):
        self.client.force_login(self.esc.admin)
        self.assertContains(
            self.client.get('/panel/contabilidad/'), 'Registrar pago')
        respuesta = self.client.post(
            f'/panel/contabilidad/cobro/{self.cobro.pk}/pago/',
            {'monto_pagado': '100000',
             'fecha_pago': timezone.localdate().isoformat(),
             'medio_pago': 'transferencia', 'observacion': ''})
        self.assertEqual(respuesta.status_code, 302)
        self.cobro.refresh_from_db()
        self.assertEqual(self.cobro.estado, Cobro.Estado.PAGADO)
        pago = self.cobro.pagos.first()
        self.assertEqual(pago.history.first().history_user, self.esc.admin)

    def test_generacion_masiva_crea_y_omite_existentes(self):
        self.client.force_login(self.esc.admin)
        datos = {
            'tipo_arancel': self.cobro.tipo_arancel.pk,
            'periodo': f'{self.esc.anio}-04', 'monto': '',
            'fecha_vencimiento': date(self.esc.anio, 4, 5).isoformat(),
            'curso': '',
        }
        self.client.post('/panel/contabilidad/generar/', datos)
        self.assertEqual(
            Cobro.objects.filter(periodo=f'{self.esc.anio}-04').count(), 2)
        self.client.post('/panel/contabilidad/generar/', datos)  # repetir
        self.assertEqual(
            Cobro.objects.filter(periodo=f'{self.esc.anio}-04').count(), 2)

    def test_mi_cuenta_solo_apoderado_y_solo_sus_pupilos(self):
        self.client.force_login(self.esc.profesor)
        self.assertEqual(self.client.get('/panel/mi-cuenta/').status_code, 403)

        self.client.force_login(self.esc.apoderados[0].usuario)
        respuesta = self.client.get('/panel/mi-cuenta/')
        self.assertContains(respuesta, self.esc.alumnos[0].usuario.get_full_name())
        self.assertNotContains(respuesta, self.esc.alumnos[1].usuario.get_full_name())

    def test_comprobante_pdf_admin_y_apoderado_vinculado(self):
        pago = Pago.objects.create(
            cobro=self.cobro, monto_pagado=Decimal('100000'),
            medio_pago='efectivo', registrado_por=self.esc.admin)
        url = f'/panel/contabilidad/pago/{pago.pk}/comprobante.pdf'

        self.client.force_login(self.esc.admin)
        respuesta = self.client.get(url)
        self.assertEqual(respuesta['Content-Type'], 'application/pdf')
        self.assertTrue(respuesta.content.startswith(b'%PDF'))

        self.client.force_login(self.esc.apoderados[0].usuario)  # su pupilo
        self.assertEqual(self.client.get(url).status_code, 200)

        self.client.force_login(self.esc.apoderados[1].usuario)  # ajeno
        self.assertEqual(self.client.get(url).status_code, 404)

        self.client.force_login(self.esc.profesor)
        self.assertEqual(self.client.get(url).status_code, 403)
