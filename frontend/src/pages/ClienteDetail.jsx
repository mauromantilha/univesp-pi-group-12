import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../api/axios";
import toast from "react-hot-toast";

const LEAD_ETAPAS = [
  { value: "novo", label: "Novo" },
  { value: "qualificacao", label: "Qualificação" },
  { value: "proposta", label: "Proposta" },
  { value: "contrato", label: "Contrato" },
  { value: "convertido", label: "Convertido" },
  { value: "perdido", label: "Perdido" },
];

const QUALIFICACAO_STATUS = [
  { value: "nao_iniciado", label: "Não iniciado" },
  { value: "em_analise", label: "Em análise" },
  { value: "qualificado", label: "Qualificado" },
  { value: "desqualificado", label: "Desqualificado" },
];

const CONFLITO_STATUS = [
  { value: "pendente", label: "Pendente" },
  { value: "aprovado", label: "Aprovado" },
  { value: "reprovado", label: "Reprovado" },
];

const AUTOMACAO_CANAIS = [
  { value: "email", label: "E-mail" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "sms", label: "SMS" },
];

const AUTOMACAO_TIPOS = [
  { value: "mensagem", label: "Mensagem" },
  { value: "followup", label: "Follow-up" },
  { value: "agendamento", label: "Agendamento" },
];

const TAREFA_PRIORIDADES = [
  { value: "baixa", label: "Baixa" },
  { value: "media", label: "Média" },
  { value: "alta", label: "Alta" },
];

const TAREFA_STATUS = [
  { value: "pendente", label: "Pendente" },
  { value: "em_andamento", label: "Em andamento" },
  { value: "concluida", label: "Concluída" },
  { value: "cancelada", label: "Cancelada" },
];

const CONTRATO_TIPOS = [
  { value: "contrato", label: "Contrato" },
  { value: "procuracao", label: "Procuração" },
];

const EMPTY_FORM = {
  nome: "",
  tipo: "pf",
  cpf_cnpj: "",
  email: "",
  telefone: "",
  endereco: "",
  demanda: "",
  processos_possiveis: [],
  observacoes: "",
};

const STATUS_BADGE = {
  em_andamento: "badge-blue",
  suspenso: "badge-yellow",
  finalizado: "badge-green",
  arquivado: "badge-gray",
};

const STATUS_LABEL = {
  em_andamento: "Em andamento",
  suspenso: "Suspenso",
  finalizado: "Finalizado",
  arquivado: "Arquivado",
};

function toList(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.results || [];
}

function fmtDate(v) {
  if (!v) return "-";
  try {
    return new Date(v).toLocaleString("pt-BR");
  } catch {
    return v;
  }
}

function toLocalInput(v) {
  if (!v) return "";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return "";
  const off = d.getTimezoneOffset();
  const local = new Date(d.getTime() - off * 60000);
  return local.toISOString().slice(0, 16);
}

