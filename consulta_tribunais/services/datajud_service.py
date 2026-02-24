"""
Serviço de integração com a API DataJud do CNJ
"""
import requests
import json
from django.core.cache import cache
from django.utils import timezone


class DataJudService:
    """Serviço para consultar processos no DataJud"""
    
    def __init__(self, tribunal):
        self.tribunal = tribunal
        self.endpoint = tribunal.api_endpoint
        self.api_key = tribunal.api_key
    
    def consultar_processo(self, numero_processo):
        """Consulta um processo específico no DataJud"""
        # Verifica cache primeiro (válido por 24h)
        cache_key = f'datajud_{self.tribunal.sigla}_{numero_processo}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            query = {
                "query": {
                    "match": {
                        "numeroProcesso": numero_processo
                    }
                }
            }
            
            headers = {
                'Authorization': f'APIKey {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=query,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('hits', {}).get('hits'):
                processo_data = data['hits']['hits'][0]['_source']
                cache.set(cache_key, processo_data, 86400)  # 24h
                return processo_data
            
            return None
            
        except requests.RequestException as e:
            raise Exception(f"Erro ao consultar DataJud: {str(e)}")
    
    def buscar_processos_avancado(self, filtros, max_results=20):
        """
        Busca avançada de processos.
        
        ATENÇÃO: A API Pública DataJud NÃO possui dados de partes/advogados.
        Campos disponíveis: numeroProcesso, classe, orgaoJulgador, dataAjuizamento, assuntos
        
        Args:
            filtros (dict): Filtros de busca
                - classe: Nome da classe processual (ex: "Reclamação Trabalhista")
                - orgao_julgador: Nome do órgão (ex: "1ª Vara do Trabalho")
                - data_inicio: Data inicial (formato: YYYYMMDD)
                - data_fim: Data final (formato: YYYYMMDD)
                - assunto: Assunto (ex: "Horas Extras")
            max_results (int): Número máximo de resultados
        
        Returns:
            list: Lista de processos encontrados
        """
        try:
            # Construir query Elasticsearch
            must_clauses = []
            
            if filtros.get('classe'):
                must_clauses.append({
                    "match": {"classe.nome": filtros['classe']}
                })
            
            if filtros.get('orgao_julgador'):
                must_clauses.append({
                    "match": {"orgaoJulgador.nome": filtros['orgao_julgador']}
                })
            
            if filtros.get('assunto'):
                must_clauses.append({
                    "match": {"assuntos.nome": filtros['assunto']}
                })
            
            if filtros.get('data_inicio') or filtros.get('data_fim'):
                range_filter = {}
                if filtros.get('data_inicio'):
                    range_filter['gte'] = filtros['data_inicio']
                if filtros.get('data_fim'):
                    range_filter['lte'] = filtros['data_fim']
                
                must_clauses.append({
                    "range": {"dataAjuizamento": range_filter}
                })
            
            # Se não há filtros, busca os mais recentes
            if not must_clauses:
                query = {"query": {"match_all": {}}}
            else:
                query = {
                    "query": {
                        "bool": {
                            "must": must_clauses
                        }
                    }
                }
            
            query["size"] = max_results
            query["sort"] = [{"dataAjuizamento": "desc"}]
            
            headers = {
                'Authorization': f'APIKey {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=query,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            processos = []
            for hit in data.get('hits', {}).get('hits', []):
                processos.append(hit['_source'])
            
            return processos
            
        except requests.RequestException as e:
            raise Exception(f"Erro ao buscar processos: {str(e)}")


def formatar_dados_processo(dados_raw):
    """Formata os dados brutos do processo"""
    if not dados_raw:
        return {}
    
    return {
        'numero_processo': dados_raw.get('numeroProcesso', ''),
        'classe': dados_raw.get('classe', {}).get('nome', ''),
        'assuntos': [a.get('nome', '') for a in dados_raw.get('assuntos', [])],
        'data_ajuizamento': dados_raw.get('dataAjuizamento', ''),
        'orgao_julgador': dados_raw.get('orgaoJulgador', {}).get('nome', ''),
        'tribunal': dados_raw.get('tribunal', ''),
        'grau': dados_raw.get('grau', ''),
        'movimentos': dados_raw.get('movimentos', []),
        'valor_causa': dados_raw.get('valorCausa', 0),
        'sistema': dados_raw.get('sistema', {}).get('nome', ''),
    }
