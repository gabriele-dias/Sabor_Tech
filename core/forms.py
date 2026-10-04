from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q

from .models import KitchenPreparation


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
