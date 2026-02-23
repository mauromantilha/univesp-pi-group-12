from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnaliseRiscoViewSet, SugestaoJurisprudenciaViewSet, chat_juridico

router = DefaultRouter()
router.register(r"analises", AnaliseRiscoViewSet, basename="analise-risco")
router.register(r"sugestoes", SugestaoJurisprudenciaViewSet, basename="sugestao-jurisprudencia")

urlpatterns = [
    path("", include(router.urls)),
    path("chat/", chat_juridico, name="chat-juridico"),
]
