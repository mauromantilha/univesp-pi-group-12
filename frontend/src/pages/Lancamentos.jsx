import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import api from "../api/axios";
import toast from "react-hot-toast";

const STATUS_LABEL = {
  pendente: "Pendente",
  pago: "Pago",
  atrasado: "Atrasado",
  cancelado: "Cancelado",
};
const STATUS_COLOR = {
  pendente: "badge-blue",
  pago: "badge-green",
  atrasado: "badge-red",
  cancelado: "badge-gray",
};

function fmtBRL(v) {
  return Number(v || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
function fmtDate(d) {
  if (!d) return "—";
  return new Date(d + "T00:00:00").toLocaleDateString("pt-BR");
}

function isTipoReceita(tipo) {
  return ["receber", "honorario", "reembolso", "pagamento"].includes(tipo);
}

// ----------- Modal Novo Lançamento -----------
function ModalNovo({ onClose, onSaved, categorias, contas }) {
  const [form, setForm] = useState({
    tipo: "receber",
    descricao: "",
    valor: "",
    data_vencimento: "",
    categoria: "",
    conta_bancaria: "",
    processo: "",
    reembolsavel_cliente: false,
    observacoes: "",
  });
  const [saving, setSaving] = useState(false);
  const catFiltradas = categorias.filter((c) => c.tipo === form.tipo);

  function set(k, v) {
    setForm((prev) => ({ ...prev, [k]: v }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.descricao || !form.valor || !form.data_vencimento || !form.categoria) {
      toast.error("Preencha todos os campos obrigatórios");
      return;
    }
    setSaving(true);
    try {
      await api.post("/financeiro/lancamentos/", {
        ...form,
        tipo: form.tipo,
        valor: parseFloat(form.valor.replace(",", ".")),
        processo: form.processo || null,
        conta_bancaria: form.conta_bancaria || null,
      });
      toast.success("Lançamento criado!");
      onSaved();
    } catch (err) {
      toast.error("Erro ao criar lançamento");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-screen overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Novo Lançamento</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* Tipo */}
          <div className="flex gap-2">
            {["receber", "pagar"].map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => set("tipo", t)}
                className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-colors ${
                  form.tipo === t
                    ? t === "receber"
                      ? "bg-green-500 text-white border-green-500"
                      : "bg-red-500 text-white border-red-500"
                    : "bg-white text-gray-600 border-gray-300 hover:border-gray-400"
                }`}
              >
                {t === "receber" ? "📈 A Receber" : "📉 A Pagar"}
              </button>
            ))}
          </div>

          <div>
            <label className="label">Descrição *</label>
            <input className="input" value={form.descricao} onChange={(e) => set("descricao", e.target.value)} required />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Valor (R$) *</label>
              <input className="input" type="number" step="0.01" min="0" value={form.valor} onChange={(e) => set("valor", e.target.value)} required />
            </div>
            <div>
              <label className="label">Vencimento *</label>
              <input className="input" type="date" value={form.data_vencimento} onChange={(e) => set("data_vencimento", e.target.value)} required />
            </div>
          </div>
          <div>
            <label className="label">Categoria *</label>
            <select className="input" value={form.categoria} onChange={(e) => set("categoria", e.target.value)} required>
              <option value="">Selecione...</option>
              {catFiltradas.map((c) => (
                <option key={c.id} value={c.id}>{c.nome}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Conta Bancária</label>
            <select className="input" value={form.conta_bancaria} onChange={(e) => set("conta_bancaria", e.target.value)}>
              <option value="">Nenhuma</option>
              {contas.map((c) => (
                <option key={c.id} value={c.id}>{c.nome}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Observações</label>
            <textarea className="input" rows={2} value={form.observacoes} onChange={(e) => set("observacoes", e.target.value)} />
          </div>
          <label className="text-sm flex items-center gap-2">
            <input
              type="checkbox"
              checked={!!form.reembolsavel_cliente}
              onChange={(e) => set("reembolsavel_cliente", e.target.checked)}
            />
            Marcar como despesa reembolsável ao cliente
          </label>

          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary flex-1">
              {saving ? "Salvando..." : "Salvar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ----------- Modal Dar Baixa -----------
function ModalBaixa({ lancamento, contas, onClose, onSaved }) {
  const [form, setForm] = useState({
    data_pagamento: new Date().toISOString().split("T")[0],
    conta_bancaria_id: "",
  });
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post(`/financeiro/lancamentos/${lancamento.id}/baixar/`, {
        data_pagamento: form.data_pagamento,
        conta_bancaria_id: form.conta_bancaria_id || null,
      });
      toast.success("Baixa registrada com sucesso!");
      onSaved();
    } catch (err) {
      toast.error(err?.response?.data?.error || "Erro ao dar baixa");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Dar Baixa</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div className="bg-gray-50 rounded-lg p-3 text-sm">
            <div className="font-medium text-gray-800">{lancamento.descricao}</div>
            <div className="text-gray-500 mt-1">
              {isTipoReceita(lancamento.tipo) ? "📈 A Receber" : "📉 A Pagar"} ·{" "}
              <span className={isTipoReceita(lancamento.tipo) ? "text-green-600 font-semibold" : "text-red-600 font-semibold"}>
                {fmtBRL(lancamento.valor)}
              </span>
            </div>
          </div>

          <div>
            <label className="label">Data de Pagamento *</label>
            <input
              className="input"
              type="date"
              value={form.data_pagamento}
              onChange={(e) => setForm((f) => ({ ...f, data_pagamento: e.target.value }))}
              required
            />
          </div>
          <div>
            <label className="label">Conta Bancária</label>
            <select
              className="input"
              value={form.conta_bancaria_id}
              onChange={(e) => setForm((f) => ({ ...f, conta_bancaria_id: e.target.value }))}
            >
              <option value="">Nenhuma</option>
              {contas.map((c) => (
                <option key={c.id} value={c.id}>{c.nome} — {fmtBRL(c.saldo)}</option>
              ))}
            </select>
          </div>
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary flex-1">
              {saving ? "Processando..." : "Confirmar Baixa"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ----------- Main Page -----------
export default function Lancamentos() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tipoParam = searchParams.get("tipo") || "receber";
  const statusParam = searchParams.get("status") || "";

  const [tab, setTab] = useState(tipoParam === "pagar" || tipoParam === "despesa" ? "pagar" : "receber");
  const [lancamentos, setLancamentos] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [contas, setContas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalNovo, setModalNovo] = useState(false);
  const [modalBaixa, setModalBaixa] = useState(null);
  const [filtroStatus, setFiltroStatus] = useState(statusParam);

  const fetchData = useCallback(() => {
    setLoading(true);
    const params = { tipo: tab };
    if (filtroStatus) params.status = filtroStatus;
    Promise.all([
      api.get("/financeiro/lancamentos/", { params }),
      api.get("/financeiro/categorias/"),
      api.get("/financeiro/contas/"),
    ])
      .then(([l, c, ct]) => {
        setLancamentos(l.data?.results ?? l.data ?? []);
        setCategorias(c.data?.results ?? c.data ?? []);
        setContas(ct.data?.results ?? ct.data ?? []);
      })
      .catch(() => toast.error("Erro ao carregar lançamentos"))
      .finally(() => setLoading(false));
  }, [tab, filtroStatus]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  function handleTabChange(t) {
    setTab(t);
    setSearchParams((p) => { p.set("tipo", t); return p; });
  }

  const totalPendente = lancamentos
    .filter((l) => l.status === "pendente" || l.status === "atrasado")
    .reduce((s, l) => s + Number(l.valor), 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">💸 Lançamentos</h1>
          <p className="text-sm text-gray-500 mt-1">Controle de receitas e despesas</p>
        </div>
        <button onClick={() => setModalNovo(true)} className="btn-primary text-sm">
          + Novo Lançamento
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        {[
          { key: "receber", label: "📈 A Receber", color: "text-green-600 border-green-500" },
          { key: "pagar", label: "📉 A Pagar", color: "text-red-600 border-red-500" },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => handleTabChange(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
              tab === t.key ? t.color : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Filtros + Resumo */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Status:</span>
          {["", "pendente", "atrasado", "pago"].map((s) => (
            <button
              key={s}
              onClick={() => setFiltroStatus(s)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                filtroStatus === s
                  ? "bg-primary-600 text-white border-primary-600"
                  : "bg-white text-gray-600 border-gray-200 hover:border-gray-400"
              }`}
            >
              {s === "" ? "Todos" : STATUS_LABEL[s]}
            </button>
          ))}
        </div>
        <div className={`text-sm font-semibold ${tab === "receber" ? "text-green-600" : "text-red-600"}`}>
          Pendente: {fmtBRL(totalPendente)}
        </div>
      </div>

      {/* Tabela */}
      <div className="card p-0 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Vencimento</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Descrição</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Cliente</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Categoria</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Reembolso</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Valor</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Ações</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} className="text-center py-10 text-gray-400">Carregando...</td>
              </tr>
            ) : lancamentos.length === 0 ? (
              <tr>
                <td colSpan={8} className="text-center py-10 text-gray-400">
                  Nenhum lançamento encontrado
                </td>
              </tr>
            ) : (
              lancamentos.map((l) => (
                <tr key={l.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={l.status === "atrasado" ? "text-red-600 font-medium" : ""}>
                      {fmtDate(l.data_vencimento)}
                    </span>
                  </td>
                  <td className="px-4 py-3 max-w-xs truncate">{l.descricao}</td>
                  <td className="px-4 py-3 text-gray-500">{l.cliente_nome || "—"}</td>
                  <td className="px-4 py-3 text-gray-500">{l.categoria_nome || "—"}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {l.reembolsavel_cliente ? "Reembolsável" : "—"}
                  </td>
                  <td className={`px-4 py-3 text-right font-semibold ${
                    isTipoReceita(l.tipo) ? "text-green-600" : "text-red-600"
                  }`}>
                    {fmtBRL(l.valor)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={STATUS_COLOR[l.status] || "badge-gray"}>
                      {STATUS_LABEL[l.status] || l.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {(l.status === "pendente" || l.status === "atrasado") && (
                      <button
                        onClick={() => setModalBaixa(l)}
                        className="text-xs bg-green-100 text-green-700 hover:bg-green-200 px-2 py-1 rounded font-medium transition-colors"
                      >
                        ✓ Baixar
                      </button>
                    )}
                    {l.status === "pago" && (
                      <span className="text-xs text-gray-400">{fmtDate(l.data_pagamento)}</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {modalNovo && (
        <ModalNovo
          onClose={() => setModalNovo(false)}
          onSaved={() => { setModalNovo(false); fetchData(); }}
          categorias={categorias}
          contas={contas}
        />
      )}

      {modalBaixa && (
        <ModalBaixa
          lancamento={modalBaixa}
          contas={contas}
          onClose={() => setModalBaixa(null)}
          onSaved={() => { setModalBaixa(null); fetchData(); }}
        />
      )}
    </div>
  );
}
