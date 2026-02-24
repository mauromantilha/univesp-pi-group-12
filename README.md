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

## Como executar (local)

```bash
# Instalar dependências
pip install -r requirements.txt

# Aplicar migrações
python manage.py migrate

# Criar dados de demonstração
python manage.py seed_demo

# Iniciar servidor (localhost)
python manage.py runserver
```

Acesse `http://localhost:8000` e entre com:
- **Admin**: `admin` / `admin123`
- **Advogado**: `adv1` / `senha123`

## Deploy em servidor remoto (EC2 / VPS)

### 1. Iniciar o servidor acessível externamente

```bash
# Bind em todas as interfaces (necessário para acesso externo)
python manage.py runserver 0.0.0.0:8000
```

### 2. IP mudou? Siga estes passos

```bash
# 1. No servidor, descubra o novo IP público
curl -s ifconfig.me

# 2. Reinicie o servidor com o novo IP
python manage.py runserver 0.0.0.0:8000

# 3. Acesse via nip.io substituindo SEU_IP pelo IP atual
# http://SEU_IP.nip.io:8000/login
```

### 3. Definir CSRF_TRUSTED_ORIGINS (importante para nip.io)

Quando acessado por URL pública (nip.io ou domínio), defina a variável de ambiente **antes** de iniciar o servidor:

```bash
export CSRF_TRUSTED_ORIGINS=http://SEU_IP.nip.io:8000
python manage.py runserver 0.0.0.0:8000
```

Ou em linha única:

```bash
CSRF_TRUSTED_ORIGINS=http://15.228.99.99.nip.io:8000 python manage.py runserver 0.0.0.0:8000
```

### 5. Esqueceu a senha / senha não aceita?

Execute no servidor para redefinir a senha do admin:

```bash
python manage.py shell -c "
from accounts.models import Usuario
u = Usuario.objects.get(username='admin')
u.set_password('admin123')
u.save()
print('Senha redefinida com sucesso!')
"
```

Ou use o comando nativo do Django para qualquer usuário:

```bash
python manage.py changepassword admin
```

O `seed_demo` também redefine as senhas se executado novamente:

```bash
python manage.py seed_demo
# admin -> admin123 | adv1..adv5 -> senha123
```


### 6. Manter o servidor rodando em segundo plano (nohup)

```bash
export CSRF_TRUSTED_ORIGINS=http://SEU_IP.nip.io:8000
nohup python manage.py runserver 0.0.0.0:8000 > crm.log 2>&1 &
echo "Servidor iniciado. PID: $!"
```

Para parar:

```bash
pkill -f "manage.py runserver"
```

## Tecnologias
- Python 3 / Django 6
- Bootstrap 5 (local)
- SQLite (desenvolvimento)
- Whitenoise (arquivos estáticos)
