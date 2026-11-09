import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from decimal import Decimal, InvalidOperation


def bootstrap_default_tenant(apps, schema_editor):
    Tenant = apps.get_model('core', 'Tenant')
    Unit = apps.get_model('core', 'Unit')
    TenantMembership = apps.get_model('core', 'TenantMembership')
    Product = apps.get_model('core', 'Product')
    Order = apps.get_model('core', 'Order')
    OrderItem = apps.get_model('core', 'OrderItem')
    Client = apps.get_model('core', 'Client')
    KitchenPreparation = apps.get_model('core', 'KitchenPreparation')
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    Group = apps.get_model('auth', 'Group')

    tenant, _ = Tenant.objects.get_or_create(
        slug='sabor-tech-principal',
        defaults={'name': 'Sabor Tech - Unidade principal', 'plan': 'essencial'},
    )
    unit, _ = Unit.objects.get_or_create(
        tenant=tenant,
        name='Unidade principal',
    )

    for user in User.objects.all().iterator():
        group_names = set(
            Group.objects.filter(user__id=user.pk).values_list('name', flat=True)
        )
        if user.is_superuser or 'Gestão' in group_names:
            role = 'owner' if user.is_superuser else 'manager'
        elif 'Garçom' in group_names:
            role = 'waiter'
        elif 'Chefe de Cozinha' in group_names:
            role = 'cook'
        elif 'Auxiliar de cozinha' in group_names:
            role = 'assistant'
        else:
            role = 'manager'
        TenantMembership.objects.get_or_create(
            tenant=tenant,
            user=user,
            defaults={'unit': unit, 'role': role, 'is_active': user.is_active},
        )

    catalog = [
        ('Pizza Calabresa', 'Pizzas', 'Calabresa, queijo e cebola', '🍕', '59.90', True),
        ('Pizza Marguerita', 'Pizzas', 'Queijo, tomate e manjericão', '🍕', '54.90', True),
        ('Frango com Catupiry', 'Pizzas', 'Frango, queijo e catupiry', '🍕', '62.90', True),
        ('Pizza Portuguesa', 'Pizzas', 'Presunto, ovos, queijo e cebola', '🍕', '61.90', True),
        ('X-Bacon', 'Lanches', 'Hambúrguer, bacon e queijo', '🍔', '34.90', True),
        ('X-Salada', 'Lanches', 'Hambúrguer, queijo e salada', '🍔', '32.90', True),
        ('X-Egg Bacon', 'Lanches', 'Hambúrguer, ovo, bacon e queijo', '🍔', '36.90', True),
        ('Frango Grelhado', 'Lanches', 'Frango, queijo e salada', '🍔', '31.90', True),
    ]
    for name, category, description, icon, sale_price, is_available in catalog:
        Product.objects.get_or_create(
            tenant=tenant,
            name=name,
            defaults={
                'category': category,
                'description': description,
                'icon': icon,
                'sale_price': sale_price,
                'is_available': is_available,
            },
        )

    Order.objects.filter(tenant__isnull=True).update(tenant=tenant, unit=unit)
    KitchenPreparation.objects.filter(tenant__isnull=True).update(tenant=tenant, unit=unit)
    for order in Order.objects.filter(tenant=tenant).iterator():
        items = order.items if isinstance(order.items, list) else []
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get('nome', '')).strip()
            if not name:
                continue
            product = Product.objects.filter(tenant=tenant, name__iexact=name).first()
            if product is None:
                continue
            try:
                quantity = max(1, int(item.get('quantidade', 1)))
                unit_price = Decimal(str(item.get('preco', product.sale_price)))
            except (TypeError, ValueError, InvalidOperation):
                continue
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=name,
                quantity=quantity,
                unit_price=unit_price,
            )
        customer_name = next((str(item.get('cliente', '')).strip() for item in items if isinstance(item, dict) and item.get('cliente')), '')
        customer_phone = next((str(item.get('telefone', '')).strip() for item in items if isinstance(item, dict) and item.get('telefone')), '')
        order.customer_name = customer_name
        order.customer_phone = customer_phone
        order.channel = next((str(item.get('canal') or item.get('origem')) for item in items if isinstance(item, dict) and (item.get('canal') or item.get('origem'))), 'presencial')
        table_number = next((item.get('mesa') for item in items if isinstance(item, dict) and item.get('mesa')), None)
        try:
            order.table_number = int(table_number) if table_number is not None else None
        except (TypeError, ValueError):
            order.table_number = None
        if customer_name:
            order.client, _ = Client.objects.get_or_create(
                tenant=tenant,
                name=customer_name,
                phone=customer_phone,
                defaults={'email': ''},
            )
        order.save(update_fields=['customer_name', 'customer_phone', 'channel', 'table_number', 'client'])


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0007_kitchenpreparation_remove_ingrediente_receita_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=160)),
                ('slug', models.SlugField(max_length=180, unique=True)),
                ('plan', models.CharField(choices=[('essencial', 'Essencial'), ('intermediario', 'Intermediário'), ('avancado', 'Avançado')], default='essencial', max_length=20)),
                ('trial_ends_at', models.DateField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=120)),
                ('phone', models.CharField(blank=True, max_length=32)),
                ('address', models.CharField(blank=True, max_length=240)),
                ('is_active', models.BooleanField(default=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='units', to='core.tenant')),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='TenantMembership',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('owner', 'Proprietário'), ('manager', 'Gestão'), ('waiter', 'Garçom'), ('cook', 'Cozinheiro'), ('assistant', 'Auxiliar de cozinha')], default='manager', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='core.tenant')),
                ('unit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='memberships', to='core.unit')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tenant_memberships', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=120)),
                ('unit', models.CharField(choices=[('g', 'g'), ('ml', 'ml'), ('un', 'un.')], default='g', max_length=4)),
                ('stock_quantity', models.DecimalField(decimal_places=3, default=0, max_digits=12)),
                ('minimum_stock', models.DecimalField(decimal_places=3, default=0, max_digits=12)),
                ('unit_cost', models.DecimalField(decimal_places=4, default=0, max_digits=12)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredients', to='core.tenant')),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=120)),
                ('category', models.CharField(max_length=60)),
                ('description', models.CharField(blank=True, max_length=240)),
                ('icon', models.CharField(default='🍽', max_length=12)),
                ('sale_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('is_available', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='core.tenant')),
            ],
            options={'ordering': ['category', 'name']},
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=150)),
                ('phone', models.CharField(blank=True, max_length=32)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='clients', to='core.tenant')),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('yield_quantity', models.PositiveIntegerField(default=1)),
                ('prep_time_minutes', models.PositiveIntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='recipe', to='core.product')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipes', to='core.tenant')),
            ],
            options={'ordering': ['product__name']},
        ),
        migrations.CreateModel(
            name='RecipeIngredient',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('quantity', models.DecimalField(decimal_places=3, max_digits=12)),
                ('ingredient', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='recipes', to='core.ingredient')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredients', to='core.recipe')),
            ],
        ),
        migrations.CreateModel(
            name='InventoryMovement',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('movement_type', models.CharField(choices=[('purchase', 'Compra'), ('consumption', 'Consumo'), ('waste', 'Desperdício'), ('adjustment', 'Ajuste')], max_length=16)),
                ('direction', models.CharField(choices=[('in', 'Entrada'), ('out', 'Saída')], max_length=3)),
                ('quantity', models.DecimalField(decimal_places=3, max_digits=12)),
                ('unit_cost', models.DecimalField(decimal_places=4, max_digits=12)),
                ('note', models.CharField(blank=True, max_length=240)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inventory_movements', to=settings.AUTH_USER_MODEL)),
                ('ingredient', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='movements', to='core.ingredient')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='inventory_movements', to='core.tenant')),
                ('unit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inventory_movements', to='core.unit')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddField(
            model_name='order',
            name='tenant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='core.tenant'),
        ),
        migrations.AddField(
            model_name='order',
            name='unit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='core.unit'),
        ),
        migrations.AddField(
            model_name='order',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='core.client'),
        ),
        migrations.AddField(
            model_name='order',
            name='customer_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='order',
            name='customer_phone',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='order',
            name='channel',
            field=models.CharField(default='presencial', max_length=24),
        ),
        migrations.AddField(
            model_name='order',
            name='table_number',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='kitchenpreparation',
            name='tenant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='kitchen_preparations', to='core.tenant'),
        ),
        migrations.AddField(
            model_name='kitchenpreparation',
            name='unit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='kitchen_preparations', to='core.unit'),
        ),
        migrations.AddField(
            model_name='kitchenpreparation',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='preparations', to='core.order'),
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('product_name', models.CharField(max_length=120)),
                ('quantity', models.PositiveIntegerField()),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='core.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='order_lines', to='core.product')),
            ],
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Pendente', 'Pendente'), ('Em preparo', 'Em preparo'), ('Pronto', 'Pronto'), ('Entregue', 'Entregue'), ('Cancelado', 'Cancelado')], default='Pendente', max_length=20),
        ),
        migrations.AddConstraint(
            model_name='orderitem',
            constraint=models.CheckConstraint(condition=models.Q(('quantity__gt', 0)), name='order_item_quantity_positive'),
        ),
        migrations.AlterField(
            model_name='kitchenpreparation',
            name='status',
            field=models.CharField(choices=[('Pendente', 'Pendente'), ('Em preparo', 'Em preparo'), ('Pronto', 'Pronto'), ('Concluído', 'Concluído')], default='Em preparo', max_length=20),
        ),
        migrations.AlterField(
            model_name='kitchenpreparation',
            name='responsible',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='kitchen_preparations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(bootstrap_default_tenant, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='order',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='core.tenant'),
        ),
        migrations.AlterField(
            model_name='kitchenpreparation',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='kitchen_preparations', to='core.tenant'),
        ),
        migrations.AddConstraint(
            model_name='unit',
            constraint=models.UniqueConstraint(fields=('tenant', 'name'), name='unique_unit_name_per_tenant'),
        ),
        migrations.AddConstraint(
            model_name='tenantmembership',
            constraint=models.UniqueConstraint(fields=('tenant', 'user'), name='unique_user_membership_per_tenant'),
        ),
        migrations.AddConstraint(
            model_name='ingredient',
            constraint=models.UniqueConstraint(fields=('tenant', 'name'), name='unique_ingredient_name_per_tenant'),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.UniqueConstraint(fields=('tenant', 'name'), name='unique_product_name_per_tenant'),
        ),
        migrations.AddConstraint(
            model_name='recipeingredient',
            constraint=models.UniqueConstraint(fields=('recipe', 'ingredient'), name='unique_ingredient_per_recipe'),
        ),
        migrations.AddConstraint(
            model_name='recipeingredient',
            constraint=models.CheckConstraint(condition=models.Q(('quantity__gt', 0)), name='recipe_ingredient_quantity_positive'),
        ),
        migrations.AddConstraint(
            model_name='inventorymovement',
            constraint=models.CheckConstraint(condition=models.Q(('quantity__gt', 0)), name='inventory_movement_quantity_positive'),
        ),
    ]
