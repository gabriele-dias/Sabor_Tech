from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_tenant_catalog_inventory'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='confirmed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='ready_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