export default function ClienteDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [cliente, setCliente] = useState(null);
  const [processos, setProcessos] = useState([]);
  const [tiposProcesso, setTiposProcesso] = useState([]);
  const [usuarios, setUsuarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [savingPipeline, setSavingPipeline] = useState(false);
  const [savingQualificacao, setSavingQualificacao] = useState(false);
  const [savingConflito, setSavingConflito] = useState(false);
  const [pipelineForm, setPipelineForm] = useState({
    lead_origem: "",
    lead_campanha: "",
    lead_etapa: "novo",
    lead_sla_resposta_em: "",
    lead_ultimo_contato_em: "",
    lead_responsavel: "",
  });
  const [qualificacaoForm, setQualificacaoForm] = useState({
    qualificacao_status: "nao_iniciado",
    qualificacao_score: 0,
    formulario_qualificacao: "",
  });
  const [conflitoForm, setConflitoForm] = useState({
    conflito_interesses_status: "pendente",
    conflito_interesses_observacoes: "",
  });
  const [automacoes, setAutomacoes] = useState([]);
  const [automacaoForm, setAutomacaoForm] = useState({
    canal: "email",
    tipo: "mensagem",
    status: "agendado",
    mensagem: "",
    agendado_em: "",
  });
  const [tarefas, setTarefas] = useState([]);
  const [tarefaForm, setTarefaForm] = useState({
    titulo: "",
    descricao: "",
    status: "pendente",
    prioridade: "media",
    prazo_em: "",
    responsavel: "",
  });
  const [contratos, setContratos] = useState([]);
  const [contratoForm, setContratoForm] = useState({
    tipo_documento: "contrato",
    titulo: "",
    assinatura_provedor: "interno",
    assinatura_link: "",
    arquivo: null,
  });

  async function carregarCliente() {
    const res = await api.get(`/clientes/${id}/`);
    setCliente(res.data);
    setForm({
      nome: res.data.nome || "",
      tipo: res.data.tipo || "pf",
      cpf_cnpj: res.data.cpf_cnpj || "",
      email: res.data.email || "",
      telefone: res.data.telefone || "",
      endereco: res.data.endereco || "",
      demanda: res.data.demanda || "",
      processos_possiveis: Array.isArray(res.data.processos_possiveis)
        ? res.data.processos_possiveis
        : [],
      observacoes: res.data.observacoes || "",
    });
    setPipelineForm({
      lead_origem: res.data.lead_origem || "",
      lead_campanha: res.data.lead_campanha || "",
      lead_etapa: res.data.lead_etapa || "novo",
      lead_sla_resposta_em: toLocalInput(res.data.lead_sla_resposta_em),
      lead_ultimo_contato_em: toLocalInput(res.data.lead_ultimo_contato_em),
      lead_responsavel: res.data.lead_responsavel || "",
    });
    setQualificacaoForm({
      qualificacao_status: res.data.qualificacao_status || "nao_iniciado",
      qualificacao_score: Number(res.data.qualificacao_score || 0),
      formulario_qualificacao: res.data.formulario_qualificacao
        ? JSON.stringify(res.data.formulario_qualificacao, null, 2)
        : "",
    });
    setConflitoForm({
      conflito_interesses_status: res.data.conflito_interesses_status || "pendente",
      conflito_interesses_observacoes: res.data.conflito_interesses_observacoes || "",
    });
  }

  async function carregarProcessos() {
    const res = await api.get(`/processos/?cliente=${id}&limit=300`);
    setProcessos(toList(res.data));
  }

  async function carregarUsuarios() {
    const res = await api.get("/usuarios/?limit=200");
    setUsuarios(toList(res.data));
  }

  async function carregarAutomacoes() {
    const res = await api.get(`/clientes/${id}/automacoes/`);
    setAutomacoes(toList(res.data));
  }

  async function carregarTarefas() {
    const res = await api.get(`/clientes/${id}/tarefas/`);
    setTarefas(toList(res.data));
  }

  async function carregarContratos() {
    const res = await api.get(`/clientes/${id}/contratos/`);
    setContratos(toList(res.data));
  }

  useEffect(() => {
    setLoading(true);
    Promise.all([
      carregarCliente(),
      carregarProcessos(),
      api.get("/tipos-processo/?limit=300").then((r) => setTiposProcesso(toList(r.data))).catch(() => setTiposProcesso([])),
      carregarUsuarios().catch(() => setUsuarios([])),
      carregarAutomacoes().catch(() => setAutomacoes([])),
      carregarTarefas().catch(() => setTarefas([])),
      carregarContratos().catch(() => setContratos([])),
    ])
      .catch(() => toast.error("Erro ao carregar cliente"))
      .finally(() => setLoading(false));
  }, [id]);

  const tipoLabel = useMemo(() => {
    if (!cliente) return "-";
    return cliente.tipo_display || (cliente.tipo === "pj" ? "Pessoa Jurídica" : "Pessoa Física");
  }, [cliente]);

  function setField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSalvar(e) {
    e.preventDefault();
    if (!cliente) return;

    setSaving(true);
    try {
      const res = await api.patch(`/clientes/${cliente.id}/`, form);
      setCliente(res.data);
      setShowEditModal(false);
      toast.success("Cliente atualizado");
    } catch (err) {
      const data = err.response?.data;
      toast.error(data ? JSON.stringify(data).slice(0, 180) : "Erro ao atualizar cliente");
    } finally {
      setSaving(false);
    }
  }

  async function handleExcluir() {
    if (!cliente) return;
    if (!confirm(`Excluir o cliente \"${cliente.nome}\"?`)) return;

    try {
      await api.delete(`/clientes/${cliente.id}/`);
      toast.success("Cliente excluído");
      navigate("/clientes");
    } catch {
      toast.error("Não foi possível excluir este cliente");
    }
  }

  async function handleInativar() {
    if (!cliente) return;
    if (!cliente.ativo) {
      toast("Cliente já está inativo");
      return;
    }
    if (!confirm(`Inativar o cliente \"${cliente.nome}\"?`)) return;

    try {
      const res = await api.post(`/clientes/${cliente.id}/inativar/`);
      setCliente(res.data);
      toast.success("Cliente inativado");
    } catch {
      toast.error("Erro ao inativar cliente");
    }
  }

  async function handleSalvarPipeline(e) {
    e.preventDefault();
    setSavingPipeline(true);
    try {
      await api.patch(`/clientes/${id}/pipeline/`, {
        ...pipelineForm,
        lead_responsavel: pipelineForm.lead_responsavel || null,
        lead_sla_resposta_em: pipelineForm.lead_sla_resposta_em || null,
        lead_ultimo_contato_em: pipelineForm.lead_ultimo_contato_em || null,
      });
      await carregarCliente();
      toast.success("Pipeline atualizado");
    } catch (err) {
      const data = err.response?.data;
      toast.error(data ? JSON.stringify(data).slice(0, 160) : "Erro ao salvar pipeline");
    } finally {
      setSavingPipeline(false);
    }
  }

  async function handleSalvarQualificacao(e) {
    e.preventDefault();
    setSavingQualificacao(true);
    try {
      let formulario = null;
      if (qualificacaoForm.formulario_qualificacao.trim()) {
        formulario = JSON.parse(qualificacaoForm.formulario_qualificacao);
      }
      await api.patch(`/clientes/${id}/qualificacao/`, {
        qualificacao_status: qualificacaoForm.qualificacao_status,
        qualificacao_score: Number(qualificacaoForm.qualificacao_score || 0),
        formulario_qualificacao: formulario,
      });
      await carregarCliente();
      toast.success("Qualificação atualizada");
    } catch (err) {
      if (err instanceof SyntaxError) {
        toast.error("JSON do formulário de qualificação inválido");
      } else {
        const data = err.response?.data;
        toast.error(data ? JSON.stringify(data).slice(0, 160) : "Erro ao salvar qualificação");
      }
    } finally {
      setSavingQualificacao(false);
    }
  }

  async function handleSalvarConflito(e) {
    e.preventDefault();
    setSavingConflito(true);
    try {
      await api.patch(`/clientes/${id}/conflito-interesses/`, conflitoForm);
      await carregarCliente();
      toast.success("Conflito de interesses atualizado");
    } catch (err) {
      const data = err.response?.data;
      toast.error(data ? JSON.stringify(data).slice(0, 160) : "Erro ao salvar conflito");
    } finally {
      setSavingConflito(false);
    }
  }

  async function handleCriarAutomacao(e) {
    e.preventDefault();
    try {
      await api.post(`/clientes/${id}/automacoes/`, {
        ...automacaoForm,
        agendado_em: automacaoForm.agendado_em || null,
      });
      setAutomacaoForm({
        canal: "email",
        tipo: "mensagem",
        status: "agendado",
        mensagem: "",
        agendado_em: "",
      });
      await carregarAutomacoes();
      toast.success("Automação registrada");
    } catch (err) {
      const data = err.response?.data;
      toast.error(data ? JSON.stringify(data).slice(0, 160) : "Erro ao criar automação");
    }
  }

  async function handleCriarTarefa(e) {
    e.preventDefault();
    try {
      await api.post(`/clientes/${id}/tarefas/`, {
        ...tarefaForm,
        responsavel: tarefaForm.responsavel || null,
        prazo_em: tarefaForm.prazo_em || null,
      });
      setTarefaForm({
        titulo: "",
        descricao: "",
        status: "pendente",
        prioridade: "media",
        prazo_em: "",
        responsavel: "",
      });
      await carregarTarefas();
      toast.success("Tarefa criada");
    } catch (err) {
      const data = err.response?.data;
      toast.error(data ? JSON.stringify(data).slice(0, 160) : "Erro ao criar tarefa");
    }
  }

  async function handleConcluirTarefa(tarefaId) {
    try {
      await api.post(`/clientes/${id}/tarefas/${tarefaId}/concluir/`);
      await carregarTarefas();
      toast.success("Tarefa concluída");
    } catch {
      toast.error("Erro ao concluir tarefa");
    }
  }

  async function handleCriarContrato(e) {
    e.preventDefault();
    if (!contratoForm.titulo.trim()) {
      toast.error("Informe o título do documento");
      return;
    }

    const formData = new FormData();
    formData.append("tipo_documento", contratoForm.tipo_documento);
    formData.append("titulo", contratoForm.titulo);
    formData.append("assinatura_provedor", contratoForm.assinatura_provedor || "interno");
    if (contratoForm.assinatura_link) formData.append("assinatura_link", contratoForm.assinatura_link);
    if (contratoForm.arquivo) formData.append("arquivo", contratoForm.arquivo);

    try {
      await api.post(`/clientes/${id}/contratos/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setContratoForm({
        tipo_documento: "contrato",
        titulo: "",
        assinatura_provedor: "interno",
        assinatura_link: "",
        arquivo: null,
      });
      await carregarContratos();
      toast.success("Documento criado");
    } catch (err) {
      const data = err.response?.data;
      toast.error(data ? JSON.stringify(data).slice(0, 160) : "Erro ao criar documento");
    }
  }

  async function handleEnviarAssinatura(contratoId) {
    try {
      await api.post(`/clientes/${id}/contratos/${contratoId}/enviar-assinatura/`, {
        assinatura_provedor: "interno",
      });
      await carregarContratos();
      toast.success("Documento enviado para assinatura");
    } catch {
      toast.error("Erro ao enviar para assinatura");
    }
  }

  async function handleMarcarAssinado(contratoId) {
    try {
      await api.post(`/clientes/${id}/contratos/${contratoId}/marcar-assinado/`);
      await carregarContratos();
      toast.success("Documento marcado como assinado");
    } catch {
      toast.error("Erro ao marcar assinatura");
    }
  }

  if (loading) {
    return <div className="text-center py-20 text-gray-400">Carregando...</div>;
  }

  if (!cliente) {
    return <div className="text-center py-20 text-gray-400">Cliente não encontrado.</div>;
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <button onClick={() => navigate("/clientes")} className="hover:text-primary-600">Clientes</button>
          <span>/</span>
          <span className="text-gray-800 font-medium truncate">{cliente.nome}</span>
        </div>
        <button onClick={() => navigate("/clientes")} className="btn-secondary text-sm">
          ← Voltar
        </button>
      </div>

      <div className="card">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <h1 className="text-xl font-bold text-gray-900">{cliente.nome}</h1>
            <p className="text-sm text-gray-500 mt-1">{cliente.cpf_cnpj || "Sem CPF/CNPJ"}</p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className={cliente.ativo ? "badge-green" : "badge-gray"}>
              {cliente.ativo ? "Ativo" : "Inativo"}
            </span>
            <button onClick={() => setShowEditModal(true)} className="btn-secondary text-sm">Editar</button>
            <button onClick={handleExcluir} className="btn-secondary text-sm text-red-700">Excluir</button>
            <button onClick={handleInativar} className="btn-secondary text-sm text-amber-700">Inativar</button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5 pt-5 border-t border-gray-100">
          <InfoItem label="Tipo" value={tipoLabel} />
          <InfoItem label="Telefone" value={cliente.telefone || "-"} />
          <InfoItem label="Email" value={cliente.email || "-"} />
          <InfoItem label="Criado em" value={fmtDate(cliente.criado_em)} />
          <InfoItem label="Endereço" value={cliente.endereco || "-"} />
          <InfoItem label="Responsável" value={cliente.responsavel_nome || "-"} />
        </div>

        <div className="mt-4 pt-4 border-t border-gray-100 space-y-3">
          <div>
            <div className="text-xs text-gray-500 mb-1">Demanda</div>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{cliente.demanda || "-"}</p>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-1">Observações</div>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{cliente.observacoes || "-"}</p>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-1">Processos possíveis</div>
            <p className="text-sm text-gray-700">
              {Array.isArray(cliente.processos_possiveis_nomes) && cliente.processos_possiveis_nomes.length
                ? cliente.processos_possiveis_nomes.join(", ")
                : "-"}
            </p>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold">Processos do cliente</h2>
          <Link to="/processos" className="text-primary-600 hover:text-primary-800 text-sm font-medium">Ir para processos</Link>
        </div>
        {processos.length === 0 ? (
          <p className="text-sm text-gray-400">Nenhum processo vinculado.</p>
        ) : (
          <div className="space-y-2">
            {processos.map((processo) => (
              <div key={processo.id} className="flex items-center justify-between gap-3 rounded-lg border border-gray-200 p-3">
                <div>
                  <Link to={`/processos/${processo.id}`} className="font-mono text-sm font-semibold text-primary-700 hover:text-primary-900">
                    {processo.numero}
                  </Link>
                  <div className="text-xs text-gray-500 mt-1">{processo.tipo_nome || "-"}</div>
                </div>
                <span className={STATUS_BADGE[processo.status] || "badge-gray"}>
                  {processo.status_display || STATUS_LABEL[processo.status] || processo.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-base font-semibold mb-4">Pipeline de Leads</h2>
          <form onSubmit={handleSalvarPipeline} className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="label">Origem</label>
                <input
                  className="input"
                  value={pipelineForm.lead_origem}
                  onChange={(e) => setPipelineForm((f) => ({ ...f, lead_origem: e.target.value }))}
                  placeholder="Instagram, indicação, site..."
                />
              </div>
              <div>
                <label className="label">Campanha</label>
                <input
                  className="input"
                  value={pipelineForm.lead_campanha}
                  onChange={(e) => setPipelineForm((f) => ({ ...f, lead_campanha: e.target.value }))}
                  placeholder="Campanha de captação"
                />
              </div>
              <div>
                <label className="label">Etapa</label>
                <select
                  className="input"
                  value={pipelineForm.lead_etapa}
                  onChange={(e) => setPipelineForm((f) => ({ ...f, lead_etapa: e.target.value }))}
                >
                  {LEAD_ETAPAS.map((op) => (
                    <option key={op.value} value={op.value}>{op.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Responsável</label>
                <select
                  className="input"
                  value={pipelineForm.lead_responsavel || ""}
                  onChange={(e) => setPipelineForm((f) => ({ ...f, lead_responsavel: e.target.value }))}
                >
                  <option value="">Selecione...</option>
                  {usuarios.map((u) => (
                    <option key={u.id} value={u.id}>{u.first_name || u.username}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">SLA de resposta</label>
                <input
                  type="datetime-local"
                  className="input"
                  value={pipelineForm.lead_sla_resposta_em}
                  onChange={(e) => setPipelineForm((f) => ({ ...f, lead_sla_resposta_em: e.target.value }))}
                />
              </div>
              <div>
                <label className="label">Último contato</label>
                <input
                  type="datetime-local"
                  className="input"
                  value={pipelineForm.lead_ultimo_contato_em}
                  onChange={(e) => setPipelineForm((f) => ({ ...f, lead_ultimo_contato_em: e.target.value }))}
                />
              </div>
            </div>
            <button className="btn-primary text-sm" disabled={savingPipeline}>
              {savingPipeline ? "Salvando..." : "Salvar Pipeline"}
            </button>
          </form>
        </div>

        <div className="card">
          <h2 className="text-base font-semibold mb-4">Qualificação e Conflito</h2>
          <form onSubmit={handleSalvarQualificacao} className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="label">Status de qualificação</label>
                <select
                  className="input"
                  value={qualificacaoForm.qualificacao_status}
                  onChange={(e) => setQualificacaoForm((f) => ({ ...f, qualificacao_status: e.target.value }))}
                >
                  {QUALIFICACAO_STATUS.map((op) => (
                    <option key={op.value} value={op.value}>{op.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Score (0-100)</label>
                <input
                  className="input"
                  type="number"
                  min={0}
                  max={100}
                  value={qualificacaoForm.qualificacao_score}
                  onChange={(e) => setQualificacaoForm((f) => ({ ...f, qualificacao_score: e.target.value }))}
                />
              </div>
            </div>
            <div>
              <label className="label">Formulário de qualificação (JSON)</label>
              <textarea
                className="input font-mono text-xs"
                rows={5}
                value={qualificacaoForm.formulario_qualificacao}
                onChange={(e) => setQualificacaoForm((f) => ({ ...f, formulario_qualificacao: e.target.value }))}
                placeholder='{"orcamento":"alto","urgencia":"media"}'
              />
            </div>
            <button className="btn-secondary text-sm" disabled={savingQualificacao}>
              {savingQualificacao ? "Salvando..." : "Salvar Qualificação"}
            </button>
          </form>

          <form onSubmit={handleSalvarConflito} className="space-y-3 mt-5 pt-5 border-t border-gray-100">
            <div>
              <label className="label">Conflito de interesses</label>
              <select
                className="input"
                value={conflitoForm.conflito_interesses_status}
                onChange={(e) => setConflitoForm((f) => ({ ...f, conflito_interesses_status: e.target.value }))}
              >
                {CONFLITO_STATUS.map((op) => (
                  <option key={op.value} value={op.value}>{op.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Observações</label>
              <textarea
                className="input"
                rows={3}
                value={conflitoForm.conflito_interesses_observacoes}
                onChange={(e) => setConflitoForm((f) => ({ ...f, conflito_interesses_observacoes: e.target.value }))}
              />
            </div>
            <button className="btn-secondary text-sm" disabled={savingConflito}>
              {savingConflito ? "Salvando..." : "Salvar Conflito"}
            </button>
          </form>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-base font-semibold mb-4">Automações</h2>
          <form onSubmit={handleCriarAutomacao} className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="label">Canal</label>
                <select className="input" value={automacaoForm.canal} onChange={(e) => setAutomacaoForm((f) => ({ ...f, canal: e.target.value }))}>
                  {AUTOMACAO_CANAIS.map((op) => <option key={op.value} value={op.value}>{op.label}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Tipo</label>
                <select className="input" value={automacaoForm.tipo} onChange={(e) => setAutomacaoForm((f) => ({ ...f, tipo: e.target.value }))}>
                  {AUTOMACAO_TIPOS.map((op) => <option key={op.value} value={op.value}>{op.label}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="label">Mensagem</label>
              <textarea className="input" rows={3} value={automacaoForm.mensagem} onChange={(e) => setAutomacaoForm((f) => ({ ...f, mensagem: e.target.value }))} />
            </div>
            <div>
              <label className="label">Agendar para</label>
              <input type="datetime-local" className="input" value={automacaoForm.agendado_em} onChange={(e) => setAutomacaoForm((f) => ({ ...f, agendado_em: e.target.value }))} />
            </div>
            <button className="btn-primary text-sm">Registrar Automação</button>
          </form>

          <div className="space-y-2 mt-5 pt-5 border-t border-gray-100 max-h-72 overflow-y-auto">
            {automacoes.length === 0 ? (
              <p className="text-sm text-gray-400">Sem automações registradas.</p>
            ) : automacoes.map((a) => (
              <div key={a.id} className="rounded-lg border border-gray-200 p-2">
                <div className="text-sm font-medium">{a.canal_display} · {a.tipo_display}</div>
                <div className="text-xs text-gray-500">{a.status_display} · {fmtDate(a.agendado_em || a.criado_em)}</div>
                <div className="text-xs text-gray-700 mt-1 whitespace-pre-wrap">{a.mensagem || "-"}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h2 className="text-base font-semibold mb-4">Tarefas, Follow-up e Agendamento</h2>
          <form onSubmit={handleCriarTarefa} className="space-y-3">
            <div>
              <label className="label">Título</label>
              <input className="input" required value={tarefaForm.titulo} onChange={(e) => setTarefaForm((f) => ({ ...f, titulo: e.target.value }))} />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="label">Status</label>
                <select className="input" value={tarefaForm.status} onChange={(e) => setTarefaForm((f) => ({ ...f, status: e.target.value }))}>
                  {TAREFA_STATUS.map((op) => <option key={op.value} value={op.value}>{op.label}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Prioridade</label>
                <select className="input" value={tarefaForm.prioridade} onChange={(e) => setTarefaForm((f) => ({ ...f, prioridade: e.target.value }))}>
                  {TAREFA_PRIORIDADES.map((op) => <option key={op.value} value={op.value}>{op.label}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Responsável</label>
                <select className="input" value={tarefaForm.responsavel} onChange={(e) => setTarefaForm((f) => ({ ...f, responsavel: e.target.value }))}>
                  <option value="">Selecione...</option>
                  {usuarios.map((u) => <option key={u.id} value={u.id}>{u.first_name || u.username}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="label">Prazo</label>
              <input type="datetime-local" className="input" value={tarefaForm.prazo_em} onChange={(e) => setTarefaForm((f) => ({ ...f, prazo_em: e.target.value }))} />
            </div>
            <div>
              <label className="label">Descrição</label>
              <textarea className="input" rows={3} value={tarefaForm.descricao} onChange={(e) => setTarefaForm((f) => ({ ...f, descricao: e.target.value }))} />
            </div>
            <button className="btn-primary text-sm">Criar Tarefa</button>
          </form>

          <div className="space-y-2 mt-5 pt-5 border-t border-gray-100 max-h-72 overflow-y-auto">
            {tarefas.length === 0 ? (
              <p className="text-sm text-gray-400">Sem tarefas registradas.</p>
            ) : tarefas.map((t) => (
              <div key={t.id} className="rounded-lg border border-gray-200 p-2 flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-medium">{t.titulo}</div>
                  <div className="text-xs text-gray-500">{t.status_display} · {t.prioridade_display} · Prazo: {fmtDate(t.prazo_em)}</div>
                  <div className="text-xs text-gray-700 mt-1 whitespace-pre-wrap">{t.descricao || "-"}</div>
                </div>
                {t.status !== "concluida" && (
                  <button className="btn-secondary text-xs" onClick={() => handleConcluirTarefa(t.id)}>
                    Concluir
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-base font-semibold mb-4">Contrato e Procuração (e-signature)</h2>
        <form onSubmit={handleCriarContrato} className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
          <div className="md:col-span-1">
            <label className="label">Tipo</label>
            <select className="input" value={contratoForm.tipo_documento} onChange={(e) => setContratoForm((f) => ({ ...f, tipo_documento: e.target.value }))}>
              {CONTRATO_TIPOS.map((op) => <option key={op.value} value={op.value}>{op.label}</option>)}
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="label">Título</label>
            <input className="input" value={contratoForm.titulo} onChange={(e) => setContratoForm((f) => ({ ...f, titulo: e.target.value }))} required />
          </div>
          <div className="md:col-span-1">
            <label className="label">Provedor</label>
            <input className="input" value={contratoForm.assinatura_provedor} onChange={(e) => setContratoForm((f) => ({ ...f, assinatura_provedor: e.target.value }))} />
          </div>
          <div className="md:col-span-1">
            <label className="label">Arquivo</label>
            <input type="file" className="input" onChange={(e) => setContratoForm((f) => ({ ...f, arquivo: e.target.files?.[0] || null }))} />
          </div>
          <div className="md:col-span-4">
            <label className="label">Link de assinatura (opcional)</label>
            <input className="input" value={contratoForm.assinatura_link} onChange={(e) => setContratoForm((f) => ({ ...f, assinatura_link: e.target.value }))} placeholder="https://..." />
          </div>
          <div className="md:col-span-1">
            <button className="btn-primary w-full text-sm">Gerar Documento</button>
          </div>
        </form>

        <div className="space-y-2 mt-5 pt-5 border-t border-gray-100">
          {contratos.length === 0 ? (
            <p className="text-sm text-gray-400">Sem contratos/procurações.</p>
          ) : contratos.map((c) => (
            <div key={c.id} className="rounded-lg border border-gray-200 p-3 flex items-center justify-between gap-3 flex-wrap">
              <div>
                <div className="text-sm font-semibold">{c.titulo}</div>
                <div className="text-xs text-gray-500">
                  {c.tipo_documento_display} · {c.status_assinatura_display} · {fmtDate(c.assinado_em || c.criado_em)}
                </div>
                {c.assinatura_link && (
                  <a href={c.assinatura_link} target="_blank" rel="noreferrer" className="text-xs text-primary-600 hover:underline">
                    Abrir link de assinatura
                  </a>
                )}
              </div>
              <div className="flex gap-2">
                {c.status_assinatura === "pendente" && (
                  <button className="btn-secondary text-xs" onClick={() => handleEnviarAssinatura(c.id)}>
                    Enviar Assinatura
                  </button>
                )}
                {c.status_assinatura !== "assinado" && (
                  <button className="btn-secondary text-xs" onClick={() => handleMarcarAssinado(c.id)}>
                    Marcar Assinado
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {showEditModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-screen overflow-y-auto">
            <div className="p-6 border-b flex justify-between items-center">
              <h2 className="text-lg font-semibold">Editar Cliente</h2>
              <button onClick={() => setShowEditModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>

            <form onSubmit={handleSalvar} className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="label">Nome *</label>
                  <input className="input" required value={form.nome} onChange={(e) => setField("nome", e.target.value)} />
                </div>

                <div>
                  <label className="label">Tipo</label>
                  <select className="input" value={form.tipo} onChange={(e) => setField("tipo", e.target.value)}>
                    <option value="pf">Pessoa Física</option>
                    <option value="pj">Pessoa Jurídica</option>
                  </select>
                </div>

                <div>
                  <label className="label">CPF / CNPJ</label>
                  <input className="input" value={form.cpf_cnpj} onChange={(e) => setField("cpf_cnpj", e.target.value)} />
                </div>

                <div>
                  <label className="label">Telefone</label>
                  <input className="input" value={form.telefone} onChange={(e) => setField("telefone", e.target.value)} />
                </div>

                <div>
                  <label className="label">Email</label>
                  <input className="input" type="email" value={form.email} onChange={(e) => setField("email", e.target.value)} />
                </div>

                <div className="md:col-span-2">
                  <label className="label">Endereço</label>
                  <textarea className="input" rows={2} value={form.endereco} onChange={(e) => setField("endereco", e.target.value)} />
                </div>

                <div className="md:col-span-2">
                  <label className="label">Demanda</label>
                  <textarea className="input" rows={2} value={form.demanda} onChange={(e) => setField("demanda", e.target.value)} />
                </div>

                <div className="md:col-span-2">
                  <label className="label">Processos Possíveis</label>
                  <select
                    className="input min-h-[120px]"
                    multiple
                    value={form.processos_possiveis}
                    onChange={(e) => {
                      const ids = Array.from(e.target.selectedOptions).map((o) => Number(o.value));
                      setField("processos_possiveis", ids);
                    }}
                  >
                    {tiposProcesso.map((tipo) => (
                      <option key={tipo.id} value={tipo.id}>{tipo.nome}</option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Use Ctrl/Cmd para selecionar mais de um item.</p>
                </div>

                <div className="md:col-span-2">
                  <label className="label">Observações</label>
                  <textarea className="input" rows={3} value={form.observacoes} onChange={(e) => setField("observacoes", e.target.value)} />
                </div>
              </div>

              <div className="flex gap-3 justify-end pt-1">
                <button type="button" onClick={() => setShowEditModal(false)} className="btn-secondary">Cancelar</button>
                <button type="submit" className="btn-primary" disabled={saving}>
                  {saving ? "Salvando..." : "Salvar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function InfoItem({ label, value }) {
  return (
    <div>
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-sm font-medium text-gray-800 mt-0.5 whitespace-pre-wrap">{value}</div>
    </div>
  );
}
