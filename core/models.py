<<<<<<< HEAD
from decimal import Decimal

from django.db import models

# Create your models here.

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.nome


class Receita(models.Model):
    nome = models.CharField(max_length=150)
    quantidade_kg = models.DecimalField(max_digits=8, decimal_places=3, default=Decimal("0"))
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criada_em"]

    def __str__(self):
        return self.nome


class Ingrediente(models.Model):
    UNIDADES = [
        ("kg", "kg"),
        ("g", "g"),
        ("L", "L"),
        ("ml", "ml"),
        ("unidade", "unidade"),
    ]
    receita = models.ForeignKey(Receita, on_delete=models.CASCADE, related_name="ingredientes")
    nome = models.CharField(max_length=150)
    quantidade = models.DecimalField(max_digits=10, decimal_places=3)
    unidade = models.CharField(max_length=20, choices=UNIDADES, default="unidade")

    def __str__(self):
        return f"{self.quantidade} {self.unidade} de {self.nome}"
=======
from django.db import models

# Create your models here.
>>>>>>> Parte_Front/main
