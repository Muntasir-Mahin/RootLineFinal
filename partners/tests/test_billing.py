from datetime import date, datetime, time, timedelta
from decimal import Decimal
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from partners.billing_services import (default_plan, generate_invoice, mark_invoice_paid,
    month_start, submit_invoice_payment)
from partners.models import (CompanyBillingSettings, CompanyProfile, Invoice,
    InvoicePaymentSubmission, PartnerAuditLog)
from partners.order_services import adjust_ledger, report_manual_sale
from partners.storage import PartnerPrivateStorage
from .helpers import make_company


class PartnerBillingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company()
        cls.other = make_company('Other farm')
        cls.owner = get_user_model().objects.create_superuser('owner', 'owner@example.com', 'Owner-demo-942!')
        cls.month = month_start(timezone.localdate())

    def sale(self, amount='1000', company=None, when=None):
        return report_manual_sale((company or self.company).pk, actor=(company or self.company).user,
            data={'amount':amount, 'sale_date':when or timezone.localdate(), 'reference':'Phone order'})

    def test_default_commission_rounding_and_idempotent_command_and_action(self):
        self.assertEqual(default_plan().commission_rate, Decimal('5.00'))
        self.sale('1234.56')
        invoice, created = generate_invoice(self.company.pk, self.month)
        self.assertTrue(created)
        self.assertEqual(invoice.commission_amount, Decimal('61.73'))
        self.assertEqual(invoice.total_due, Decimal('61.73'))
        audits = PartnerAuditLog.objects.count()
        second, created = generate_invoice(self.company.pk, self.month)
        self.assertEqual(second.pk, invoice.pk)
        self.assertFalse(created)
        self.assertEqual(PartnerAuditLog.objects.count(), audits)
        self.assertEqual(invoice.lines.count(), 1)
        call_command('generate_partner_invoices', month=self.month.strftime('%Y-%m'), company=self.company.pk, stdout=StringIO())
        self.client.force_login(self.owner)
        response = self.client.post(reverse('admin:partners_companyprofile_changelist'), {
            'action':'generate_monthly_invoices', '_selected_action':[str(self.company.pk)],
            'month':self.month.strftime('%Y-%m')})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Invoice.objects.filter(company=self.company).count(), 1)

    def test_three_modes_minimum_and_per_company_zero_override(self):
        self.sale('1000')
        plan = default_plan()
        plan.fixed_fee, plan.minimum_monthly_fee = Decimal('80'), Decimal('60')
        plan.save()
        for mode, expected in [('commission', '60'), ('subscription', '80'), ('higher', '80')]:
            with self.subTest(mode=mode):
                # Use an independent company/month: issued policy snapshots must not change.
                company = make_company('Mode ' + mode)
                self.sale(company=company)
                plan.billing_mode = mode
                plan.save()
                invoice, _ = generate_invoice(company.pk, self.month)
                self.assertEqual(invoice.total_due, Decimal(expected))
        CompanyBillingSettings.objects.create(company=self.company, plan=plan,
            billing_mode='commission', commission_rate=0, minimum_monthly_fee=0)
        invoice, _ = generate_invoice(self.company.pk, self.month)
        self.assertEqual(invoice.total_due, 0)
        self.assertEqual(invoice.status, 'paid')

    def test_unpaid_invoice_refreshes_and_paid_invoice_freezes_with_review_flag(self):
        ledger = self.sale()
        invoice, _ = generate_invoice(self.company.pk, self.month)
        adjust_ledger(ledger.pk, actor=self.owner, amount='800', reason='Corrected actual sale')
        invoice.refresh_from_db()
        self.assertEqual(invoice.total_due, Decimal('40'))
        self.assertEqual(invoice.lines.get().amount, Decimal('800'))
        plan = default_plan()
        plan.commission_rate = 20
        plan.save()
        invoice, _ = generate_invoice(self.company.pk, self.month)
        self.assertEqual(invoice.commission_rate, Decimal('5'))
        mark_invoice_paid(invoice.pk, actor=self.owner, reason='Checked bank statement')
        adjust_ledger(ledger.pk, actor=self.owner, amount='900', reason='Late correction', resolve=True)
        invoice.refresh_from_db()
        ledger.refresh_from_db()
        self.assertEqual(invoice.total_due, Decimal('40'))
        self.assertEqual(invoice.lines.get().amount, Decimal('800'))
        self.assertTrue(ledger.needs_review)

    def test_yearly_subscription_and_higher_floor_not_charged_twice(self):
        january = date(2025, 1, 1)
        february = date(2025, 2, 1)
        march = date(2025, 3, 1)
        for mode in ('subscription', 'higher'):
            company = make_company('Yearly ' + mode)
            company.approved_at = timezone.make_aware(datetime.combine(january, time()))
            company.save()
            CompanyBillingSettings.objects.create(company=company, plan=default_plan(),
                billing_mode=mode, fixed_fee=100, subscription_period='yearly')
            self.sale('1000', company=company, when=january)
            self.sale('2000', company=company, when=march)
            first, _ = generate_invoice(company.pk, january)
            self.assertEqual(first.total_due, Decimal('100'))
            second, _ = generate_invoice(company.pk, february)
            self.assertEqual(second.total_due, 0)
            third, _ = generate_invoice(company.pk, march)
            self.assertEqual(third.total_due, Decimal('50') if mode == 'higher' else 0)
        # Generating March first backfills the annual floor in January.
        company = make_company('Backfill farm')
        company.approved_at = timezone.make_aware(datetime.combine(january, time()))
        company.save()
        CompanyBillingSettings.objects.create(company=company, plan=default_plan(),
            billing_mode='higher', fixed_fee=100, subscription_period='yearly')
        invoice, _ = generate_invoice(company.pk, march)
        self.assertEqual(invoice.total_due, 0)
        self.assertEqual(company.invoices.count(), 3)
        self.assertEqual(sum(company.invoices.values_list('total_due', flat=True)), Decimal('100'))

    def test_overdue_hides_all_public_routes_but_not_dashboard_and_payment_restores(self):
        self.sale()
        invoice, _ = generate_invoice(self.company.pk, self.month)
        invoice.due_date = timezone.localdate() - timedelta(days=10)
        invoice.suspend_on = timezone.localdate() - timedelta(days=3)
        invoice.save()
        self.assertFalse(CompanyProfile.objects.public().filter(pk=self.company.pk).exists())
        self.assertEqual(self.client.get(self.company.get_absolute_url()).status_code, 404)
        self.client.force_login(self.company.user)
        self.assertContains(self.client.get(reverse('partners:billing')), 'Payment is overdue')
        call_command('update_partner_billing', stdout=StringIO())
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'overdue')
        self.company.visibility_override = 'allow'
        self.company.save()
        self.assertTrue(CompanyProfile.objects.public().filter(pk=self.company.pk).exists())
        self.company.is_suspended = True
        self.company.save()
        self.assertFalse(CompanyProfile.objects.public().filter(pk=self.company.pk).exists())
        self.company.is_suspended, self.company.visibility_override = False, 'auto'
        self.company.save()
        with self.assertRaises(PermissionDenied):
            mark_invoice_paid(invoice.pk, actor=self.company.user, reason='Trust me')
        with self.assertRaises(ValidationError):
            mark_invoice_paid(invoice.pk, actor=self.owner, reason='')
        mark_invoice_paid(invoice.pk, actor=self.owner, reason='Verified receipt')
        self.assertTrue(CompanyProfile.objects.public().filter(pk=self.company.pk).exists())

    def test_invoice_ownership_private_proof_and_admin_verification(self):
        self.sale()
        invoice, _ = generate_invoice(self.company.pk, self.month)
        self.client.force_login(self.other.user)
        url = reverse('partners:invoice_detail', args=[invoice.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {'reference':'Forged'}).status_code, 404)
        with self.assertRaises(PermissionDenied):
            submit_invoice_payment(invoice.pk, actor=self.other.user, reference='Forged')
        field = InvoicePaymentSubmission._meta.get_field('screenshot')
        with TemporaryDirectory() as directory, override_settings(BASE_DIR=Path(directory)):
            with patch.object(field, 'storage', PartnerPrivateStorage()):
                image = BytesIO()
                Image.new('RGB', (10, 10)).save(image, format='PNG')
                self.client.force_login(self.company.user)
                response = self.client.post(url, {'reference':'bank-demo-123', 'screenshot':
                    SimpleUploadedFile('receipt.png', image.getvalue(), content_type='image/png')})
                self.assertEqual(response.status_code, 302)
                proof = InvoicePaymentSubmission.objects.get()
                invoice.refresh_from_db()
                self.assertEqual(invoice.status, 'unpaid')
                with self.assertRaises(ValueError):
                    _ = proof.screenshot.url
                proof_url = reverse('partners:payment_proof', args=[proof.pk])
                self.assertEqual(self.client.get(proof_url).status_code, 200)
                self.client.force_login(self.other.user)
                self.assertEqual(self.client.get(proof_url).status_code, 403)
                self.client.force_login(self.owner)
                self.assertEqual(self.client.get(proof_url).status_code, 200)
                self.assertEqual(self.client.get(reverse('admin:partners_invoicepaymentsubmission_change', args=[proof.pk])).status_code, 200)
                self.client.post(reverse('admin:partners_invoice_changelist'), {'action':'verify_paid',
                    '_selected_action':[str(invoice.pk)], 'reason':'Matched bank-demo-123 to statement'})
                invoice.refresh_from_db()
                self.assertEqual(invoice.status, 'paid')
                proof.refresh_from_db()
                self.assertEqual(proof.reviewed_by, self.owner)

    def test_owner_report_and_csv_escape_spreadsheet_formulas(self):
        ledger = self.sale()
        ledger.reference = '=HYPERLINK("bad")'
        ledger.save()
        generate_invoice(self.company.pk, self.month)
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(reverse('admin:partners_billing_report')), 'Agro Partners billing report')
        self.assertContains(self.client.get(reverse('admin:partners_ledger_csv')), "'=HYPERLINK", html=False)
        self.assertContains(self.client.get(reverse('admin:partners_invoices_csv')), 'Calculated commission')
        self.client.force_login(self.company.user)
        self.assertEqual(self.client.get(reverse('admin:partners_ledger_csv')).status_code, 403)
