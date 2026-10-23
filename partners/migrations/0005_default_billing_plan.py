from decimal import Decimal

from django.db import migrations


def seed_default_plan(apps, schema_editor):
    plan = apps.get_model('partners', 'BillingPlan')
    if not plan.objects.using(schema_editor.connection.alias).exists():
        plan.objects.using(schema_editor.connection.alias).create(
            name='Standard Partner Plan', is_default=True,
            commission_rate=Decimal('5.00'), billing_mode='commission',
            fixed_fee=Decimal('0.00'), minimum_monthly_fee=Decimal('0.00'))


class Migration(migrations.Migration):
    dependencies = [('partners', '0004_companyprofile_visibility_override_billingplan_and_more')]
    operations = [migrations.RunPython(seed_default_plan, migrations.RunPython.noop)]
