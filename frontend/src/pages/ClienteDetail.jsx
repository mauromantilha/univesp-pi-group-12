import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../api/axios";
import toast from "react-hot-toast";

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

export default function ClienteDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [cliente, setCliente] = useState(null);
  const [processos, setProcessos] = useState([]);
  const [tiposProcesso, setTiposProcesso] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);

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
  }

  async function carregarProcessos() {
    const res = await api.get(`/processos/?cliente=${id}&limit=300`);
    setProcessos(toList(res.data));
  }

  useEffect(() => {
    setLoading(true);
    Promise.all([
      carregarCliente(),
      carregarProcessos(),
      api.get("/tipos-processo/?limit=300").then((r) => setTiposProcesso(toList(r.data))).catch(() => setTiposProcesso([])),
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

  if (loading) {
    return <div className="text-center py-20 text-gray-400">Carregando...</div>;
  }

  if (!cliente) {
    return <div className="text-center py-20 text-gray-400">Cliente não encontrado.</div>;
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <button onClick={() => navigate("/clientes")} className="hover:text-primary-600">Clientes</button>
        <span>/</span>
        <span className="text-gray-800 font-medium truncate">{cliente.nome}</span>
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
