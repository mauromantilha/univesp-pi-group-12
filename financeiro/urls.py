from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("contas", views.ContaBancariaViewSet, basename="contabancaria")
router.register("categorias", views.PlanoContasViewSet, basename="planocontas")
router.register("lancamentos", views.LancamentoFinanceiroViewSet, basename="lancamento")

urlpatterns = [
    path("", include(router.urls)),
]
