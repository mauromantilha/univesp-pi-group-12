# CRM para Escritório de Advocacia – UNIVESP PI Grupo 12

Sistema de gerenciamento de escritório de advocacia desenvolvido com Django (Python).

## Módulos Implementados

### Módulo 1 – Administração e Perfis
- Gestão de usuários (advogados, estagiários, administradores)
- Controle de Acesso por papel (RBAC)
- Dashboard personalizado por papel

### Módulo 2 – Gestão de Processos (Core)
- Cadastro de clientes (PF/PJ)
- Ficha do processo com número, cliente, advogado, vara, status
- Timeline de movimentações
- Comarcas, Varas e Tipos de Processo
- Visão de carga de trabalho dos advogados

### Módulo 3 – Agenda e Prazos
- Calendário de compromissos (audiências, reuniões, prazos fatais)
- Alertas de prazos próximos (7 dias)
- Vinculação automática ao processo

### Módulo 4 – Inteligência e Jurisprudência
- Repositório de sentenças, acórdãos e teses
- Busca textual em conteúdo, título e tags
- Filtro por categoria e tribunal

### Módulo 5 – IA Preditiva
- Análise de risco por tipo/vara com base no histórico
- Sugestão automática de jurisprudência por processo
- Busca inteligente no repositório

## Como executar

```bash
# Instalar dependências
pip install -r requirements.txt

# Aplicar migrações
python manage.py migrate

# Criar dados de demonstração
python manage.py seed_demo

# Iniciar servidor
python manage.py runserver
```

Acesse `http://localhost:8000` e entre com:
- **Admin**: `admin` / `admin123`
- **Advogado**: `adv1` / `senha123`

## Tecnologias
- Python 3 / Django 6
- Bootstrap 5 (local)
- SQLite (desenvolvimento)
- Whitenoise (arquivos estáticos)
