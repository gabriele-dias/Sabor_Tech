from .models import TenantMembership


def membership_for_user(user):
    if not user.is_authenticated:
        return None
    return (
        TenantMembership.objects.filter(
            user=user,
            is_active=True,
            tenant__is_active=True,
        )
        .select_related("tenant", "unit")
        .order_by("id")
        .first()
    )


def membership_for_request(request):
    memberships = TenantMembership.objects.filter(
        user=request.user,
        is_active=True,
        tenant__is_active=True,
    ).select_related("tenant", "unit")
    selected_id = request.session.get("tenant_membership_id")
    if selected_id:
        selected = memberships.filter(pk=selected_id).first()
        if selected:
            return selected
        request.session.pop("tenant_membership_id", None)
    return memberships.order_by("id").first()
