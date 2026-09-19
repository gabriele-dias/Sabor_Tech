from django.db import migrations


def create_waiter_role(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='Garçom')


def delete_waiter_role(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Garçom').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_alter_receita_quantidade_kg_ingrediente'),
    ]

    operations = [
        migrations.RunPython(create_waiter_role, delete_waiter_role),
    ]