# CRM Jurídico - UNIVESP PI Grupo 12

Sistema web para gestão de escritório de advocacia, com frontend React (SPA) e backend Django REST, cobrindo operações jurídicas, agenda, consulta de tribunais, IA, financeiro e gestão de usuários.

## Sumário

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Módulos e Funcionalidades](#módulos-e-funcionalidades)
4. [Perfis e Regras de Acesso](#perfis-e-regras-de-acesso)
5. [Stack Tecnológica](#stack-tecnológica)
6. [Estrutura do Projeto](#estrutura-do-projeto)
7. [Requisitos](#requisitos)
8. [Configuração de Ambiente](#configuração-de-ambiente)
9. [Execução Local](#execução-local)
10. [Dados de Demonstração](#dados-de-demonstração)
11. [API REST](#api-rest)
12. [Build e Deploy](#build-e-deploy)
13. [Testes](#testes)
14. [Troubleshooting](#troubleshooting)
15. [Checklist de Produção](#checklist-de-produção)

## Visão Geral

O CRM Jurídico foi desenvolvido para centralizar o fluxo operacional de escritórios de advocacia em um único sistema:

- Gestão de clientes e processos com segregação por advogado.
- Gestão de documentos com upload múltiplo e pré-visualização em iframe.
- Agenda de compromissos e prazos.
- Consulta de processos em tribunais (DataJud) com análise assistida por IA.
- Módulo financeiro com lançamentos, categorias, contas bancárias e anexos.
- Gestão de usuários com auditoria/atividades.

## Arquitetura

### Backend

- Django + Django REST Framework.
- Autenticação JWT (`access` + `refresh`) via `rest_framework_simplejwt`.
- API principal em `/api/v1/`.
- Controle de permissões por papel (RBAC) e escopo por usuário.

### Frontend

- React + Vite + React Router.
- SPA protegida por autenticação JWT.
- Layout responsivo com sidebar colapsável/hamburger.
- Comunicação com backend via Axios (`/api/v1` por padrão).

### Banco de Dados

- Desenvolvimento: SQLite (padrão).
- Produção: PostgreSQL (RDS/Aurora), habilitado por variáveis de ambiente.

## Módulos e Funcionalidades

### 1) Dashboard

- Cards com dados reais:
  - Processos ativos
  - Total de clientes
  - Eventos do dia
  - Prazos próximos
- Lista de processos recentes.
- Lista de prazos urgentes.

### 2) Processos

- CRUD de processos.
- Tela de detalhe do processo com:
  - Informações completas
  - Movimentações
  - Análise de risco (IA)
- Ações disponíveis no detalhe:
  - Editar
  - Excluir
  - Inativar (status `suspenso`)
  - Concluir (status `finalizado`)
  - Arquivar processo (status `arquivado`)
- Link para abrir detalhe a partir da listagem.

### 3) Clientes

- CRUD de clientes.
- Campo de demanda e processos possíveis.
- Tela de detalhe com processos vinculados.
- Ações disponíveis:
  - Editar
  - Excluir
  - Inativar cliente (`ativo=false`)
- Link para abrir detalhe a partir da listagem.

### 4) Documentos (área centralizada)

- Aba `Documentos Clientes`:
  - Busca cliente
  - Upload múltiplo
  - Vinculação automática ao cliente
  - Visualização por iframe
- Aba `Documentos Processos`:
  - Busca processo
  - Exibição do cliente vinculado
  - Upload múltiplo
  - Visualização por iframe

### 5) Agenda

- CRUD de compromissos/eventos.
- Endpoint de prazos próximos (`/eventos/prazos-proximos/`).
- Filtros por mês e próximos 7 dias.

### 6) Consulta Tribunais

- Consulta de processos por tribunal (DataJud).
- Busca avançada por filtros.
- Perguntas sobre o processo consultado com suporte IA (quando configurado).

### 7) IA Preditiva

- Chat jurídico (`/ia/chat/`).
- Sugestões de jurisprudência (`/ia/sugestoes/sugerir/`).
- Análise de risco por processo (`/ia/analises/analisar/`).

### 8) Financeiro

- Lançamentos (a pagar/receber/honorários etc.).
- Categorias financeiras.
- Contas bancárias e extrato.
- Dashboard financeiro consolidado.
- Upload múltiplo de arquivos em lançamentos.

### 9) Gestão de Usuários

- Área administrativa (`Gestão Usuários`).
- Usuários ativos, gerenciamento de usuários, atividades e auditoria.
- Logs de atividade por usuário.

## Perfis e Regras de Acesso

Perfis do sistema (`accounts.Usuario.papel`):

- `administrador`
- `advogado`
- `estagiario`

### Regras principais

- Administrador vê e gerencia tudo.
- Advogado vê apenas seus próprios dados e dados vinculados.
- Processos são segregados por advogado responsável.
- Clientes para advogados são filtrados por relação (responsável ou processo vinculado).
- Gestão de usuários é restrita ao administrador.

## Stack Tecnológica

### Backend

- Python 3.9+
- Django 4.2.x
- Django REST Framework
- Simple JWT
- CORS Headers
- WhiteNoise
- Pillow
- python-dotenv
- Groq SDK

### Frontend

- React 19
- React Router
- Axios
- Vite
- Tailwind CSS
- react-hot-toast
- date-fns

## Estrutura do Projeto

```text
crm_juridico/
├── accounts/              # autenticação, usuários, permissões, auditoria
├── processos/             # clientes, processos, movimentações, uploads
├── agenda/                # compromissos e prazos
├── consulta_tribunais/    # integração DataJud + IA contextual
├── ia_preditiva/          # chat/sugestões/análise de risco
├── jurisprudencia/        # base de documentos jurídicos
├── financeiro/            # lançamentos, contas, categorias, uploads
├── crm_advocacia/         # settings e urls do Django
├── frontend/              # aplicação React SPA
├── api_urls.py            # roteamento principal da API REST
├── manage.py
└── README.md
```

## Requisitos

- Python 3.9+
- Node.js 18+
- npm 9+
- (Opcional produção) PostgreSQL 14+

## Configuração de Ambiente

Crie `.env` na raiz com base em `.env.example`.

### Variáveis principais (backend)

- `SECRET_KEY` (obrigatória em produção)
- `DEBUG` (`True`/`False`)
- `ALLOWED_HOSTS` (lista separada por vírgula)
- `CSRF_TRUSTED_ORIGINS` (lista separada por vírgula)
- `GROQ_API_KEY` (para funcionalidades de IA)

### Banco de dados

#### Opção 1: SQLite (padrão)

Sem configuração extra.

#### Opção 2: PostgreSQL

Escolha uma das abordagens:

1. `DATABASE_URL` completo.
2. Variáveis separadas:
   - `USE_POSTGRES=1`
   - `DB_ENGINE=django.db.backends.postgresql`
   - `DB_NAME`
   - `DB_USER`
   - `DB_PASSWORD`
   - `DB_HOST`
   - `DB_PORT` (padrão `5432`)
   - `DB_SSLMODE` (ex.: `require`)
   - `DB_SSLROOTCERT` (quando necessário)

### Variável opcional do frontend

- `VITE_API_URL` (padrão: `/api/v1`)

Exemplo para desenvolvimento desacoplado:

```bash
VITE_API_URL=http://127.0.0.1:8000/api/v1
```

## Execução Local

## 1) Backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Acesse:

- Frontend: `http://localhost:5173`
- API Django: `http://127.0.0.1:8000/api/v1/`

## Dados de Demonstração

Para popular o sistema com dados iniciais:

```bash
python manage.py seed_demo
```

Credenciais geradas:

- Admin: `admin` / `admin123`
- Advogado: `adv1` / `senha123`

## API REST

Base URL: `/api/v1`

### Autenticação

- `POST /auth/login/`
- `POST /auth/refresh/`

### Usuários

- `GET /usuarios/me/`
- `GET /usuarios/dashboard/`
- `GET /usuarios/atividades/`
- `GET /usuarios/auditoria/`

### Processos

- `GET/POST /processos/`
- `GET/PATCH/DELETE /processos/{id}/`
- `POST /processos/{id}/inativar/`
- `POST /processos/{id}/concluir/`
- `POST /processos/{id}/arquivar/`
- `GET /processos/{id}/movimentacoes/`
- `GET/POST /processos/{id}/arquivos/`

### Clientes

- `GET/POST /clientes/`
- `GET/PATCH/DELETE /clientes/{id}/`
- `POST /clientes/{id}/inativar/`
- `GET/POST /clientes/{id}/arquivos/`

### Agenda

- `GET/POST /eventos/`
- `GET /eventos/prazos-proximos/`
- `GET /eventos/proximos/`
- `GET /eventos/mes/`

### IA

- `POST /ia/chat/`
- `POST /ia/sugestoes/sugerir/`
- `POST /ia/analises/analisar/`

### Consulta Tribunais

- `GET /tribunais/`
- `POST /consultas-processos/consultar/`
- `POST /consultas-processos/buscar_avancado/`
- `POST /consultas-processos/{id}/fazer_pergunta/`
- `POST /consultas-processos/{id}/reanalisar/`

### Financeiro

- `GET/POST /financeiro/lancamentos/`
- `GET /financeiro/lancamentos/dashboard/`
- `POST /financeiro/lancamentos/{id}/baixar/`
- `GET/POST /financeiro/lancamentos/{id}/arquivos/`
- `GET/POST /financeiro/categorias/`
- `GET/POST /financeiro/contas/`
- `GET /financeiro/contas/{id}/extrato/`

## Build e Deploy

### Build do frontend

```bash
cd frontend
npm run build
```

Saída em: `frontend/dist/`

### Exemplo de publicação (Nginx estático)

```bash
sudo rsync -a --delete frontend/dist/ /var/www/crm-frontend/
```

### Migrações em produção

```bash
source venv/bin/activate
python manage.py migrate
```

### Reinício do backend (exemplo systemd)

```bash
sudo systemctl restart crm_juridico.service
sudo systemctl status crm_juridico.service
```

## Testes

Executar suíte completa:

```bash
python manage.py test
```

Executar somente testes de API de processos:

```bash
python manage.py test processos.tests_api
```

## Troubleshooting

### 1) Tela branca no frontend

- Verifique se o build foi atualizado em `frontend/dist`.
- Republique em `/var/www/crm-frontend`.
- Faça hard refresh no navegador (`Ctrl+F5`).

### 2) Erro de login

- Valide endpoint `/api/v1/auth/login/`.
- Confira credenciais do usuário.
- Se necessário, rode `seed_demo` para reset dos usuários demo.

### 3) IA não responde

- Configure `GROQ_API_KEY`.
- Sem chave, alguns endpoints retornam fallback controlado.

### 4) Falha de conexão com PostgreSQL/RDS

- Validar DNS/rede da instância.
- Conferir `DB_HOST`, `DB_PORT`, SSL e credenciais.
- Testar conexão manual antes de rodar migração.

### 5) CORS/CSRF em domínio público

- Ajustar `ALLOWED_HOSTS`.
- Ajustar `CSRF_TRUSTED_ORIGINS` com esquema correto (`http://` ou `https://`).

## Checklist de Produção

- `DEBUG=False`
- `SECRET_KEY` forte definida
- `ALLOWED_HOSTS` restrito
- `CSRF_TRUSTED_ORIGINS` configurado
- Banco PostgreSQL com backup e SSL
- Build frontend publicado
- Migrações aplicadas
- Serviço backend ativo e monitorado
- Logs e auditoria de usuários habilitados

---

Se quiser, eu também posso gerar uma versão curta desse README para a página inicial do repositório e deixar esta versão completa em `docs/README_COMPLETO.md`.
