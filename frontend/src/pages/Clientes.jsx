import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api/axios";
import toast from "react-hot-toast";
import useDebouncedValue from "../hooks/useDebouncedValue";

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

function toList(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.results || [];
}

function TipoBadge({ tipo, label }) {
  return (
    <span className={tipo === "pj" ? "badge-blue" : "badge-green"}>
      {label || (tipo === "pj" ? "Pessoa Jurídica" : "Pessoa Física")}
    </span>
  );
}

export default function Clientes() {
  const navigate = useNavigate();
  const [clientes, setClientes] = useState([]);
  const [tiposProcesso, setTiposProcesso] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 350);
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const fetchClientes = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (debouncedSearch.trim()) params.set("search", debouncedSearch.trim());
    params.set("limit", "200");

    api
      .get(`/clientes/?${params.toString()}`)
      .then((r) => setClientes(toList(r.data)))
      .catch(() => toast.error("Erro ao carregar clientes"))
      .finally(() => setLoading(false));
  }, [debouncedSearch]);

  useEffect(() => {
    fetchClientes();
  }, [fetchClientes]);

  useEffect(() => {
    api
      .get("/tipos-processo/?limit=300")
      .then((r) => setTiposProcesso(toList(r.data)))
      .catch(() => setTiposProcesso([]));
  }, []);

  function openCreate() {
    setEditItem(null);
    setForm(EMPTY_FORM);
    setShowModal(true);
  }

  function openEdit(cliente) {
    setEditItem(cliente);
    setForm({
      nome: cliente.nome || "",
      tipo: cliente.tipo || "pf",
      cpf_cnpj: cliente.cpf_cnpj || "",
      email: cliente.email || "",
      telefone: cliente.telefone || "",
      endereco: cliente.endereco || "",
      demanda: cliente.demanda || "",
      processos_possiveis: Array.isArray(cliente.processos_possiveis)
        ? cliente.processos_possiveis
        : [],
      observacoes: cliente.observacoes || "",
    });
    setShowModal(true);
  }

  function setField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      if (editItem) {
        await api.patch(`/clientes/${editItem.id}/`, form);
        toast.success("Cliente atualizado");
      } else {
        await api.post("/clientes/", form);
        toast.success("Cliente criado");
      }
      setShowModal(false);
      fetchClientes();
    } catch (err) {
      const data = err.response?.data;
      const msg = data ? JSON.stringify(data).slice(0, 180) : "Erro ao salvar cliente";
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(cliente) {
    if (!confirm(`Excluir o cliente \"${cliente.nome}\"?`)) return;
    try {
      await api.delete(`/clientes/${cliente.id}/`);
      toast.success("Cliente excluído");
      fetchClientes();
    } catch {
      toast.error("Não foi possível excluir este cliente");
    }
  }

  async function handleInativar(cliente) {
    if (!cliente.ativo) {
      toast("Cliente já está inativo");
      return;
    }
    if (!confirm(`Inativar o cliente \"${cliente.nome}\"?`)) return;

    try {
      await api.post(`/clientes/${cliente.id}/inativar/`);
      toast.success("Cliente inativado");
      fetchClientes();
    } catch {
      toast.error("Erro ao inativar cliente");
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h1 className="text-2xl font-bold text-gray-900">Clientes</h1>
        <div className="flex gap-2">
          <button onClick={() => navigate("/documentos")} className="btn-secondary">Documentos</button>
          <button onClick={openCreate} className="btn-primary">+ Novo Cliente</button>
        </div>
      </div>

      <input
        className="input max-w-sm"
        placeholder="Buscar por nome, CPF/CNPJ, e-mail..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th className="th">Cliente</th>
              <th className="th">Tipo</th>
              <th className="th">Status</th>
              <th className="th">Contato</th>
              <th className="th">Demanda</th>
              <th className="th">Ações</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="td text-center text-gray-400 py-8">Carregando...</td>
              </tr>
            ) : clientes.length === 0 ? (
              <tr>
                <td colSpan={6} className="td text-center text-gray-400 py-8">Nenhum cliente encontrado</td>
              </tr>
            ) : (
              clientes.map((c) => (
                <tr key={c.id} className="tr-hover">
                  <td className="td">
                    <Link to={`/clientes/${c.id}`} className="text-primary-700 hover:text-primary-900 font-semibold">
                      {c.nome}
                    </Link>
                    <div className="text-xs text-gray-500 font-mono">{c.cpf_cnpj || "-"}</div>
                  </td>
                  <td className="td"><TipoBadge tipo={c.tipo} label={c.tipo_display} /></td>
                  <td className="td">
                    <span className={c.ativo ? "badge-green" : "badge-gray"}>
                      {c.ativo ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  <td className="td text-xs">
                    <div>{c.telefone || "-"}</div>
                    <div className="text-gray-500">{c.email || "-"}</div>
                  </td>
                  <td className="td text-xs max-w-[320px] truncate" title={c.demanda || ""}>
                    {c.demanda || "-"}
                  </td>
                  <td className="td">
                    <div className="flex flex-wrap gap-2">
                      <Link to={`/clientes/${c.id}`} className="text-primary-600 hover:text-primary-800 text-xs font-medium">
                        Abrir
                      </Link>
                      <button
                        onClick={() => openEdit(c)}
                        className="text-primary-600 hover:text-primary-800 text-xs font-medium"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => handleDelete(c)}
                        className="text-red-600 hover:text-red-800 text-xs font-medium"
                      >
                        Excluir
                      </button>
                      <button
                        onClick={() => handleInativar(c)}
                        className="text-amber-700 hover:text-amber-900 text-xs font-medium"
                      >
                        Inativar
                      </button>
                    </div>
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
            <div className="p-6 border-b flex justify-between items-center">
              <h2 className="text-lg font-semibold">{editItem ? "Editar Cliente" : "Novo Cliente"}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
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
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
                <button type="submit" className="btn-primary" disabled={saving}>
                  {saving ? "Salvando..." : editItem ? "Salvar" : "Criar Cliente"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
