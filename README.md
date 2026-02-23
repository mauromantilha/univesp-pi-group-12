# univesp-pi-group-12
# CRM Jurídico Inteligente - Grupo 12 (UNIVESP)

Este repositório contém o código-fonte do Projeto Integrador desenvolvido pelo Grupo 12 da UNIVESP. O objetivo do projeto é construir um sistema de CRM (Customer Relationship Management) customizado para a gestão de um escritório de advocacia de pequeno/médio porte (focado em uma operação de 5 advogados).

O grande diferencial do sistema é a futura integração com Inteligência Artificial preditiva para análise de viabilidade processual e sugestão de jurisprudência.

---

## 💻 Tecnologias Utilizadas

A arquitetura do projeto foi desenhada para ser modular e escalável, separando claramente as responsabilidades entre o cliente e o servidor:

* **Backend:** Python com Django e Django REST Framework (DRF) para a construção de uma API robusta e preparada para integrações de Data Science e IA.
* **Frontend:** [React / Vue.js] *(Nota do grupo: definir qual será adotado)* consumindo a API via requisições assíncronas (SPA).
* **Banco de Dados:** Relacional (PostgreSQL recomendado para lidar com buscas textuais em bases de jurisprudência).

---

## ⚙️ Estrutura de Módulos (Escopo)

O sistema está dividido em 5 módulos lógicos principais:

1.  **Administração e Perfis (Base):**
    * Controle de acesso (RBAC) para advogados, estagiários e administradores.
    * Dashboards individuais com resumo de tarefas do dia.
2.  **Gestão de Processos (Core):**
    * Cadastro centralizado de clientes e qualificação.
    * Ficha completa do processo (Número, Vara, Comarca, Tipo de Ação, Status).
    * Distribuição de carga de trabalho entre a equipe.
3.  **Agenda e Controle de Prazos:**
    * Calendário central de audiências e reuniões.
    * Sistema de alertas atrelado aos processos para evitar perda de prazos.
4.  **Base de Conhecimento e Jurisprudência:**
    * Repositório interno para salvar sentenças, acórdãos e peças-chave.
    * Busca textual avançada.
5.  **Módulo de Inteligência Artificial Preditiva:**
    * **Análise de Risco:** Estimativa de êxito baseada em histórico de varas e juízes.
    * **Sugestão de Jurisprudência:** Recomendação automática de peças baseada no contexto do novo processo.
    * **Extração de Dados (NLP):** Leitura de PDFs de decisões para preenchimento automático do banco de dados.

---

## 🗺️ Roadmap de Desenvolvimento (Fases do Projeto Integrador)

Para garantir entregas consistentes e gerenciar o escopo de forma eficiente ao longo do semestre, o desenvolvimento seguirá as seguintes fases:

* **Fase 1 (MVP - Módulos 1, 2 e 3):** Construção da API base, autenticação, CRUD de processos e sistema básico de agenda.
* **Fase 2 (Base de Conhecimento - Módulo 4):** Estruturação do repositório de documentos e indexação de buscas.
* **Fase 3 (IA - Módulo 5):** Integração de bibliotecas de NLP e modelos preditivos rodando em segundo plano.

---

## 🚀 Como rodar o projeto localmente (Backend)

*(Instruções preliminares - serão atualizadas conforme a configuração do ambiente)*

1. Clone este repositório:
   ```bash
   git clone [https://github.com/mauromantilha/univesp-pi-group-12.git](https://github.com/mauromantilha/univesp-pi-group-12.git)
