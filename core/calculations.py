from decimal import Decimal, InvalidOperation


def calculate_total_insumo(quantidade_por_pessoa, pessoas):
    """Calcula a quantidade total de insumo para o número de pessoas."""
    if pessoas <= 0:
        raise ValueError("A quantidade de pessoas deve ser maior que zero.")
    return Decimal(str(quantidade_por_pessoa)) * Decimal(str(pessoas))


def calculate_custo_total(total_insumo, custo_unitario):
    """Calcula o custo total pelo insumo e seu custo unitário."""
    return Decimal(str(total_insumo)) * Decimal(str(custo_unitario))


def calculate_custo_por_pessoa(custo_total, pessoas):
    """Calcula o custo por pessoa."""
    if pessoas <= 0:
        raise ValueError("A quantidade de pessoas deve ser maior que zero.")
    return Decimal(str(custo_total)) / Decimal(str(pessoas))


def calculate_receita(quantidade_por_pessoa, pessoas, custo_unitario):
    """Retorna todos os resultados da lógica da receita."""
    total_insumo = calculate_total_insumo(quantidade_por_pessoa, pessoas)
    custo_total = calculate_custo_total(total_insumo, custo_unitario)
    custo_por_pessoa = calculate_custo_por_pessoa(custo_total, pessoas)

    return {
        "quantidade_por_pessoa": Decimal(str(quantidade_por_pessoa)),
        "pessoas": pessoas,
        "custo_unitario": Decimal(str(custo_unitario)),
        "total_insumo": total_insumo,
        "custo_total": custo_total,
        "custo_por_pessoa": custo_por_pessoa,
    }


def calculate_orders_total(orders):
	total = Decimal("0.00")

	for order in orders:
		try:
			value = Decimal(str(order["valor"]))
		except (KeyError, TypeError, ValueError, InvalidOperation) as error:
			raise ValueError("Cada pedido precisa ter um valor válido.") from error

		if value < 0:
			raise ValueError("O valor do pedido não pode ser negativo.")

		total += value

	return total