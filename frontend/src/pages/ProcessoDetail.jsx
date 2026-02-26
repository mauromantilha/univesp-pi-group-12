import { useState, useEffect } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../api/axios";
import toast from "react-hot-toast";

const STATUS_BADGE = {
  em_andamento: "badge-blue",
  suspenso: "badge-yellow",
  finalizado: "badge-green",
  arquivado: "badge-gray",
};

const STATUS_LABELS = {
  em_andamento: "Em Andamento",
  suspenso: "Suspenso",
  finalizado: "Finalizado",
  arquivado: "Arquivado",
};

const TIPO_CASO_LABELS = {
  contencioso: "Contencioso",
  consultivo: "Consultivo",
  massificado: "Massificado",
};

const ETAPAS_WORKFLOW = {
  contencioso: [
    { value: "triagem", label: "Triagem" },
    { value: "estrategia", label: "Estratégia" },
    { value: "instrucao", label: "Instrução" },
    { value: "negociacao", label: "Negociação" },
    { value: "execucao", label: "Execução" },
    { value: "encerramento", label: "Encerramento" },
  ],
  consultivo: [
    { value: "triagem", label: "Triagem" },
    { value: "estrategia", label: "Estratégia" },
    { value: "negociacao", label: "Negociação" },
    { value: "execucao", label: "Execução" },
    { value: "encerramento", label: "Encerramento" },
  ],
  massificado: [
    { value: "triagem", label: "Triagem" },
    { value: "instrucao", label: "Instrução" },
    { value: "monitoramento", label: "Monitoramento" },
    { value: "execucao", label: "Execução" },
    { value: "encerramento", label: "Encerramento" },
  ],
};

const PRIORIDADE_TAREFA = {
  baixa: "Baixa",
  media: "Média",
  alta: "Alta",
  urgente: "Urgente",
};

const PAPEL_RESPONSAVEL = {
  principal: "Principal",
  apoio: "Apoio",
  estagiario: "Estagiário",
};

const EMPTY_EDIT_FORM = {
  numero: "",
  cliente: "",
  tipo: "",
  vara: "",
  status: "em_andamento",
  tipo_caso: "contencioso",
  valor_causa: "",
  objeto: "",
};

const EMPTY_PARTE_FORM = {
  tipo_parte: "autor",
  nome: "",
  documento: "",
  observacoes: "",
};

const EMPTY_RESP_FORM = {
  usuario: "",
  papel: "apoio",
};

const EMPTY_TAREFA_FORM = {
  titulo: "",
  descricao: "",
  prioridade: "media",
  prazo_em: "",
  responsavel: "",
};

const EMPTY_PRAZO_FORM = {
  titulo: "",
  data: "",
  hora: "",
  descricao: "",
  alerta_dias_antes: 1,
  alerta_horas_antes: 0,
};

