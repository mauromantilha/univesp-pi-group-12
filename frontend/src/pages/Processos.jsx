import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api/axios";
import toast from "react-hot-toast";
import useDebouncedValue from "../hooks/useDebouncedValue";

const STATUS_LABELS = {
  em_andamento: "Em Andamento",
  suspenso: "Suspenso",
  finalizado: "Finalizado",
  arquivado: "Arquivado",
};

const STATUS_BADGE = {
  em_andamento: "badge-blue",
  suspenso: "badge-yellow",
  finalizado: "badge-green",
  arquivado: "badge-gray",
};

const TIPO_CASO_LABELS = {
  contencioso: "Contencioso",
  consultivo: "Consultivo",
  massificado: "Massificado",
};

const EMPTY_FORM = {
  numero: "",
  cliente: "",
  tipo: "",
  vara: "",
  status: "em_andamento",
  segredo_justica: false,
  tipo_caso: "contencioso",
  valor_causa: "",
  objeto: "",
};

function toList(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.results || [];
}

function formatMoney(value) {
  if (value === null || value === undefined || value === "") return "-";
  const num = Number(value);
  if (Number.isNaN(num)) return String(value);
  return `R$ ${num.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function Processos() {
  const navigate = useNavigate();
  const [processos, setProcessos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 350);
  const [filterStatus, setFilterStatus] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [clientes, setClientes] = useState([]);
  const [tipos, setTipos] = useState([]);
  const [varas, setVaras] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const fetchProcessos = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (debouncedSearch.trim()) params.set("search", debouncedSearch.trim());
    if (filterStatus) params.set("status", filterStatus);
    params.set("limit", "200");

    api
      .get(`/processos/?${params.toString()}`)
      .then((r) => setProcessos(toList(r.data)))
      .catch(() => toast.error("Erro ao carregar processos"))
      .finally(() => setLoading(false));
  }, [debouncedSearch, filterStatus]);

  useEffect(() => {
    fetchProcessos();
  }, [fetchProcessos]);

  useEffect(() => {
    if (!showModal) return;
    Promise.all([
      api.get("/clientes/?limit=500").catch(() => ({ data: [] })),
      api.get("/tipos-processo/?limit=300").catch(() => ({ data: [] })),
      api.get("/varas/?limit=300").catch(() => ({ data: [] })),
    ]).then(([c, t, v]) => {
      setClientes(toList(c.data));
      setTipos(toList(t.data));
      setVaras(toList(v.data));
    });
  }, [showModal]);

  function openModal() {
    setForm(EMPTY_FORM);
    setShowModal(true);
  }

  async function handleCreate(e) {
    e.preventDefault();
    if (!form.cliente) {
      toast.error("Selecione um cliente");
      return;
    }
    if (!form.tipo) {
      toast.error("Selecione o tipo do processo");
      return;
    }

    const payload = {
      numero: form.numero,
      cliente: Number(form.cliente),
      tipo: Number(form.tipo),
      vara: form.vara ? Number(form.vara) : null,
      status: form.status,
      segredo_justica: !!form.segredo_justica,
      tipo_caso: form.tipo_caso,
      valor_causa: form.valor_causa === "" ? null : form.valor_causa,
      objeto: form.objeto,
    };

    setSaving(true);
    try {
      await api.post("/processos/", payload);
      toast.success("Processo criado");
      setShowModal(false);
      fetchProcessos();
    } catch (err) {
      const msg = err.response?.data ? JSON.stringify(err.response.data).slice(0, 180) : "Erro ao criar processo";
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h1 className="text-2xl font-bold text-gray-900">Processos</h1>
        <div className="flex gap-2">
          <button onClick={() => navigate("/documentos")} className="btn-secondary">Documentos</button>
          <button onClick={openModal} className="btn-primary">+ Novo Processo</button>
        </div>
      </div>

      <div className="flex gap-3 flex-wrap">
        <input
          className="input max-w-sm"
          placeholder="Buscar número, cliente ou objeto..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="input max-w-xs" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">Todos os status</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      <div className="table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th className="th">Número</th>
              <th className="th">Cliente</th>
              <th className="th">Tipo</th>
              <th className="th">Caso</th>
              <th className="th">Status</th>
              <th className="th">Valor</th>
              <th className="th">Ações</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="td text-center text-gray-400 py-8">Carregando...</td>
              </tr>
            ) : processos.length === 0 ? (
              <tr>
                <td colSpan={7} className="td text-center text-gray-400 py-8">Nenhum processo encontrado</td>
              </tr>
            ) : (
              processos.map((p) => (
                <tr key={p.id} className="tr-hover">
                  <td className="td">
                    <Link to={`/processos/${p.id}`} className="text-primary-700 hover:text-primary-900 font-mono text-xs font-semibold">
                      {p.numero}
                    </Link>
                  </td>
                  <td className="td font-medium">{p.cliente_nome || "-"}</td>
                  <td className="td text-xs">{p.tipo_nome || "-"}</td>
                  <td className="td text-xs">{p.tipo_caso_display || TIPO_CASO_LABELS[p.tipo_caso] || "-"}</td>
                  <td className="td">
                    <span className={STATUS_BADGE[p.status] || "badge-gray"}>
                      {p.status_display || STATUS_LABELS[p.status] || p.status}
                    </span>
                    {p.segredo_justica && (
                      <span className="badge-red ml-2">Segredo de Justiça</span>
                    )}
                  </td>
                  <td className="td text-xs">{formatMoney(p.valor_causa)}</td>
                  <td className="td">
                    <Link to={`/processos/${p.id}`} className="text-primary-600 hover:text-primary-800 text-xs font-medium">
                      Abrir
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-lg font-semibold">Novo Processo</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>

            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Número do Processo *</label>
                  <input
                    className="input"
                    required
                    placeholder="0000000-00.0000.0.00.0000"
                    value={form.numero}
                    onChange={(e) => setForm({ ...form, numero: e.target.value })}
                  />
                </div>

                <div>
                  <label className="label">Status</label>
                  <select className="input" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                    {Object.entries(STATUS_LABELS).map(([k, v]) => (
                      <option key={k} value={k}>{v}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="label">Sigilo</label>
                  <label className="inline-flex items-center gap-2 text-sm text-gray-700 mt-2">
                    <input
                      type="checkbox"
                      checked={!!form.segredo_justica}
                      onChange={(e) => setForm({ ...form, segredo_justica: e.target.checked })}
                    />
                    Segredo de Justiça
                  </label>
                </div>

                <div>
                  <label className="label">Cliente *</label>
                  <select className="input" required value={form.cliente} onChange={(e) => setForm({ ...form, cliente: e.target.value })}>
                    <option value="">Selecione...</option>
                    {clientes.map((c) => (
                      <option key={c.id} value={c.id}>{c.nome}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="label">Tipo de Processo *</label>
                  <select className="input" required value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}>
                    <option value="">Selecione...</option>
                    {tipos.map((t) => (
                      <option key={t.id} value={t.id}>{t.nome}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="label">Vara</label>
                  <select className="input" value={form.vara} onChange={(e) => setForm({ ...form, vara: e.target.value })}>
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
                    value={form.valor_causa}
                    onChange={(e) => setForm({ ...form, valor_causa: e.target.value })}
                  />
                </div>

                <div>
                  <label className="label">Tipo de Caso</label>
                  <select className="input" value={form.tipo_caso} onChange={(e) => setForm({ ...form, tipo_caso: e.target.value })}>
                    {Object.entries(TIPO_CASO_LABELS).map(([k, v]) => (
                      <option key={k} value={k}>{v}</option>
                    ))}
                  </select>
                </div>

                <div className="md:col-span-2">
                  <label className="label">Objeto / Descrição *</label>
                  <textarea
                    className="input"
                    rows={3}
                    required
                    value={form.objeto}
                    onChange={(e) => setForm({ ...form, objeto: e.target.value })}
                  />
                </div>
              </div>

              <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-xs text-blue-700">
                Upload de documentos foi centralizado na área <strong>Documentos</strong>.
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
                <button type="submit" className="btn-primary" disabled={saving}>
                  {saving ? "Criando..." : "Criar Processo"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
