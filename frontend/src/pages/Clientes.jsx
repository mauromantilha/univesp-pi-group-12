import { useState, useEffect, useCallback } from "react";
import api from "../api/axios";
import toast from "react-hot-toast";

export default function Clientes() {
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [form, setForm] = useState({ nome:"", tipo_pessoa:"fisica", cpf_cnpj:"", email:"", telefone:"", cidade:"", estado:"", observacoes:"" });

  const fetch = useCallback(() => {
    setLoading(true);
    const params = search ? `?search=${search}` : "";
    api.get(`/clientes/${params}`).then((r) => setClientes(r.data?.results || r.data || [])).finally(() => setLoading(false));
  }, [search]);

  useEffect(() => { fetch(); }, [fetch]);

  function openCreate() { setEditItem(null); setForm({ nome:"", tipo_pessoa:"fisica", cpf_cnpj:"", email:"", telefone:"", cidade:"", estado:"", observacoes:"" }); setShowModal(true); }
  function openEdit(c) { setEditItem(c); setForm({ nome:c.nome, tipo_pessoa:c.tipo_pessoa, cpf_cnpj:c.cpf_cnpj||"", email:c.email||"", telefone:c.telefone||"", cidade:c.cidade||"", estado:c.estado||"", observacoes:c.observacoes||"" }); setShowModal(true); }

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      if (editItem) {
        await api.patch(`/clientes/${editItem.id}/`, form);
        toast.success("Cliente atualizado!");
      } else {
        await api.post("/clientes/", form);
        toast.success("Cliente criado!");
      }
      setShowModal(false);
      fetch();
    } catch (err) {
      toast.error(err.response?.data ? JSON.stringify(err.response.data).slice(0,120) : "Erro ao salvar");
    }
  }

  async function handleDelete(id) {
    if (!confirm("Excluir este cliente?")) return;
    try {
      await api.delete(`/clientes/${id}/`);
      toast.success("Cliente removido!");
      fetch();
    } catch { toast.error("Não foi possível excluir (pode ter processos vinculados)"); }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">👥 Clientes</h1>
        <button onClick={openCreate} className="btn-primary">+ Novo Cliente</button>
      </div>
      <input className="input max-w-xs" placeholder="Buscar por nome, CPF/CNPJ..." value={search} onChange={(e) => setSearch(e.target.value)} />
      <div className="table-wrapper">
        <table className="table">
          <thead><tr>
            <th className="th">Nome</th><th className="th">Tipo</th><th className="th">CPF/CNPJ</th>
            <th className="th">Email</th><th className="th">Telefone</th><th className="th">Cidade/UF</th><th className="th">Ações</th>
          </tr></thead>
          <tbody>
            {loading ? <tr><td colSpan={7} className="td text-center text-gray-400 py-8">Carregando...</td></tr>
            : clientes.length === 0 ? <tr><td colSpan={7} className="td text-center text-gray-400 py-8">Nenhum cliente encontrado</td></tr>
            : clientes.map((c) => (
              <tr key={c.id} className="tr-hover">
                <td className="td font-medium">{c.nome}</td>
                <td className="td"><span className={c.tipo_pessoa === "juridica" ? "badge-blue" : "badge-green"}>{c.tipo_pessoa === "juridica" ? "Jurídica" : "Física"}</span></td>
                <td className="td text-xs font-mono">{c.cpf_cnpj || "—"}</td>
                <td className="td text-xs">{c.email || "—"}</td>
                <td className="td text-xs">{c.telefone || "—"}</td>
                <td className="td text-xs">{c.cidade ? `${c.cidade}/${c.estado}` : "—"}</td>
                <td className="td">
                  <div className="flex gap-2">
                    <button onClick={() => openEdit(c)} className="text-primary-600 hover:text-primary-800 text-xs font-medium">Editar</button>
                    <button onClick={() => handleDelete(c.id)} className="text-red-500 hover:text-red-700 text-xs font-medium">Excluir</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-screen overflow-y-auto">
            <div className="p-6 border-b flex justify-between items-center">
              <h2 className="text-lg font-semibold">{editItem ? "Editar Cliente" : "Novo Cliente"}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2"><label className="label">Nome *</label><input className="input" required value={form.nome} onChange={(e) => setForm({...form, nome: e.target.value})} /></div>
                <div><label className="label">Tipo</label><select className="input" value={form.tipo_pessoa} onChange={(e) => setForm({...form, tipo_pessoa: e.target.value})}><option value="fisica">Pessoa Física</option><option value="juridica">Pessoa Jurídica</option></select></div>
                <div><label className="label">CPF/CNPJ</label><input className="input" value={form.cpf_cnpj} onChange={(e) => setForm({...form, cpf_cnpj: e.target.value})} /></div>
                <div><label className="label">Email</label><input className="input" type="email" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} /></div>
                <div><label className="label">Telefone</label><input className="input" value={form.telefone} onChange={(e) => setForm({...form, telefone: e.target.value})} /></div>
                <div><label className="label">Cidade</label><input className="input" value={form.cidade} onChange={(e) => setForm({...form, cidade: e.target.value})} /></div>
                <div><label className="label">Estado (UF)</label><input className="input" maxLength={2} value={form.estado} onChange={(e) => setForm({...form, estado: e.target.value.toUpperCase()})} /></div>
                <div className="col-span-2"><label className="label">Observações</label><textarea className="input" rows={2} value={form.observacoes} onChange={(e) => setForm({...form, observacoes: e.target.value})} /></div>
              </div>
              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
                <button type="submit" className="btn-primary">{editItem ? "Salvar" : "Criar"}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
