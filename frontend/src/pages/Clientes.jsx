import { useState, useEffect, useCallback } from "react";
import api from "../api/axios";
import toast from "react-hot-toast";

// Formata número para link WhatsApp (adiciona 55 se não tiver)
function waLink(tel) {
  if (!tel) return null;
  const digits = tel.replace(/\D/g, "");
  if (digits.length < 8) return null;
  const num = digits.startsWith("55") ? digits : `55${digits}`;
  return `https://wa.me/${num}`;
}

function WhatsAppBtn({ tel }) {
  const link = waLink(tel);
  if (!link) return <span className="text-xs text-gray-400">—</span>;
  return (
    <a
      href={link}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 text-xs text-green-600 hover:text-green-700 font-medium"
      title="Abrir no WhatsApp"
    >
      <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 fill-current shrink-0">
        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
      </svg>
      {tel}
    </a>
  );
}

const EMPTY_FORM = {
  nome: "", tipo_pessoa: "fisica", cpf_cnpj: "", rg: "",
  email: "", telefone: "", telefone2: "",
  cep: "", endereco: "", numero: "", complemento: "", bairro: "",
  cidade: "", estado: "", observacoes: "",
};

export default function Clientes() {
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [buscandoCep, setBuscandoCep] = useState(false);

  const fetchClientes = useCallback(() => {
    setLoading(true);
    const params = search ? `?search=${search}` : "";
    api
      .get(`/clientes/${params}`)
      .then((r) => setClientes(r.data?.results || r.data || []))
      .finally(() => setLoading(false));
  }, [search]);

  useEffect(() => { fetchClientes(); }, [fetchClientes]);

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })); }

  function openCreate() {
    setEditItem(null);
    setForm(EMPTY_FORM);
    setShowModal(true);
  }

  function openEdit(c) {
    setEditItem(c);
    setForm({
      nome: c.nome || "", tipo_pessoa: c.tipo_pessoa || "fisica",
      cpf_cnpj: c.cpf_cnpj || "", rg: c.rg || "",
      email: c.email || "", telefone: c.telefone || "", telefone2: c.telefone2 || "",
      cep: c.cep || "", endereco: c.endereco || "", numero: c.numero || "",
      complemento: c.complemento || "", bairro: c.bairro || "",
      cidade: c.cidade || "", estado: c.estado || "", observacoes: c.observacoes || "",
    });
    setShowModal(true);
  }

  async function buscarCep(cep) {
    const digits = cep.replace(/\D/g, "");
    if (digits.length !== 8) return;
    setBuscandoCep(true);
    try {
      const res = await fetch(`https://viacep.com.br/ws/${digits}/json/`);
      const data = await res.json();
      if (data.erro) { toast.error("CEP não encontrado"); return; }
      setForm((f) => ({
        ...f,
        endereco: data.logradouro || f.endereco,
        bairro: data.bairro || f.bairro,
        cidade: data.localidade || f.cidade,
        estado: data.uf || f.estado,
        cep: data.cep?.replace("-", "") || f.cep,
      }));
      toast.success("CEP encontrado!");
    } catch {
      toast.error("Erro ao buscar CEP");
    } finally {
      setBuscandoCep(false);
    }
  }

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
      fetchClientes();
    } catch (err) {
      toast.error(
        err.response?.data ? JSON.stringify(err.response.data).slice(0, 120) : "Erro ao salvar"
      );
    }
  }

  async function handleDelete(id) {
    if (!confirm("Excluir este cliente?")) return;
    try {
      await api.delete(`/clientes/${id}/`);
      toast.success("Cliente removido!");
      fetchClientes();
    } catch {
      toast.error("Não foi possível excluir (pode ter processos vinculados)");
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">👥 Clientes</h1>
        <button onClick={openCreate} className="btn-primary">+ Novo Cliente</button>
      </div>

      <input
        className="input max-w-xs"
        placeholder="Buscar por nome, CPF/CNPJ..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th className="th">Nome</th>
              <th className="th">Tipo</th>
              <th className="th">CPF/CNPJ</th>
              <th className="th">Email</th>
              <th className="th">Telefone</th>
              <th className="th">Cidade/UF</th>
              <th className="th">Ações</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="td text-center text-gray-400 py-8">Carregando...</td></tr>
            ) : clientes.length === 0 ? (
              <tr><td colSpan={7} className="td text-center text-gray-400 py-8">Nenhum cliente encontrado</td></tr>
            ) : (
              clientes.map((c) => (
                <tr key={c.id} className="tr-hover">
                  <td className="td font-medium">{c.nome}</td>
                  <td className="td">
                    <span className={c.tipo_pessoa === "juridica" ? "badge-blue" : "badge-green"}>
                      {c.tipo_pessoa === "juridica" ? "Jurídica" : "Física"}
                    </span>
                  </td>
                  <td className="td text-xs font-mono">{c.cpf_cnpj || "—"}</td>
                  <td className="td text-xs">
                    {c.email ? (
                      <a href={`mailto:${c.email}`} className="text-primary-600 hover:underline">
                        {c.email}
                      </a>
                    ) : "—"}
                  </td>
                  <td className="td">
                    <div className="flex flex-col gap-0.5">
                      <WhatsAppBtn tel={c.telefone} />
                      {c.telefone2 && <WhatsAppBtn tel={c.telefone2} />}
                    </div>
                  </td>
                  <td className="td text-xs">
                    {c.cidade ? `${c.cidade}/${c.estado}` : "—"}
                  </td>
                  <td className="td">
                    <div className="flex gap-2">
                      <button
                        onClick={() => openEdit(c)}
                        className="text-primary-600 hover:text-primary-800 text-xs font-medium"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => handleDelete(c.id)}
                        className="text-red-500 hover:text-red-700 text-xs font-medium"
                      >
                        Excluir
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-screen overflow-y-auto">
            <div className="p-6 border-b flex justify-between items-center">
              <h2 className="text-lg font-semibold">
                {editItem ? "Editar Cliente" : "Novo Cliente"}
              </h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-5">
              {/* Dados pessoais */}
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Dados Pessoais</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <label className="label">Nome *</label>
                    <input className="input" required value={form.nome} onChange={(e) => set("nome", e.target.value)} />
                  </div>
                  <div>
                    <label className="label">Tipo</label>
                    <select className="input" value={form.tipo_pessoa} onChange={(e) => set("tipo_pessoa", e.target.value)}>
                      <option value="fisica">Pessoa Física</option>
                      <option value="juridica">Pessoa Jurídica</option>
                    </select>
                  </div>
                  <div>
                    <label className="label">CPF / CNPJ</label>
                    <input className="input" value={form.cpf_cnpj} onChange={(e) => set("cpf_cnpj", e.target.value)} />
                  </div>
                  <div>
                    <label className="label">RG</label>
                    <input className="input" value={form.rg} onChange={(e) => set("rg", e.target.value)} />
                  </div>
                  <div>
                    <label className="label">Email</label>
                    <input className="input" type="email" value={form.email} onChange={(e) => set("email", e.target.value)} />
                  </div>
                  <div>
                    <label className="label">Telefone / WhatsApp</label>
                    <div className="flex items-center gap-2">
                      <input className="input flex-1" value={form.telefone} onChange={(e) => set("telefone", e.target.value)} placeholder="(99) 99999-9999" />
                      {waLink(form.telefone) && (
                        <a href={waLink(form.telefone)} target="_blank" rel="noopener noreferrer"
                          className="shrink-0 bg-green-500 hover:bg-green-600 text-white rounded-lg px-2 py-2 transition-colors"
                          title="Testar WhatsApp">
                          <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current">
                            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
                          </svg>
                        </a>
                      )}
                    </div>
                  </div>
                  <div>
                    <label className="label">Telefone 2</label>
                    <div className="flex items-center gap-2">
                      <input className="input flex-1" value={form.telefone2} onChange={(e) => set("telefone2", e.target.value)} placeholder="(99) 99999-9999" />
                      {waLink(form.telefone2) && (
                        <a href={waLink(form.telefone2)} target="_blank" rel="noopener noreferrer"
                          className="shrink-0 bg-green-500 hover:bg-green-600 text-white rounded-lg px-2 py-2 transition-colors"
                          title="Testar WhatsApp">
                          <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current">
                            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
                          </svg>
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Endereço */}
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Endereço</h3>
                <div className="grid grid-cols-2 gap-4">
                  {/* CEP com busca */}
                  <div>
                    <label className="label">CEP</label>
                    <div className="flex gap-2">
                      <input
                        className="input flex-1"
                        value={form.cep}
                        onChange={(e) => set("cep", e.target.value)}
                        placeholder="00000-000"
                        maxLength={9}
                      />
                      <button
                        type="button"
                        onClick={() => buscarCep(form.cep)}
                        disabled={buscandoCep}
                        className="btn-secondary text-xs px-3 shrink-0"
                      >
                        {buscandoCep ? "..." : "Buscar"}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="label">Bairro</label>
                    <input className="input" value={form.bairro} onChange={(e) => set("bairro", e.target.value)} />
                  </div>

                  <div className="col-span-2">
                    <label className="label">Logradouro (Rua/Av.)</label>
                    <input className="input" value={form.endereco} onChange={(e) => set("endereco", e.target.value)} placeholder="Rua, Avenida, etc." />
                  </div>

                  <div>
                    <label className="label">Número</label>
                    <input className="input" value={form.numero} onChange={(e) => set("numero", e.target.value)} placeholder="ex: 123" />
                  </div>

                  <div>
                    <label className="label">Complemento</label>
                    <input className="input" value={form.complemento} onChange={(e) => set("complemento", e.target.value)} placeholder="Apto, Sala, Bloco..." />
                  </div>

                  <div>
                    <label className="label">Cidade</label>
                    <input className="input" value={form.cidade} onChange={(e) => set("cidade", e.target.value)} />
                  </div>

                  <div>
                    <label className="label">Estado (UF)</label>
                    <input className="input" maxLength={2} value={form.estado} onChange={(e) => set("estado", e.target.value.toUpperCase())} />
                  </div>
                </div>
              </div>

              {/* Observações */}
              <div>
                <label className="label">Observações</label>
                <textarea className="input" rows={2} value={form.observacoes} onChange={(e) => set("observacoes", e.target.value)} />
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">
                  Cancelar
                </button>
                <button type="submit" className="btn-primary">
                  {editItem ? "Salvar" : "Criar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
