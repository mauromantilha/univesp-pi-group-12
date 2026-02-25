"""
Serviço de integração com Groq AI para análise de processos
"""
import os
import json
from groq import Groq


class GroqService:
    """Serviço para análise de processos usando Groq AI"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY não configurada")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"  # Modelo mais rápido e eficiente
    
    def analisar_processo(self, dados_processo):
        """
        Analisa um processo e gera um resumo inteligente
        
        Args:
            dados_processo: Dict com dados do processo
        
        Returns:
            str: Análise gerada pela IA
        """
        prompt = self._criar_prompt_analise(dados_processo)
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você é um assistente jurídico especializado em análise de processos trabalhistas. "
                            "Analise os dados fornecidos e gere um resumo claro, objetivo e profissional. "
                            "Destaque os pontos mais importantes: classe, assuntos, movimentações recentes, "
                            "status atual e riscos/oportunidades identificados."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=1500,
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Erro ao analisar processo com Groq: {str(e)}")
    
    def responder_pergunta(self, dados_processo, pergunta, historico_perguntas=None):
        """
        Responde uma pergunta específica sobre o processo
        
        Args:
            dados_processo: Dict com dados do processo
            pergunta: Pergunta do usuário
            historico_perguntas: Lista de perguntas/respostas anteriores
        
        Returns:
            str: Resposta da IA
        """
        mensagens = [
            {
                "role": "system",
                "content": (
                    "Você é um assistente jurídico especializado. Responda perguntas sobre processos "
                    "de forma clara, precisa e profissional. Base suas respostas apenas nos dados "
                    "fornecidos do processo. Se não houver informação suficiente, informe isso claramente."
                )
            }
        ]
        
        # Adiciona contexto do processo
        contexto = f"DADOS DO PROCESSO:\n{json.dumps(dados_processo, indent=2, ensure_ascii=False)}"
        mensagens.append({
            "role": "user",
            "content": contexto
        })
        
        # Adiciona histórico se existir
        if historico_perguntas:
            for item in historico_perguntas[-3:]:  # Últimas 3 perguntas
                mensagens.append({
                    "role": "user",
                    "content": item['pergunta']
                })
                mensagens.append({
                    "role": "assistant",
                    "content": item['resposta']
                })
        
        # Adiciona a pergunta atual
        mensagens.append({
            "role": "user",
            "content": pergunta
        })
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=mensagens,
                model=self.model,
                temperature=0.2,
                max_tokens=1000,
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Erro ao responder pergunta: {str(e)}")
    
    def _criar_prompt_analise(self, dados_processo):
        """Cria o prompt para análise do processo"""
        return f"""
Analise o seguinte processo trabalhista e forneça um resumo executivo:

DADOS DO PROCESSO:
{json.dumps(dados_processo, indent=2, ensure_ascii=False)}

Forneça uma análise estruturada com:
1. IDENTIFICAÇÃO: Número, classe e órgão julgador
2. ASSUNTOS: Principais temas discutidos
3. ANDAMENTO: Status atual e movimentações recentes
4. VALOR DA CAUSA: Se informado
5. ANÁLISE DE RISCO: Pontos de atenção e oportunidades
6. PRÓXIMOS PASSOS: Recomendações
"""
