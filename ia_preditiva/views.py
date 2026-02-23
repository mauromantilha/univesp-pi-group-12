from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from .models import AnaliseRisco, SugestaoJurisprudencia
from .serializers import AnaliseRiscoSerializer, SugestaoJurisprudenciaSerializer
from processos.models import Processo
import os


def get_groq_client():
    from groq import Groq
    api_key = os.environ.get("GROQ_API_KEY") or getattr(settings, "GROQ_API_KEY", "")
    return Groq(api_key=api_key)


class AnaliseRiscoViewSet(viewsets.ModelViewSet):
    queryset = AnaliseRisco.objects.select_related("processo").all()
    serializer_class = AnaliseRiscoSerializer

    @action(detail=False, methods=["post"], url_path="analisar")
    def analisar(self, request):
        processo_id = request.data.get("processo_id")
        if not processo_id:
            return Response({"erro": "processo_id obrigatorio"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            processo = Processo.objects.select_related(
                "cliente", "advogado_responsavel", "vara", "tipo_processo"
            ).get(pk=processo_id)
        except Processo.DoesNotExist:
            return Response({"erro": "Processo nao encontrado"}, status=status.HTTP_404_NOT_FOUND)

        from jurisprudencia.models import Documento
        similares = Documento.objects.filter(tipo_processo=processo.tipo_processo)
        total = similares.count()
        procedentes = similares.filter(resultado__icontains="procedente").count()
        prob_base = (procedentes / total) if total > 0 else 0.5

        prompt = (
            "Voce e um assistente juridico especializado em analise de risco processual brasileiro.\n\n"
            "Analise o seguinte processo e forneca:\n"
            "1. Probabilidade de exito (0.0 a 1.0)\n"
            "2. Nivel de risco: baixo, medio ou alto\n"
            "3. Justificativa detalhada (3-5 paragrafos)\n"
            "4. Pontos fortes do caso\n"
            "5. Pontos de atencao\n\n"
            "DADOS DO PROCESSO:\n"
            "- Numero: " + str(processo.numero) + "\n"
            "- Tipo: " + str(processo.tipo_processo.nome) + "\n"
            "- Status: " + str(processo.get_status_display()) + "\n"
            "- Polo do cliente: " + str(processo.get_polo_display()) + "\n"
            "- Parte contraria: " + str(processo.parte_contraria or "Nao informado") + "\n"
            "- Vara: " + str(processo.vara or "Nao informado") + "\n"
            "- Valor da causa: R$ " + str(processo.valor_causa or "Nao informado") + "\n"
            "- Descricao: " + str(processo.descricao or "Sem descricao") + "\n"
            "- Historico: " + str(total) + " decisoes similares, " + str(procedentes) + " procedentes\n\n"
            "Responda APENAS com JSON valido:\n"
            '{"probabilidade_exito": 0.XX, "nivel_risco": "baixo|medio|alto", '
            '"justificativa": "...", "pontos_fortes": ["...", "..."], "pontos_atencao": ["...", "..."]}'
        )

        try:
            client = get_groq_client()
            chat = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Especialista juridico brasileiro. Responda APENAS com JSON valido, sem texto fora do JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=1500,
            )
            import json
            raw = chat.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            ia_data = json.loads(raw.strip())
            prob = float(ia_data.get("probabilidade_exito", prob_base))
            nivel = ia_data.get("nivel_risco", "medio")
            pontos_fortes = ia_data.get("pontos_fortes", [])
            pontos_atencao = ia_data.get("pontos_atencao", [])
            justificativa_completa = (
                ia_data.get("justificativa", "")
                + "\n\nPONTOS FORTES:\n" + "\n".join("- " + p for p in pontos_fortes)
                + "\n\nPONTOS DE ATENCAO:\n" + "\n".join("- " + p for p in pontos_atencao)
            )
        except Exception as e:
            prob = prob_base
            nivel = "medio"
            justificativa_completa = (
                "Analise baseada em historico: " + str(total) + " decisoes similares, "
                + str(procedentes) + " procedentes. Erro IA: " + str(e)
            )

        analise, _ = AnaliseRisco.objects.update_or_create(
            processo=processo,
            defaults={
                "probabilidade_exito": prob,
                "nivel_risco": nivel,
                "justificativa": justificativa_completa,
            },
        )
        serializer = AnaliseRiscoSerializer(analise)
        return Response(serializer.data)


class SugestaoJurisprudenciaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SugestaoJurisprudencia.objects.all()
    serializer_class = SugestaoJurisprudenciaSerializer

    @action(detail=False, methods=["post"], url_path="sugerir")
    def sugerir(self, request):
        processo_id = request.data.get("processo_id")
        if not processo_id:
            return Response({"erro": "processo_id obrigatorio"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            processo = Processo.objects.select_related("tipo_processo", "cliente").get(pk=processo_id)
        except Processo.DoesNotExist:
            return Response({"erro": "Processo nao encontrado"}, status=status.HTTP_404_NOT_FOUND)

        from jurisprudencia.models import Documento
        docs = Documento.objects.filter(tipo_processo=processo.tipo_processo)[:10]

        if docs.exists():
            sugestoes = []
            for doc in docs:
                obj, _ = SugestaoJurisprudencia.objects.update_or_create(
                    processo=processo,
                    documento_sugerido_id=doc.pk,
                    defaults={
                        "titulo_documento": doc.titulo,
                        "score_relevancia": 0.8,
                        "motivo": "Mesmo tipo de processo: " + str(processo.tipo_processo.nome),
                    },
                )
                sugestoes.append(obj)
            serializer = SugestaoJurisprudenciaSerializer(sugestoes, many=True)
            return Response(serializer.data)

        prompt = (
            "Como especialista juridico brasileiro, sugira 5 jurisprudencias, "
            "sumulas ou decisoes relevantes para o seguinte caso:\n\n"
            "Tipo de processo: " + str(processo.tipo_processo.nome) + "\n"
            "Polo do cliente: " + str(processo.get_polo_display()) + "\n"
            "Descricao: " + str(processo.descricao or "Sem descricao adicional") + "\n\n"
            "Responda APENAS com JSON array:\n"
            '[{"titulo": "...", "tribunal": "...", "resultado": "procedente|improcedente", '
            '"relevancia": 0.XX, "motivo": "..."}]'
        )
        try:
            client = get_groq_client()
            chat = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Especialista juridico brasileiro. Responda APENAS com JSON valido."},
                    {"role": "user", "content": prompt},
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.4,
                max_tokens=1200,
            )
            import json
            raw = chat.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            sugestoes_ia = json.loads(raw.strip())
            return Response({"fonte": "groq_ia", "processo": processo.numero, "sugestoes": sugestoes_ia})
        except Exception as e:
            return Response({"erro": "Erro na IA: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_juridico(request):
    """Endpoint de chat livre com assistente juridico Groq."""
    pergunta = (request.data.get("mensagem") or request.data.get("pergunta") or "").strip()
    contexto = request.data.get("contexto", "")
    historico = request.data.get("historico", [])

    if not pergunta:
        return Response({"erro": "Campo pergunta e obrigatorio"}, status=status.HTTP_400_BAD_REQUEST)

    messages = [
        {
            "role": "system",
            "content": (
                "Voce e um assistente juridico especializado no direito brasileiro, "
                "trabalhando para o escritorio Santos Nobre Assessoria Juridica. "
                "Responda de forma clara, objetiva e profissional em portugues. "
                "Cite leis, artigos e jurisprudencias relevantes quando aplicavel. "
                "Sempre adicione ressalvas eticas quando necessario."
            ),
        }
    ]

    for msg in historico[-6:]:
        if msg.get("role") in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    if contexto:
        pergunta = "Contexto: " + contexto + "\n\nPergunta: " + pergunta

    messages.append({"role": "user", "content": pergunta})

    try:
        client = get_groq_client()
        chat = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.6,
            max_tokens=2000,
        )
        resposta = chat.choices[0].message.content
        tokens_usados = chat.usage.total_tokens if chat.usage else None
        return Response({
            "resposta": resposta,
            "modelo": "llama-3.3-70b-versatile",
            "tokens_usados": tokens_usados,
        })
    except Exception as e:
        return Response({"erro": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
