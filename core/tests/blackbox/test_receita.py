import pytest
from decimal import Decimal
from core.calculations import calculate_receita, calculate_orders_total

def test_calculate_receita_valores_validos():
    result = calculate_receita(100, 5, 2.5)
    assert result["total_insumo"] == Decimal("500")
    assert result["custo_total"] == Decimal("1250")
    assert result["custo_por_pessoa"] == Decimal("250")

def test_calculate_receita_pessoas_zero():
    with pytest.raises(ValueError):
        calculate_receita(100, 0, 2.5)

def test_calculate_orders_total_valores_validos():
    orders = [{"valor": 10}, {"valor": 20}, {"valor": 30}]
    total = calculate_orders_total(orders)
    assert total == Decimal("60")

def test_calculate_orders_total_valor_invalido():
    orders = [{"valor": -5}]
    with pytest.raises(ValueError):
        calculate_orders_total(orders)

def test_calculate_orders_total_chave_invalida():
    orders = [{"preco": 10}]
    with pytest.raises(ValueError):
        calculate_orders_total(orders)