const EMPTY_PECA_FORM = {
  titulo: "",
  tipo_peca: "peticao",
  status: "rascunho",
  conteudo: "",
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

function userLabel(user) {
  if (!user) return "-";
  const nome = `${user.first_name || ""} ${user.last_name || ""}`.trim();
  return nome || user.username || `Usuário #${user.id}`;
}

export default function ProcessoDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [processo, setProcesso] = useState(null);
  const [movs, setMovs] = useState([]);
  const [partes, setPartes] = useState([]);
  const [responsaveis, setResponsaveis] = useState([]);
  const [tarefas, setTarefas] = useState([]);
  const [prazos, setPrazos] = useState([]);
  const [pecas, setPecas] = useState([]);
  const [usuarios, setUsuarios] = useState([]);

  const [workflowForm, setWorkflowForm] = useState({ tipo_caso: "contencioso", etapa_workflow: "triagem" });
  const [parteForm, setParteForm] = useState(EMPTY_PARTE_FORM);
  const [responsavelForm, setResponsavelForm] = useState(EMPTY_RESP_FORM);
  const [tarefaForm, setTarefaForm] = useState(EMPTY_TAREFA_FORM);
  const [prazoForm, setPrazoForm] = useState(EMPTY_PRAZO_FORM);
  const [pecaForm, setPecaForm] = useState(EMPTY_PECA_FORM);
  const [selectedPecaId, setSelectedPecaId] = useState(null);
  const [revisaoPecaIA, setRevisaoPecaIA] = useState(null);
  const [loadingPecaIA, setLoadingPecaIA] = useState(false);

  const [analise, setAnalise] = useState(null);
  const [loadingAnalise, setLoadingAnalise] = useState(false);
  const [showMovModal, setShowMovModal] = useState(false);
  const [movForm, setMovForm] = useState({ titulo: "", descricao: "", data: new Date().toISOString().slice(0, 10) });

  const [showEditModal, setShowEditModal] = useState(false);
  const [editForm, setEditForm] = useState(EMPTY_EDIT_FORM);
  const [clientes, setClientes] = useState([]);
  const [tipos, setTipos] = useState([]);
  const [varas, setVaras] = useState([]);
  const [savingEdit, setSavingEdit] = useState(false);

  async function carregarProcesso() {
    const res = await api.get(`/processos/${id}/`);
    setProcesso(res.data);
    setEditForm({
      numero: res.data.numero || "",
      cliente: res.data.cliente || "",
      tipo: res.data.tipo || "",
      vara: res.data.vara || "",
      status: res.data.status || "em_andamento",
      tipo_caso: res.data.tipo_caso || "contencioso",
      valor_causa: res.data.valor_causa || "",
      objeto: res.data.objeto || "",
    });
    setWorkflowForm({
      tipo_caso: res.data.tipo_caso || "contencioso",
      etapa_workflow: res.data.etapa_workflow || "triagem",
    });
  }

  async function carregarMovimentacoes() {
    const res = await api.get(`/processos/${id}/movimentacoes/`);
    setMovs(toList(res.data));
  }

  async function carregarEstruturas() {
    const [w, p, r, t, pr, pe, u] = await Promise.all([
      api.get(`/processos/${id}/workflow/`).catch(() => ({ data: null })),
      api.get(`/processos/${id}/partes/`).catch(() => ({ data: [] })),
      api.get(`/processos/${id}/responsaveis/`).catch(() => ({ data: [] })),
      api.get(`/processos/${id}/tarefas/`).catch(() => ({ data: [] })),
      api.get(`/processos/${id}/prazos/`).catch(() => ({ data: [] })),
      api.get(`/processos/${id}/pecas/`).catch(() => ({ data: [] })),
      api.get("/usuarios/?limit=400").catch(() => ({ data: [] })),
    ]);

    if (w.data) {
      setWorkflowForm({
        tipo_caso: w.data.tipo_caso || "contencioso",
        etapa_workflow: w.data.etapa_workflow || "triagem",
      });
    }

    setPartes(toList(p.data));
    setResponsaveis(toList(r.data));
    setTarefas(toList(t.data));
    setPrazos(toList(pr.data));
    setPecas(toList(pe.data));
    setUsuarios(toList(u.data));
  }

  async function recarregarTudo() {
    await Promise.all([carregarProcesso(), carregarMovimentacoes(), carregarEstruturas()]);
  }

  useEffect(() => {
    recarregarTudo().catch(() => {
      toast.error("Processo não encontrado");
    });
  }, [id]);

  useEffect(() => {
    if (!showEditModal) return;
    Promise.all([
      api.get("/clientes/?limit=500").catch(() => ({ data: [] })),
      api.get("/tipos-processo/?limit=300").catch(() => ({ data: [] })),
      api.get("/varas/?limit=300").catch(() => ({ data: [] })),
    ]).then(([c, t, v]) => {
      setClientes(toList(c.data));
      setTipos(toList(t.data));
      setVaras(toList(v.data));
    });
  }, [showEditModal]);

  async function handleAnaliseIA() {
    setLoadingAnalise(true);
    try {
      const res = await api.post("/ia/analises/analisar/", { processo_id: parseInt(id, 10) });
      setAnalise(res.data);
      toast.success("Análise IA concluída");
    } catch (err) {
      toast.error("Erro na análise IA: " + (err.response?.data?.erro || err.message));
    } finally {
      setLoadingAnalise(false);
    }
  }

  async function handleAddMovimentacao(e) {
    e.preventDefault();
    try {
      await api.post("/movimentacoes/", { ...movForm, processo: parseInt(id, 10) });
      toast.success("Movimentação adicionada");
      setShowMovModal(false);
      setMovForm({ titulo: "", descricao: "", data: new Date().toISOString().slice(0, 10) });
      await carregarMovimentacoes();
    } catch {
      toast.error("Erro ao adicionar movimentação");
    }
  }

  async function handleSalvarEdicao(e) {
    e.preventDefault();
    if (!processo) return;

    const payload = {
      numero: editForm.numero,
      cliente: Number(editForm.cliente),
      tipo: Number(editForm.tipo),
      vara: editForm.vara ? Number(editForm.vara) : null,
      status: editForm.status,
      tipo_caso: editForm.tipo_caso,
      valor_causa: editForm.valor_causa === "" ? null : editForm.valor_causa,
      objeto: editForm.objeto,
    };

    setSavingEdit(true);
    try {
      const res = await api.patch(`/processos/${processo.id}/`, payload);
      setProcesso(res.data);
      setShowEditModal(false);
      toast.success("Processo atualizado");
      await carregarEstruturas();
    } catch (err) {
      const data = err.response?.data;
      toast.error(data ? JSON.stringify(data).slice(0, 180) : "Erro ao atualizar processo");
    } finally {
      setSavingEdit(false);
    }
  }

  async function handleExcluirProcesso() {
    if (!processo) return;
    if (!confirm(`Excluir o processo ${processo.numero}?`)) return;

    try {
      await api.delete(`/processos/${processo.id}/`);
      toast.success("Processo excluído");
      navigate("/processos");
    } catch {
      toast.error("Não foi possível excluir o processo");
    }
  }

  async function atualizarStatus(acao, label) {
    if (!processo) return;
    if (!confirm(`${label} o processo ${processo.numero}?`)) return;

    try {
      const res = await api.post(`/processos/${processo.id}/${acao}/`);
      setProcesso(res.data);
      toast.success(`Processo ${label.toLowerCase()} com sucesso`);
    } catch {
      toast.error(`Erro ao ${label.toLowerCase()} processo`);
    }
  }

  async function salvarWorkflow() {
    if (!processo) return;
    try {
      const res = await api.patch(`/processos/${processo.id}/workflow/`, workflowForm);
      setProcesso(res.data);
      toast.success("Workflow atualizado");
    } catch (err) {
      const data = err.response?.data;
      toast.error(data?.detail || "Falha ao atualizar workflow");
    }
  }

  async function adicionarParte(e) {
    e.preventDefault();
    if (!processo) return;
    if (!parteForm.nome.trim()) {
      toast.error("Informe o nome da parte");
      return;
    }
    try {
      await api.post(`/processos/${processo.id}/partes/`, parteForm);
      setParteForm(EMPTY_PARTE_FORM);
      await carregarEstruturas();
      toast.success("Parte cadastrada");
    } catch {
      toast.error("Erro ao cadastrar parte");
    }
  }

  async function toggleParteAtiva(parte) {
    if (!processo) return;
    try {
      await api.patch(`/processos/${processo.id}/partes/${parte.id}/`, { ativo: !parte.ativo });
      await carregarEstruturas();
    } catch {
      toast.error("Falha ao atualizar parte");
    }
  }

  async function adicionarResponsavel(e) {
    e.preventDefault();
    if (!processo) return;
    if (!responsavelForm.usuario) {
      toast.error("Selecione um usuário");
      return;
    }
    try {
      await api.post(`/processos/${processo.id}/responsaveis/`, {
        usuario: Number(responsavelForm.usuario),
        papel: responsavelForm.papel,
      });
      setResponsavelForm(EMPTY_RESP_FORM);
      await carregarEstruturas();
      toast.success("Responsável atualizado");
    } catch {
      toast.error("Erro ao atualizar responsáveis");
    }
  }

  async function toggleResponsavelAtivo(item) {
    if (!processo) return;
    try {
      await api.patch(`/processos/${processo.id}/responsaveis/${item.id}/`, { ativo: !item.ativo });
      await carregarEstruturas();
    } catch {
      toast.error("Falha ao atualizar responsável");
    }
  }

  async function adicionarTarefa(e) {
    e.preventDefault();
    if (!processo) return;
    if (!tarefaForm.titulo.trim()) {
      toast.error("Informe o título da tarefa");
      return;
    }
    try {
      const payload = {
        ...tarefaForm,
        responsavel: tarefaForm.responsavel ? Number(tarefaForm.responsavel) : null,
        prazo_em: tarefaForm.prazo_em || null,
      };
      await api.post(`/processos/${processo.id}/tarefas/`, payload);
      setTarefaForm(EMPTY_TAREFA_FORM);
      await carregarEstruturas();
      toast.success("Tarefa adicionada");
    } catch {
      toast.error("Erro ao cadastrar tarefa");
    }
  }

  async function concluirTarefa(tarefa) {
    if (!processo) return;
    try {
      await api.post(`/processos/${processo.id}/tarefas/${tarefa.id}/concluir/`);
      await carregarEstruturas();
      toast.success("Tarefa concluída");
    } catch {
      toast.error("Falha ao concluir tarefa");
    }
  }

  async function adicionarPrazo(e) {
    e.preventDefault();
    if (!processo) return;
    if (!prazoForm.data) {
      toast.error("Informe a data do prazo");
      return;
    }
    try {
      await api.post(`/processos/${processo.id}/prazos/`, prazoForm);
      setPrazoForm(EMPTY_PRAZO_FORM);
      await carregarEstruturas();
      toast.success("Prazo cadastrado");
    } catch {
      toast.error("Erro ao cadastrar prazo");
    }
  }

  async function concluirPrazo(prazo) {
    if (!processo) return;
    try {
      await api.post(`/processos/${processo.id}/prazos/${prazo.id}/concluir/`);
      await carregarEstruturas();
      toast.success("Prazo concluído");
    } catch {
      toast.error("Falha ao concluir prazo");
    }
  }

  async function salvarPeca(e) {
    e.preventDefault();
    if (!processo) return;
    if (!pecaForm.titulo.trim()) {
      toast.error("Informe o título da peça");
      return;
    }
    if (!pecaForm.conteudo.trim()) {
      toast.error("Informe o conteúdo da peça");
      return;
    }

    try {
      if (selectedPecaId) {
        await api.patch(`/processos/${processo.id}/pecas/${selectedPecaId}/`, pecaForm);
        toast.success("Peça atualizada");
      } else {
        await api.post(`/processos/${processo.id}/pecas/`, pecaForm);
        toast.success("Peça criada");
      }
      setPecaForm(EMPTY_PECA_FORM);
      setSelectedPecaId(null);
      setRevisaoPecaIA(null);
      await carregarEstruturas();
    } catch {
      toast.error("Erro ao salvar peça");
    }
  }

  function editarPeca(item) {
    setSelectedPecaId(item.id);
    setPecaForm({
      titulo: item.titulo || "",
      tipo_peca: item.tipo_peca || "peticao",
      status: item.status || "rascunho",
      conteudo: item.conteudo || "",
    });
    setRevisaoPecaIA(item.ia_revisao || null);
  }

  async function excluirPeca(item) {
    if (!processo) return;
    if (!confirm(`Excluir a peça "${item.titulo}"?`)) return;
    try {
      await api.delete(`/processos/${processo.id}/pecas/${item.id}/`);
      if (selectedPecaId === item.id) {
        setSelectedPecaId(null);
        setPecaForm(EMPTY_PECA_FORM);
        setRevisaoPecaIA(null);
      }
      await carregarEstruturas();
      toast.success("Peça excluída");
    } catch {
      toast.error("Erro ao excluir peça");
    }
  }

  async function gerarMinutaIA() {
    if (!processo) return;
    setLoadingPecaIA(true);
    try {
      const res = await api.post("/ia/analises/redigir-peca/", {
        processo_id: processo.id,
        tipo_peca: pecaForm.tipo_peca,
        objetivo: pecaForm.titulo || processo.objeto,
        tese_principal: processo.objeto,
      });
      setPecaForm((prev) => ({ ...prev, conteudo: res.data?.texto || prev.conteudo }));
      toast.success("Minuta gerada por IA");
    } catch {
      toast.error("Erro ao gerar minuta com IA");
    } finally {
      setLoadingPecaIA(false);
    }
  }

  async function revisarPecaIA() {
    if (!pecaForm.conteudo.trim()) {
      toast.error("Escreva a peça antes de revisar");
      return;
    }
    setLoadingPecaIA(true);
    try {
      const res = await api.post("/ia/analises/revisar-peca/", {
        tipo_peca: pecaForm.tipo_peca,
        texto: pecaForm.conteudo,
      });
      setRevisaoPecaIA(res.data);
      if (selectedPecaId) {
        await api.patch(`/processos/${processo.id}/pecas/${selectedPecaId}/`, {
          ia_revisao: res.data,
          ia_score_qualidade: res.data?.score_qualidade || 0,
        });
      }
      toast.success("Revisão IA concluída");
    } catch {
      toast.error("Erro na revisão IA");
    } finally {
      setLoadingPecaIA(false);
    }
  }

  if (!processo) return <div className="text-center py-20 text-gray-400">Carregando...</div>;

  const riscoCor = { baixo: "text-green-600", medio: "text-yellow-600", alto: "text-red-600" };
  const riscoIcon = { baixo: "🟢", medio: "🟡", alto: "🔴" };
  const etapasOpcoes = ETAPAS_WORKFLOW[workflowForm.tipo_caso] || ETAPAS_WORKFLOW.contencioso;

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <button onClick={() => navigate("/processos")} className="hover:text-primary-600">Processos</button>
          <span>/</span>
          <span className="text-gray-800 font-medium">{processo.numero}</span>
        </div>
        <button onClick={() => navigate("/processos")} className="btn-secondary text-sm">
          ← Voltar
        </button>
      </div>

      <div className="card">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-bold text-gray-900 font-mono">{processo.numero}</h1>
            <Link to={`/clientes/${processo.cliente}`} className="text-sm text-primary-700 hover:text-primary-900 mt-1 inline-block">
              Cliente: {processo.cliente_nome}
            </Link>
          </div>
          <div className="flex items-center gap-2 flex-wrap justify-end">
            <span className={STATUS_BADGE[processo.status] || "badge-gray"}>
              {processo.status_display || STATUS_LABELS[processo.status] || processo.status}
            </span>
            <button onClick={() => setShowEditModal(true)} className="btn-secondary text-sm">Editar</button>
            <button onClick={handleExcluirProcesso} className="btn-secondary text-sm text-red-700">Excluir</button>
            <button onClick={() => atualizarStatus("inativar", "Inativar")} className="btn-secondary text-sm text-amber-700">Inativar</button>
            <button onClick={() => atualizarStatus("concluir", "Concluir")} className="btn-secondary text-sm text-green-700">Concluído</button>
            <button onClick={() => atualizarStatus("arquivar", "Arquivar")} className="btn-secondary text-sm text-gray-700">Arquivar Processo</button>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5 pt-5 border-t border-gray-100">
          <InfoItem label="Tipo" value={processo.tipo_nome || "-"} />
          <InfoItem label="Vara" value={processo.vara_nome || "-"} />
          <InfoItem label="Tipo de Caso" value={processo.tipo_caso_display || TIPO_CASO_LABELS[processo.tipo_caso] || "-"} />
          <InfoItem label="Workflow" value={processo.etapa_workflow_display || "-"} />
          <InfoItem
            label="Valor da Causa"
            value={
              processo.valor_causa
                ? `R$ ${Number(processo.valor_causa).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                : "-"
            }
          />
          <InfoItem label="Advogado" value={processo.advogado_nome || "-"} />
          <InfoItem label="Status" value={processo.status_display || STATUS_LABELS[processo.status] || processo.status} />
          <InfoItem label="Última atualização" value={processo.atualizado_em ? new Date(processo.atualizado_em).toLocaleString("pt-BR") : "-"} />
        </div>

        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="text-xs text-gray-500 mb-1">Objeto / Descrição</div>
          <p className="text-sm text-gray-700 whitespace-pre-wrap">{processo.objeto || "-"}</p>
        </div>
      </div>

      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold">Workflow do Caso</h2>
          <button onClick={salvarWorkflow} className="btn-primary text-sm">Salvar Workflow</button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Tipo de Caso</label>
            <select
              className="input"
              value={workflowForm.tipo_caso}
              onChange={(e) => {
                const tipo = e.target.value;
                const defaultEtapa = (ETAPAS_WORKFLOW[tipo] || [])[0]?.value || "triagem";
                setWorkflowForm({ tipo_caso: tipo, etapa_workflow: defaultEtapa });
              }}
            >
              {Object.entries(TIPO_CASO_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Etapa</label>
            <select className="input" value={workflowForm.etapa_workflow} onChange={(e) => setWorkflowForm({ ...workflowForm, etapa_workflow: e.target.value })}>
              {etapasOpcoes.map((etapa) => (
                <option key={etapa.value} value={etapa.value}>{etapa.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="card space-y-4">
          <h2 className="text-base font-semibold">Partes do Processo</h2>
          <form onSubmit={adicionarParte} className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="label">Tipo</label>
                <select className="input" value={parteForm.tipo_parte} onChange={(e) => setParteForm({ ...parteForm, tipo_parte: e.target.value })}>
                  <option value="autor">Autor</option>
                  <option value="reu">Réu</option>
                  <option value="terceiro">Terceiro</option>
                  <option value="assistente">Assistente</option>
                  <option value="testemunha">Testemunha</option>
                  <option value="outro">Outro</option>
                </select>
              </div>
              <div>
                <label className="label">CPF/CNPJ</label>
                <input className="input" value={parteForm.documento} onChange={(e) => setParteForm({ ...parteForm, documento: e.target.value })} />
              </div>
            </div>
            <div>
              <label className="label">Nome</label>
              <input className="input" value={parteForm.nome} onChange={(e) => setParteForm({ ...parteForm, nome: e.target.value })} required />
            </div>
            <div>
              <label className="label">Observações</label>
              <textarea className="input" rows={2} value={parteForm.observacoes} onChange={(e) => setParteForm({ ...parteForm, observacoes: e.target.value })} />
            </div>
            <button type="submit" className="btn-secondary text-sm">+ Adicionar Parte</button>
          </form>
          <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
            {partes.length === 0 ? <p className="text-sm text-gray-400">Nenhuma parte cadastrada.</p> : partes.map((parte) => (
              <div key={parte.id} className="rounded-lg border border-gray-200 p-2 text-sm flex items-center justify-between gap-2">
                <div>
                  <div className="font-medium">{parte.nome}</div>
                  <div className="text-xs text-gray-500">{parte.tipo_parte_display || parte.tipo_parte} • {parte.documento || "Sem documento"}</div>
                </div>
                <button onClick={() => toggleParteAtiva(parte)} className="btn-secondary text-xs px-3 py-1">
                  {parte.ativo ? "Inativar" : "Ativar"}
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="card space-y-4">
          <h2 className="text-base font-semibold">Responsáveis</h2>
          <form onSubmit={adicionarResponsavel} className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="md:col-span-2">
              <label className="label">Usuário</label>
              <select className="input" value={responsavelForm.usuario} onChange={(e) => setResponsavelForm({ ...responsavelForm, usuario: e.target.value })}>
                <option value="">Selecione...</option>
                {usuarios.map((u) => (
                  <option key={u.id} value={u.id}>{userLabel(u)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Papel</label>
              <select className="input" value={responsavelForm.papel} onChange={(e) => setResponsavelForm({ ...responsavelForm, papel: e.target.value })}>
                <option value="principal">Principal</option>
                <option value="apoio">Apoio</option>
                <option value="estagiario">Estagiário</option>
              </select>
            </div>
            <div className="md:col-span-3">
              <button type="submit" className="btn-secondary text-sm">+ Vincular Responsável</button>
            </div>
          </form>

          <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
            {responsaveis.length === 0 ? <p className="text-sm text-gray-400">Nenhum responsável vinculado.</p> : responsaveis.map((r) => (
              <div key={r.id} className="rounded-lg border border-gray-200 p-2 text-sm flex items-center justify-between gap-2">
                <div>
                  <div className="font-medium">{r.usuario_nome || `Usuário #${r.usuario}`}</div>
                  <div className="text-xs text-gray-500">{r.papel_display || PAPEL_RESPONSAVEL[r.papel] || r.papel}</div>
                </div>
                <button onClick={() => toggleResponsavelAtivo(r)} className="btn-secondary text-xs px-3 py-1">
                  {r.ativo ? "Inativar" : "Ativar"}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="card space-y-4">
          <h2 className="text-base font-semibold">Tarefas do Processo</h2>
          <form onSubmit={adicionarTarefa} className="space-y-3">
            <div>
              <label className="label">Título</label>
              <input className="input" required value={tarefaForm.titulo} onChange={(e) => setTarefaForm({ ...tarefaForm, titulo: e.target.value })} />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="label">Prioridade</label>
                <select className="input" value={tarefaForm.prioridade} onChange={(e) => setTarefaForm({ ...tarefaForm, prioridade: e.target.value })}>
                  {Object.entries(PRIORIDADE_TAREFA).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Prazo</label>
                <input className="input" type="datetime-local" value={tarefaForm.prazo_em} onChange={(e) => setTarefaForm({ ...tarefaForm, prazo_em: e.target.value })} />
              </div>
              <div>
                <label className="label">Responsável</label>
                <select className="input" value={tarefaForm.responsavel} onChange={(e) => setTarefaForm({ ...tarefaForm, responsavel: e.target.value })}>
                  <option value="">Automático</option>
                  {usuarios.map((u) => (
                    <option key={u.id} value={u.id}>{userLabel(u)}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="label">Descrição</label>
              <textarea className="input" rows={2} value={tarefaForm.descricao} onChange={(e) => setTarefaForm({ ...tarefaForm, descricao: e.target.value })} />
            </div>
            <button type="submit" className="btn-secondary text-sm">+ Adicionar Tarefa</button>
          </form>

          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {tarefas.length === 0 ? <p className="text-sm text-gray-400">Nenhuma tarefa registrada.</p> : tarefas.map((t) => (
              <div key={t.id} className="rounded-lg border border-gray-200 p-2 text-sm flex items-center justify-between gap-2">
                <div>
                  <div className="font-medium">{t.titulo}</div>
                  <div className="text-xs text-gray-500">{t.prioridade_display || PRIORIDADE_TAREFA[t.prioridade] || t.prioridade} • {t.responsavel_nome || "Sem responsável"}</div>
                  <div className="text-xs text-gray-400">Prazo: {fmtDate(t.prazo_em)}</div>
                </div>
                {t.status !== "concluida" ? (
                  <button onClick={() => concluirTarefa(t)} className="btn-secondary text-xs px-3 py-1">Concluir</button>
                ) : (
                  <span className="badge-green">Concluída</span>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="card space-y-4">
          <h2 className="text-base font-semibold">Prazos e Lembretes</h2>
          <form onSubmit={adicionarPrazo} className="space-y-3">
            <div>
              <label className="label">Título</label>
              <input className="input" value={prazoForm.titulo} onChange={(e) => setPrazoForm({ ...prazoForm, titulo: e.target.value })} placeholder="Prazo - manifestação" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="label">Data</label>
                <input className="input" type="date" required value={prazoForm.data} onChange={(e) => setPrazoForm({ ...prazoForm, data: e.target.value })} />
              </div>
              <div>
                <label className="label">Hora</label>
                <input className="input" type="time" value={prazoForm.hora} onChange={(e) => setPrazoForm({ ...prazoForm, hora: e.target.value })} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Lembrar (dias antes)</label>
                <input className="input" type="number" min={0} value={prazoForm.alerta_dias_antes} onChange={(e) => setPrazoForm({ ...prazoForm, alerta_dias_antes: Number(e.target.value || 0) })} />
              </div>
              <div>
                <label className="label">Lembrar (horas antes)</label>
                <input className="input" type="number" min={0} value={prazoForm.alerta_horas_antes} onChange={(e) => setPrazoForm({ ...prazoForm, alerta_horas_antes: Number(e.target.value || 0) })} />
              </div>
            </div>
            <div>
              <label className="label">Descrição</label>
              <textarea className="input" rows={2} value={prazoForm.descricao} onChange={(e) => setPrazoForm({ ...prazoForm, descricao: e.target.value })} />
            </div>
            <button type="submit" className="btn-secondary text-sm">+ Adicionar Prazo</button>
          </form>

          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {prazos.length === 0 ? <p className="text-sm text-gray-400">Nenhum prazo cadastrado.</p> : prazos.map((p) => (
              <div key={p.id} className="rounded-lg border border-gray-200 p-2 text-sm flex items-center justify-between gap-2">
                <div>
                  <div className="font-medium">{p.titulo}</div>
                  <div className="text-xs text-gray-500">{p.data ? new Date(`${p.data}T00:00:00`).toLocaleDateString("pt-BR") : "-"} {p.hora || ""}</div>
                  <div className="text-xs text-gray-400">Lembrete: {p.alerta_dias_antes}d e {p.alerta_horas_antes}h antes</div>
                </div>
                {p.status !== "concluido" ? (
                  <button onClick={() => concluirPrazo(p)} className="btn-secondary text-xs px-3 py-1">Concluir</button>
                ) : (
                  <span className="badge-green">Concluído</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card space-y-4">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <h2 className="text-base font-semibold">Peças e Recursos (Assistente IA)</h2>
          {selectedPecaId && (
            <button
              onClick={() => {
                setSelectedPecaId(null);
                setPecaForm(EMPTY_PECA_FORM);
                setRevisaoPecaIA(null);
              }}
              className="btn-secondary text-xs"
            >
              Novo Rascunho
            </button>
          )}
        </div>

        <form onSubmit={salvarPeca} className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="md:col-span-2">
              <label className="label">Título</label>
              <input
                className="input"
                value={pecaForm.titulo}
                onChange={(e) => setPecaForm({ ...pecaForm, titulo: e.target.value })}
                placeholder="Ex.: Contestação inicial"
              />
            </div>
            <div>
              <label className="label">Tipo</label>
              <select
                className="input"
                value={pecaForm.tipo_peca}
                onChange={(e) => setPecaForm({ ...pecaForm, tipo_peca: e.target.value })}
              >
                <option value="defesa">Defesa</option>
                <option value="recurso">Recurso</option>
                <option value="peticao">Petição</option>
                <option value="manifestacao">Manifestação</option>
                <option value="outro">Outro</option>
              </select>
            </div>
          </div>

          <div>
            <label className="label">Conteúdo da Peça</label>
            <textarea
              className="input min-h-[240px] font-mono text-xs"
              value={pecaForm.conteudo}
              onChange={(e) => setPecaForm({ ...pecaForm, conteudo: e.target.value })}
              placeholder="Estruture em fatos, direito e pedidos..."
            />
          </div>

          <div className="flex gap-2 flex-wrap">
            <button type="button" onClick={gerarMinutaIA} className="btn-secondary text-sm" disabled={loadingPecaIA}>
              {loadingPecaIA ? "Processando..." : "Gerar Minuta IA"}
            </button>
            <button type="button" onClick={revisarPecaIA} className="btn-secondary text-sm" disabled={loadingPecaIA}>
              {loadingPecaIA ? "Processando..." : "Revisar IA"}
            </button>
            <button type="submit" className="btn-primary text-sm">
              {selectedPecaId ? "Salvar Alterações" : "Salvar Peça"}
            </button>
          </div>
        </form>

        {revisaoPecaIA && (
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
            <div className="text-sm font-semibold text-blue-800">
              Score IA: {revisaoPecaIA.score_qualidade ?? 0}/100
            </div>
            {revisaoPecaIA.riscos_indeferimento?.length > 0 && (
              <div className="mt-2 text-xs text-red-700">
                <div className="font-semibold">Riscos de indeferimento:</div>
                {revisaoPecaIA.riscos_indeferimento.map((item, idx) => (
                  <div key={idx}>• {item}</div>
                ))}
              </div>
            )}
            {revisaoPecaIA.erros_gramatica?.length > 0 && (
              <div className="mt-2 text-xs text-amber-700">
                <div className="font-semibold">Erros de gramática:</div>
                {revisaoPecaIA.erros_gramatica.map((item, idx) => (
                  <div key={idx}>• {item}</div>
                ))}
              </div>
            )}
            {revisaoPecaIA.erros_logica?.length > 0 && (
              <div className="mt-2 text-xs text-red-700">
                <div className="font-semibold">Erros de lógica:</div>
                {revisaoPecaIA.erros_logica.map((item, idx) => (
                  <div key={idx}>• {item}</div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
          {pecas.length === 0 ? (
            <p className="text-sm text-gray-400">Nenhuma peça cadastrada para este processo.</p>
          ) : (
            pecas.map((item) => (
              <div key={item.id} className="rounded-lg border border-gray-200 p-3 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <div className="font-medium">{item.titulo}</div>
                    <div className="text-xs text-gray-500">
                      {item.tipo_peca_display || item.tipo_peca} • v{item.versao} • {item.status_display || item.status}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => editarPeca(item)} className="btn-secondary text-xs px-3 py-1">
                      Editar
                    </button>
                    <button onClick={() => excluirPeca(item)} className="btn-secondary text-xs px-3 py-1 text-red-700">
                      Excluir
                    </button>
                  </div>
                </div>
                {item.ia_score_qualidade ? (
                  <div className="text-xs text-blue-700 mt-1">Score IA: {item.ia_score_qualidade}/100</div>
                ) : null}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold">Análise de Risco (IA)</h2>
          <button onClick={handleAnaliseIA} disabled={loadingAnalise} className="btn-primary text-sm">
            {loadingAnalise ? "Analisando..." : "Analisar com IA"}
          </button>
        </div>
        {analise ? (
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-primary-700">
                  {Number(analise.probabilidade_sucesso ?? analise.probabilidade_exito ?? 0).toFixed(2)}%
                </div>
                <div className="text-xs text-gray-500">Prob. de Êxito</div>
              </div>
              <div className="text-center">
                <div className={`text-2xl font-bold ${riscoCor[analise.nivel_risco] || "text-gray-600"}`}>
                  {riscoIcon[analise.nivel_risco]} {analise.nivel_risco?.toUpperCase()}
                </div>
                <div className="text-xs text-gray-500">Nível de Risco</div>
              </div>
            </div>
            {analise.justificativa && (
              <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap">{analise.justificativa}</div>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-400">Clique em "Analisar com IA" para obter uma análise preditiva deste processo.</p>
        )}
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold">Movimentações</h2>
          <button onClick={() => setShowMovModal(true)} className="btn-secondary text-sm">+ Adicionar</button>
        </div>
        {movs.length === 0 ? (
          <p className="text-sm text-gray-400">Nenhuma movimentação registrada</p>
        ) : (
          <div className="space-y-3">
            {movs.map((m) => (
              <div key={m.id} className="border-l-4 border-primary-200 pl-4 py-1">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium text-sm">{m.titulo}</div>
                  <div className="text-xs text-gray-500">{m.data ? new Date(m.data).toLocaleDateString("pt-BR") : ""}</div>
                </div>
                <div className="text-xs text-gray-600 mt-0.5">{m.descricao}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showMovModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
            <div className="p-6 border-b flex justify-between items-center">
              <h2 className="text-lg font-semibold">Nova Movimentação</h2>
              <button onClick={() => setShowMovModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>
            <form onSubmit={handleAddMovimentacao} className="p-6 space-y-4">
              <div>
                <label className="label">Título *</label>
                <input className="input" required value={movForm.titulo} onChange={(e) => setMovForm({ ...movForm, titulo: e.target.value })} />
              </div>
              <div>
                <label className="label">Data *</label>
                <input className="input" type="date" required value={movForm.data} onChange={(e) => setMovForm({ ...movForm, data: e.target.value })} />
              </div>
              <div>
                <label className="label">Descrição *</label>
                <textarea className="input" rows={3} required value={movForm.descricao} onChange={(e) => setMovForm({ ...movForm, descricao: e.target.value })} />
              </div>
              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setShowMovModal(false)} className="btn-secondary">Cancelar</button>
                <button type="submit" className="btn-primary">Salvar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showEditModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-lg font-semibold">Editar Processo</h2>
              <button onClick={() => setShowEditModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>

            <form onSubmit={handleSalvarEdicao} className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Número do Processo *</label>
                  <input
                    className="input"
                    required
                    value={editForm.numero}
                    onChange={(e) => setEditForm({ ...editForm, numero: e.target.value })}
                  />
                </div>

                <div>
                  <label className="label">Status</label>
                  <select
                    className="input"
                    value={editForm.status}
                    onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                  >
                    {Object.entries(STATUS_LABELS).map(([k, v]) => (
                      <option key={k} value={k}>{v}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="label">Cliente *</label>
                  <select
                    className="input"
                    required
                    value={editForm.cliente}
                    onChange={(e) => setEditForm({ ...editForm, cliente: e.target.value })}
                  >
                    <option value="">Selecione...</option>
                    {clientes.map((c) => (
                      <option key={c.id} value={c.id}>{c.nome}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="label">Tipo de Processo *</label>
                  <select
                    className="input"
                    required
                    value={editForm.tipo}
                    onChange={(e) => setEditForm({ ...editForm, tipo: e.target.value })}
                  >
                    <option value="">Selecione...</option>
                    {tipos.map((t) => (
                      <option key={t.id} value={t.id}>{t.nome}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="label">Vara</label>
                  <select
                    className="input"
                    value={editForm.vara || ""}
                    onChange={(e) => setEditForm({ ...editForm, vara: e.target.value })}
                  >
                    <option value="">Selecione...</option>
                    {varas.map((v) => (
                      <option key={v.id} value={v.id}>{v.nome} - {v.comarca_nome || ""}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="label">Tipo de Caso</label>
                  <select
                    className="input"
                    value={editForm.tipo_caso}
                    onChange={(e) => setEditForm({ ...editForm, tipo_caso: e.target.value })}
                  >
                    {Object.entries(TIPO_CASO_LABELS).map(([k, v]) => (
                      <option key={k} value={k}>{v}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="label">Valor da Causa (R$)</label>
                  <input
                    className="input"
                    type="number"
                    step="0.01"
                    value={editForm.valor_causa}
                    onChange={(e) => setEditForm({ ...editForm, valor_causa: e.target.value })}
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="label">Objeto / Descrição *</label>
                  <textarea
                    className="input"
                    rows={3}
                    required
                    value={editForm.objeto}
                    onChange={(e) => setEditForm({ ...editForm, objeto: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setShowEditModal(false)} className="btn-secondary">Cancelar</button>
                <button type="submit" className="btn-primary" disabled={savingEdit}>
                  {savingEdit ? "Salvando..." : "Salvar"}
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
      <div className="text-sm font-medium text-gray-800 mt-0.5">{value}</div>
    </div>
  );
}
