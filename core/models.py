from django.db import models
from django.contrib.auth.models import User


class Tenant(models.Model):
	class Plan(models.TextChoices):
		ESSENCIAL = 'essencial', 'Essencial'
		INTERMEDIARIO = 'intermediario', 'Intermediário'
		AVANCADO = 'avancado', 'Avançado'

	id = models.BigAutoField(primary_key=True)
	name = models.CharField(max_length=160)
	slug = models.SlugField(max_length=180, unique=True)
	plan = models.CharField(max_length=20, choices=Plan.choices, default=Plan.ESSENCIAL)
	trial_ends_at = models.DateField(null=True, blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name


class Unit(models.Model):
	id = models.BigAutoField(primary_key=True)
	tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='units')
	name = models.CharField(max_length=120)
	phone = models.CharField(max_length=32, blank=True)
	address = models.CharField(max_length=240, blank=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ['name']
		constraints = [models.UniqueConstraint(fields=['tenant', 'name'], name='unique_unit_name_per_tenant')]

	def __str__(self):
		return f'{self.tenant}: {self.name}'


class TenantMembership(models.Model):
	class Role(models.TextChoices):
		OWNER = 'owner', 'Proprietário'
		MANAGER = 'manager', 'Gestão'
		WAITER = 'waiter', 'Garçom'
		COOK = 'cook', 'Cozinheiro'
		ASSISTANT = 'assistant', 'Auxiliar de cozinha'

	id = models.BigAutoField(primary_key=True)
	tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='memberships')
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_memberships')
	unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='memberships')
	role = models.CharField(max_length=20, choices=Role.choices, default=Role.MANAGER)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=['tenant', 'user'], name='unique_user_membership_per_tenant')]


class Product(models.Model):
	id = models.BigAutoField(primary_key=True)
	tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='products')
	name = models.CharField(max_length=120)
	category = models.CharField(max_length=60)
	description = models.CharField(max_length=240, blank=True)
	icon = models.CharField(max_length=12, default='🍽')
	sale_price = models.DecimalField(max_digits=10, decimal_places=2)
	is_available = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['category', 'name']
		constraints = [models.UniqueConstraint(fields=['tenant', 'name'], name='unique_product_name_per_tenant')]

	def __str__(self):
		return self.name


class Client(models.Model):
	id = models.BigAutoField(primary_key=True)
	tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='clients')
	name = models.CharField(max_length=150)
	phone = models.CharField(max_length=32, blank=True)
	email = models.EmailField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name


class Ingredient(models.Model):
	class Unit(models.TextChoices):
		GRAM = 'g', 'g'
		MILLILITER = 'ml', 'ml'
		UNIT = 'un', 'un.'

	id = models.BigAutoField(primary_key=True)
	tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='ingredients')
	name = models.CharField(max_length=120)
	unit = models.CharField(max_length=4, choices=Unit.choices, default=Unit.GRAM)
	stock_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
	minimum_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0)
	unit_cost = models.DecimalField(max_digits=12, decimal_places=4, default=0)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['name']
		constraints = [models.UniqueConstraint(fields=['tenant', 'name'], name='unique_ingredient_name_per_tenant')]

	def __str__(self):
		return f'{self.name} ({self.unit})'


class Recipe(models.Model):
	id = models.BigAutoField(primary_key=True)
	tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='recipes')
	product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='recipe')
	yield_quantity = models.PositiveIntegerField(default=1)
	prep_time_minutes = models.PositiveIntegerField(null=True, blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['product__name']


class RecipeIngredient(models.Model):
	id = models.BigAutoField(primary_key=True)
	recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
	ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, related_name='recipes')
	quantity = models.DecimalField(max_digits=12, decimal_places=3)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['recipe', 'ingredient'], name='unique_ingredient_per_recipe'),
			models.CheckConstraint(condition=models.Q(quantity__gt=0), name='recipe_ingredient_quantity_positive'),
		]


