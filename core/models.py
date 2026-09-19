from django.db import models
from django.contrib.auth.models import User


class Order(models.Model):
	id = models.BigAutoField(primary_key=True)
	waiter = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')
	items = models.JSONField(default=list)
	subtotal = models.DecimalField(max_digits=10, decimal_places=2)
	service_fee = models.DecimalField(max_digits=10, decimal_places=2)
	total = models.DecimalField(max_digits=10, decimal_places=2)
	status = models.CharField(max_length=20, default='Pendente')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
