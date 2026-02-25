# CRM Jurídico - UNIVESP PI Grupo 12

Plataforma de gestão para escritórios de advocacia com frontend React (SPA) e backend Django REST, incluindo processos, clientes, agenda, documentos, consulta tribunais, IA, financeiro e gestão de usuários.

## Documentação

- Documentação completa: [docs/README_COMPLETO.md](docs/README_COMPLETO.md)

## Principais funcionalidades

- Dashboard com indicadores reais (processos, clientes, eventos e prazos).
- Gestão de clientes e processos com segregação por advogado.
- Área centralizada de documentos com upload múltiplo e visualização em iframe.
- Agenda e prazos jurídicos.
- Consulta de tribunais (DataJud) com suporte de IA.
- Financeiro com lançamentos, contas, categorias e anexos.
- Gestão de usuários com auditoria e logs de atividades.

## Stack

- Backend: Python, Django, Django REST Framework, JWT.
- Frontend: React, Vite, Axios, Tailwind.
- Banco: SQLite (dev) e PostgreSQL/RDS (produção).

## Execução rápida (desenvolvimento)

### 1) Backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 0.0.0.0:8000
```

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Acessos:

- Frontend: `http://localhost:5173`
- API: `http://127.0.0.1:8000/api/v1/`

Credenciais demo:

- Admin: `admin` / `admin123`
- Advogado: `adv1` / `senha123`

## Build de produção

```bash
cd frontend
npm run build
```

## API base

Todos os endpoints ficam sob:

```text
/api/v1/
```

## Licença

Projeto acadêmico UNIVESP (PI - Grupo 12).