class Order(models.Model):
	STATUS_PENDING = 'Pendente'
	STATUS_PREPARING = 'Em preparo'
	STATUS_READY = 'Pronto'
	STATUS_DELIVERED = 'Entregue'
	STATUS_CANCELLED = 'Cancelado'
	STATUS_CHOICES = (
		(STATUS_PENDING, STATUS_PENDING),
		(STATUS_PREPARING, STATUS_PREPARING),
		(STATUS_READY, STATUS_READY),
		(STATUS_DELIVERED, STATUS_DELIVERED),
		(STATUS_CANCELLED, STATUS_CANCELLED),
	)

	id = models.BigAutoField(primary_key=True)
	waiter = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')
	tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name='orders')
	unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, related_name='orders', null=True, blank=True)
	client = models.ForeignKey(Client, on_delete=models.SET_NULL, related_name='orders', null=True, blank=True)
	customer_name = models.CharField(max_length=150, blank=True)
	customer_phone = models.CharField(max_length=32, blank=True)
	channel = models.CharField(max_length=24, default='presencial')
	table_number = models.PositiveSmallIntegerField(null=True, blank=True)
	items = models.JSONField(default=list)
	subtotal = models.DecimalField(max_digits=10, decimal_places=2)
	service_fee = models.DecimalField(max_digits=10, decimal_places=2)
	total = models.DecimalField(max_digits=10, decimal_places=2)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def save(self, *args, **kwargs):
		if not self.tenant_id:
			membership = self.waiter.tenant_memberships.filter(is_active=True, tenant__is_active=True).select_related('tenant', 'unit').first()
			if membership is None:
				raise ValueError('O garçom precisa estar associado a uma empresa ativa.')
			self.tenant = membership.tenant
			self.unit = self.unit or membership.unit
		super().save(*args, **kwargs)


class OrderItem(models.Model):
	id = models.BigAutoField(primary_key=True)
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='lines')
	product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_lines')
	product_name = models.CharField(max_length=120)
	quantity = models.PositiveIntegerField()
	unit_price = models.DecimalField(max_digits=10, decimal_places=2)

	class Meta:
		constraints = [models.CheckConstraint(condition=models.Q(quantity__gt=0), name='order_item_quantity_positive')]


class KitchenPreparation(models.Model):
	id = models.BigAutoField(primary_key=True)
	STATUS_PENDING = 'Pendente'
	STATUS_IN_PROGRESS = 'Em preparo'
	STATUS_READY = 'Pronto'
	STATUS_COMPLETED = 'Concluído'
	STATUS_CHOICES = (
		(STATUS_PENDING, STATUS_PENDING),
		(STATUS_IN_PROGRESS, STATUS_IN_PROGRESS),
		(STATUS_READY, STATUS_READY),
		(STATUS_COMPLETED, STATUS_COMPLETED),
	)

	dish_name = models.CharField(max_length=120)
	responsible = models.ForeignKey(
		User,
		on_delete=models.PROTECT,
		null=True,
		blank=True,
		related_name='kitchen_preparations',
	)
	tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name='kitchen_preparations')
	unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, related_name='kitchen_preparations', null=True, blank=True)
	order = models.ForeignKey(Order, on_delete=models.SET_NULL, related_name='preparations', null=True, blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
	duration_minutes = models.PositiveIntegerField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def save(self, *args, **kwargs):
		if not self.tenant_id:
			membership = self.responsible.tenant_memberships.filter(is_active=True, tenant__is_active=True).select_related('tenant', 'unit').first() if self.responsible_id else None
			if membership is None:
				raise ValueError('O responsável pelo preparo precisa estar associado a uma empresa ativa.')
			self.tenant = membership.tenant
			self.unit = self.unit or membership.unit
		super().save(*args, **kwargs)


class InventoryMovement(models.Model):
	class Type(models.TextChoices):
		PURCHASE = 'purchase', 'Compra'
		CONSUMPTION = 'consumption', 'Consumo'
		WASTE = 'waste', 'Desperdício'
		ADJUSTMENT = 'adjustment', 'Ajuste'

	class Direction(models.TextChoices):
		IN = 'in', 'Entrada'
		OUT = 'out', 'Saída'

	id = models.BigAutoField(primary_key=True)
	tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name='inventory_movements')
	unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, related_name='inventory_movements', null=True, blank=True)
	ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, related_name='movements')
	order = models.ForeignKey(Order, on_delete=models.SET_NULL, related_name='inventory_movements', null=True, blank=True)
	created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='inventory_movements', null=True, blank=True)
	movement_type = models.CharField(max_length=16, choices=Type.choices)
	direction = models.CharField(max_length=3, choices=Direction.choices)
	quantity = models.DecimalField(max_digits=12, decimal_places=3)
	unit_cost = models.DecimalField(max_digits=12, decimal_places=4)
	note = models.CharField(max_length=240, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		constraints = [models.CheckConstraint(condition=models.Q(quantity__gt=0), name='inventory_movement_quantity_positive')]
