from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import (
    Client,
    Ingredient,
    InventoryMovement,
    KitchenPreparation,
    Order,
    OrderItem,
    Product,
    RecipeIngredient,
)


class OrderPayloadError(ValueError):
    pass


class InsufficientStockError(ValueError):
    pass


def _positive_integer(value):
    try:
        quantity = Decimal(str(value))
    except (TypeError, ValueError, InvalidOperation) as error:
        raise OrderPayloadError("A quantidade de cada produto precisa ser válida.") from error
    if quantity <= 0 or quantity != quantity.to_integral_value():
        raise OrderPayloadError("A quantidade de cada produto deve ser um inteiro positivo.")
    return int(quantity)


@transaction.atomic
def create_order_from_payload(*, waiter, membership, payload):
    submitted_items = payload.get("items")
    if not isinstance(submitted_items, list) or not submitted_items:
        raise OrderPayloadError("Adicione ao menos um produto ao pedido.")

    tenant = membership.tenant
    normalized_lines = []
    requirements = {}
    subtotal = Decimal("0.00")

    for submitted in submitted_items:
        if not isinstance(submitted, dict):
            raise OrderPayloadError("Os itens do pedido estão em formato inválido.")

        product = None
        product_id = submitted.get("product_id") or submitted.get("produto_id")
        product_name = submitted.get("nome") or submitted.get("name")
        if product_id:
            try:
                product = Product.objects.filter(tenant=tenant, is_available=True).get(pk=product_id)
            except (Product.DoesNotExist, ValueError, TypeError):
                raise OrderPayloadError("Um produto não existe ou está indisponível no seu cardápio.")
        elif product_name:
            product = Product.objects.filter(
                tenant=tenant,
                is_available=True,
                name__iexact=str(product_name).strip(),
            ).first()
            if product is None:
                raise OrderPayloadError("Um produto não existe ou está indisponível no seu cardápio.")
        else:
            raise OrderPayloadError("Cada item precisa identificar um produto do cardápio.")

        quantity = _positive_integer(submitted.get("quantidade", submitted.get("quantity", 1)))
        line_total = product.sale_price * quantity
        subtotal += line_total
        normalized_lines.append({
            "product": product,
            "quantity": quantity,
            "unit_price": product.sale_price,
            "line_total": line_total,
        })

        recipe = getattr(product, "recipe", None)
        if recipe and recipe.is_active:
            for recipe_line in RecipeIngredient.objects.filter(recipe=recipe).select_related("ingredient"):
                required = recipe_line.quantity * Decimal(quantity) / Decimal(recipe.yield_quantity)
                requirements[recipe_line.ingredient_id] = (
                    requirements.get(recipe_line.ingredient_id, Decimal("0")) + required
                )

    ingredients = {
        ingredient.pk: ingredient
        for ingredient in Ingredient.objects.select_for_update().filter(
            tenant=tenant,
            pk__in=requirements,
            is_active=True,
        )
    }
    for ingredient_id, required in requirements.items():
        ingredient = ingredients.get(ingredient_id)
        if ingredient is None:
            raise OrderPayloadError("A ficha técnica contém um insumo inativo ou de outra empresa.")
        if ingredient.stock_quantity < required:
            raise InsufficientStockError(
                f"Estoque insuficiente de {ingredient.name}: disponível "
                f"{ingredient.stock_quantity} {ingredient.unit}, necessário {required} {ingredient.unit}."
            )

    service_fee = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
    total = subtotal + service_fee
    customer_name = str(payload.get("customer_name", payload.get("cliente", ""))).strip()[:150]
    customer_phone = str(payload.get("customer_phone", payload.get("telefone", ""))).strip()[:32]
    channel = str(payload.get("channel", payload.get("canal", "presencial"))).strip().lower()[:24] or "presencial"
    table_number = payload.get("table_number", payload.get("mesa"))
    try:
        table_number = int(table_number) if table_number not in (None, "") else None
    except (TypeError, ValueError) as error:
        raise OrderPayloadError("O número da mesa deve ser inteiro.") from error
    if table_number is not None and table_number < 1:
        raise OrderPayloadError("O número da mesa precisa ser positivo.")

    client = None
    if customer_phone:
        client = Client.objects.filter(tenant=tenant, phone=customer_phone).first()
        if client is None:
            client = Client.objects.create(
                tenant=tenant,
                name=customer_name or customer_phone,
                phone=customer_phone,
            )
        elif customer_name and client.name != customer_name:
            client.name = customer_name
            client.save(update_fields=["name"])

    order = Order.objects.create(
        waiter=waiter,
        tenant=tenant,
        unit=membership.unit,
        client=client,
        customer_name=customer_name,
        customer_phone=customer_phone,
        channel=channel,
        table_number=table_number,
        items=[
            {
                "produto_id": line["product"].pk,
                "nome": line["product"].name,
                "preco": str(line["unit_price"]),
                "quantidade": line["quantity"],
            }
            for line in normalized_lines
        ],
        subtotal=subtotal,
        service_fee=service_fee,
        total=total,
        status=Order.STATUS_PENDING,
    )

    for line in normalized_lines:
        OrderItem.objects.create(
            order=order,
            product=line["product"],
            product_name=line["product"].name,
            quantity=line["quantity"],
            unit_price=line["unit_price"],
        )
        KitchenPreparation.objects.create(
            dish_name=line["product"].name,
            responsible=None,
            tenant=tenant,
            unit=membership.unit,
            order=order,
            status=KitchenPreparation.STATUS_PENDING,
        )

    for ingredient_id, required in requirements.items():
        ingredient = ingredients[ingredient_id]
        ingredient.stock_quantity -= required
        ingredient.save(update_fields=["stock_quantity"])
        InventoryMovement.objects.create(
            tenant=tenant,
            unit=membership.unit,
            ingredient=ingredient,
            order=order,
            created_by=waiter,
            movement_type=InventoryMovement.Type.CONSUMPTION,
            direction=InventoryMovement.Direction.OUT,
            quantity=required,
            unit_cost=ingredient.unit_cost,
            note=f"Consumo automático do pedido #{order.pk}",
        )

    return order
