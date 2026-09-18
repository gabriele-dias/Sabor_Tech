from django.contrib import admin
<<<<<<< HEAD
from .models import Produto


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'preco')
    search_fields = ('nome',)
=======

# Register your models here.
>>>>>>> Parte_Front/main
