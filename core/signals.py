from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Tenant, TenantMembership, Unit


@receiver(post_save, sender=get_user_model())
def attach_user_to_single_tenant(sender, instance, created, **kwargs):
    if not created or instance.tenant_memberships.exists():
        return

    active_tenants = Tenant.objects.filter(is_active=True)
    if active_tenants.count() != 1:
        return

    tenant = active_tenants.first()
    unit = Unit.objects.filter(tenant=tenant, is_active=True).order_by("id").first()
    role = "owner" if instance.is_superuser else "manager"
    TenantMembership.objects.get_or_create(
        tenant=tenant,
        user=instance,
        defaults={"unit": unit, "role": role, "is_active": instance.is_active},
    )
