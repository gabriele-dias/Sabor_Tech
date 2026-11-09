from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from django.forms import formset_factory
from decimal import Decimal

from .models import Ingredient, KitchenPreparation


class CardapioLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="E-mail",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Digite seu e-mail",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Digite sua senha",
                "autocomplete": "current-password",
            }
        ),
    )


class StaffCreateForm(forms.Form):
    PROFILE_CHOICES = (
        ("garcom", "Garçom"),
        ("administrador", "Administrador"),
        ("cozinheiro", "Cozinheiro"),
        ("auxiliar", "Auxiliar de cozinha"),
    )

    full_name = forms.CharField(
        label="Nome completo",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Ex.: Ana Souza", "autocomplete": "name"}),
    )
    email = forms.EmailField(
        label="E-mail de acesso",
        widget=forms.EmailInput(attrs={"placeholder": "funcionario@restaurante.com", "autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Senha inicial",
        validators=[validate_password],
        widget=forms.PasswordInput(attrs={"placeholder": "Digite uma senha", "autocomplete": "new-password"}),
    )
    profile = forms.ChoiceField(
        label="Perfil de acesso",
        choices=PROFILE_CHOICES,
        widget=forms.RadioSelect,
    )

    def clean_full_name(self):
        return " ".join(self.cleaned_data["full_name"].split())

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email)).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email


class KitchenPreparationForm(forms.Form):
    dish_name = forms.CharField(
        label="Preparo",
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Ex.: Pizza Marguerita"}),
    )
    status = forms.ChoiceField(
        label="Status",
        choices=KitchenPreparation.STATUS_CHOICES,
    )
    duration_minutes = forms.IntegerField(
        label="Duração em minutos",
        min_value=1,
        required=False,
        widget=forms.NumberInput(attrs={"placeholder": "Ex.: 18"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("status") == KitchenPreparation.STATUS_COMPLETED
            and cleaned_data.get("duration_minutes") is None
        ):
            self.add_error("duration_minutes", "Informe a duração do preparo concluído.")
        return cleaned_data


class RecipeCreateForm(forms.Form):
    CATEGORY_CHOICES = (
        ("Pizzas", "Pizzas"),
        ("Lanches", "Lanches"),
        ("Massas", "Massas"),
        ("Bebidas", "Bebidas"),
        ("Sobremesas", "Sobremesas"),
    )

    name = forms.CharField(max_length=120, label="Nome da receita")
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, label="Categoria")
    description = forms.CharField(max_length=240, required=False, label="Descrição")
    sale_price = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"), label="Preço de venda (R$)")
    yield_quantity = forms.IntegerField(min_value=1, label="Rendimento")
    prep_time_minutes = forms.IntegerField(min_value=1, required=False, label="Tempo de preparo (minutos)")

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())


class RecipeIngredientForm(forms.Form):
    UNIT_CHOICES = (
        ("g", "g"),
        ("ml", "ml"),
        ("un", "un."),
    )

    name = forms.CharField(max_length=120, label="Ingrediente")
    quantity = forms.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"), label="Quantidade por receita")
    unit = forms.ChoiceField(choices=UNIT_CHOICES, label="Unidade")
    unit_cost = forms.DecimalField(max_digits=12, decimal_places=4, min_value=Decimal("0"), label="Custo unitário (R$)")

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())


RecipeIngredientFormSet = formset_factory(
    RecipeIngredientForm,
    extra=1,
    min_num=1,
    validate_min=True,
    max_num=50,
    validate_max=True,
    can_delete=True,
)


class StockMovementForm(forms.Form):
    MOVEMENT_CHOICES = (
        ("purchase", "Entrada de compra"),
        ("waste", "Registrar desperdício"),
        ("adjustment", "Ajuste de inventário"),
    )
    DIRECTION_CHOICES = (
        ("in", "Entrada"),
        ("out", "Saída"),
    )

    ingredient = forms.ModelChoiceField(queryset=Ingredient.objects.none(), label="Insumo")
    movement_type = forms.ChoiceField(choices=MOVEMENT_CHOICES, label="Tipo de movimentação")
    direction = forms.ChoiceField(choices=DIRECTION_CHOICES, label="Direção")
    quantity = forms.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"), label="Quantidade")
    unit_cost = forms.DecimalField(max_digits=12, decimal_places=4, min_value=Decimal("0"), required=False, label="Custo unitário (R$)")
    note = forms.CharField(max_length=240, required=False, label="Observação")

    def __init__(self, *args, tenant, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ingredient"].queryset = Ingredient.objects.filter(tenant=tenant, is_active=True).order_by("name")

    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get("movement_type")
        direction = cleaned_data.get("direction")
        if movement_type == "purchase" and direction != "in":
            self.add_error("direction", "Uma compra deve ser registrada como entrada.")
        if movement_type == "waste" and direction != "out":
            self.add_error("direction", "Desperdício deve ser registrado como saída.")
        if movement_type == "purchase" and cleaned_data.get("unit_cost") is None:
            self.add_error("unit_cost", "Informe o custo da compra.")
        return cleaned_data
