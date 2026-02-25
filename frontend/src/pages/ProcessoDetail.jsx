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

function toList(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.results || [];
}

const EMPTY_EDIT_FORM = {
  numero: "",
  cliente: "",
  tipo: "",
  vara: "",
  status: "em_andamento",
  valor_causa: "",
  objeto: "",
};

export default function ProcessoDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [processo, setProcesso] = useState(null);
  const [movs, setMovs] = useState([]);
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
      valor_causa: res.data.valor_causa || "",
      objeto: res.data.objeto || "",
    });
  }

  async function carregarMovimentacoes() {
    const res = await api.get(`/processos/${id}/movimentacoes/`);
    setMovs(toList(res.data));
  }

  useEffect(() => {
    Promise.all([carregarProcesso(), carregarMovimentacoes()]).catch(() => {
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
      valor_causa: editForm.valor_causa === "" ? null : editForm.valor_causa,
      objeto: editForm.objeto,
    };

    setSavingEdit(true);
    try {
      const res = await api.patch(`/processos/${processo.id}/`, payload);
      setProcesso(res.data);
      setShowEditModal(false);
      toast.success("Processo atualizado");
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

  if (!processo) return <div className="text-center py-20 text-gray-400">Carregando...</div>;

  const riscoCor = { baixo: "text-green-600", medio: "text-yellow-600", alto: "text-red-600" };
  const riscoIcon = { baixo: "🟢", medio: "🟡", alto: "🔴" };

  return (
    <div className="space-y-6 max-w-4xl">
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

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-5 pt-5 border-t border-gray-100">
          <InfoItem label="Tipo" value={processo.tipo_nome || "-"} />
          <InfoItem label="Vara" value={processo.vara_nome || "-"} />
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
                <div className="text-3xl font-bold text-primary-700">{Math.round((analise.probabilidade_exito || 0) * 100)}%</div>
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
