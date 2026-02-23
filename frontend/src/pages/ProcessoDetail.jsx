import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/axios";
import toast from "react-hot-toast";

const STATUS_BADGE = { em_andamento:"badge-blue", suspenso:"badge-yellow", finalizado:"badge-green", arquivado:"badge-gray" };
const STATUS_LABELS = { em_andamento:"Em Andamento", suspenso:"Suspenso", finalizado:"Finalizado", arquivado:"Arquivado" };

export default function ProcessoDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [processo, setProcesso] = useState(null);
  const [movs, setMovs] = useState([]);
  const [analise, setAnalise] = useState(null);
  const [loadingAnalise, setLoadingAnalise] = useState(false);
  const [showMovModal, setShowMovModal] = useState(false);
  const [movForm, setMovForm] = useState({ titulo:"", descricao:"", data: new Date().toISOString().slice(0,10) });

  useEffect(() => {
    api.get(`/processos/${id}/`).then((r) => setProcesso(r.data)).catch(() => toast.error("Processo não encontrado"));
    api.get(`/processos/${id}/movimentacoes/`).then((r) => setMovs(r.data?.results || r.data || [])).catch(() => {});
  }, [id]);

  async function handleAnaliseIA() {
    setLoadingAnalise(true);
    try {
      const res = await api.post("/ia/analises/analisar/", { processo_id: parseInt(id) });
      setAnalise(res.data);
      toast.success("Análise IA concluída!");
    } catch (err) {
      toast.error("Erro na análise IA: " + (err.response?.data?.erro || err.message));
    } finally {
      setLoadingAnalise(false);
    }
  }

  async function handleAddMovimentacao(e) {
    e.preventDefault();
    try {
      await api.post("/movimentacoes/", { ...movForm, processo: parseInt(id) });
      toast.success("Movimentação adicionada!");
      setShowMovModal(false);
      const r = await api.get(`/processos/${id}/movimentacoes/`);
      setMovs(r.data?.results || r.data || []);
    } catch (err) {
      toast.error("Erro ao adicionar movimentação");
    }
  }

  if (!processo) return <div className="text-center py-20 text-gray-400">Carregando...</div>;

  const riscoCor = { baixo:"text-green-600", medio:"text-yellow-600", alto:"text-red-600" };
  const riscoIcon = { baixo:"🟢", medio:"🟡", alto:"🔴" };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <button onClick={() => navigate("/processos")} className="hover:text-primary-600">Processos</button>
        <span>/</span>
        <span className="text-gray-800 font-medium">{processo.numero}</span>
      </div>

      {/* Header */}
      <div className="card">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900 font-mono">{processo.numero}</h1>
            <p className="text-gray-500 mt-1">{processo.cliente_nome}</p>
          </div>
          <span className={STATUS_BADGE[processo.status] || "badge-gray"}>{STATUS_LABELS[processo.status] || processo.status}</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-5 pt-5 border-t border-gray-100">
          <InfoItem label="Tipo" value={processo.tipo_processo_nome} />
          <InfoItem label="Polo" value={processo.polo === "ativo" ? "Ativo (autor)" : processo.polo === "passivo" ? "Passivo (réu)" : "Terceiro"} />
          <InfoItem label="Parte Contrária" value={processo.parte_contraria || "—"} />
          <InfoItem label="Vara" value={processo.vara_nome || "—"} />
          <InfoItem label="Valor da Causa" value={processo.valor_causa ? `R$ ${Number(processo.valor_causa).toLocaleString("pt-BR")}` : "—"} />
          <InfoItem label="Advogado" value={processo.advogado_nome || "—"} />
        </div>

        {processo.descricao && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="text-xs text-gray-500 mb-1">Descrição</div>
            <p className="text-sm text-gray-700">{processo.descricao}</p>
          </div>
        )}
      </div>

      {/* Análise IA */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold">🤖 Análise de Risco (IA)</h2>
          <button onClick={handleAnaliseIA} disabled={loadingAnalise} className="btn-primary text-sm">
            {loadingAnalise ? "Analisando..." : "Analisar com IA"}
          </button>
        </div>
        {analise ? (
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-primary-700">{Math.round(analise.probabilidade_exito * 100)}%</div>
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

      {/* Movimentações */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold">📋 Movimentações</h2>
          <button onClick={() => setShowMovModal(true)} className="btn-secondary text-sm">+ Adicionar</button>
        </div>
        {movs.length === 0 ? (
          <p className="text-sm text-gray-400">Nenhuma movimentação registrada</p>
        ) : (
          <div className="space-y-3">
            {movs.map((m) => (
              <div key={m.id} className="border-l-4 border-primary-200 pl-4 py-1">
                <div className="flex items-center justify-between">
                  <div className="font-medium text-sm">{m.titulo}</div>
                  <div className="text-xs text-gray-500">{m.data ? new Date(m.data).toLocaleDateString("pt-BR") : ""}</div>
                </div>
                <div className="text-xs text-gray-600 mt-0.5">{m.descricao}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal Movimentação */}
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
                <input className="input" required value={movForm.titulo} onChange={(e) => setMovForm({...movForm, titulo: e.target.value})} />
              </div>
              <div>
                <label className="label">Data *</label>
                <input className="input" type="date" required value={movForm.data} onChange={(e) => setMovForm({...movForm, data: e.target.value})} />
              </div>
              <div>
                <label className="label">Descrição *</label>
                <textarea className="input" rows={3} required value={movForm.descricao} onChange={(e) => setMovForm({...movForm, descricao: e.target.value})} />
              </div>
              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setShowMovModal(false)} className="btn-secondary">Cancelar</button>
                <button type="submit" className="btn-primary">Salvar</button>
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
