import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";
import toast from "react-hot-toast";

const STATUS_LABELS = { em_andamento:"Em Andamento", suspenso:"Suspenso", finalizado:"Finalizado", arquivado:"Arquivado" };
const STATUS_BADGE  = { em_andamento:"badge-blue", suspenso:"badge-yellow", finalizado:"badge-green", arquivado:"badge-gray" };
const POLO_LABELS   = { ativo:"Ativo (autor)", passivo:"Passivo (réu)", terceiro:"Terceiro" };

const EMPTY_FORM = { numero:"", cliente:"", tipo_processo:"", polo:"ativo", status:"em_andamento", parte_contraria:"", valor_causa:"", descricao:"" };

export default function Processos() {
  const navigate = useNavigate();
  const [processos, setProcessos]       = useState([]);
  const [loading, setLoading]           = useState(true);
  const [search, setSearch]             = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [showModal, setShowModal]       = useState(false);
  const [clientes, setClientes]         = useState([]);
  const [tipos, setTipos]               = useState([]);
  const [varas, setVaras]               = useState([]);
  const [form, setForm]                 = useState(EMPTY_FORM);
  const [clienteSearch, setClienteSearch] = useState("");
  const [showClienteList, setShowClienteList] = useState(false);
  const [clienteSelecionado, setClienteSelecionado] = useState(null);

  const fetchProcessos = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (filterStatus) params.set("status", filterStatus);
    api.get(`/processos/?${params}`)
      .then((r) => setProcessos(r.data?.results || r.data || []))
      .catch(() => toast.error("Erro ao carregar processos"))
      .finally(() => setLoading(false));
  }, [search, filterStatus]);

  useEffect(() => { fetchProcessos(); }, [fetchProcessos]);

  useEffect(() => {
    if (showModal) {
      Promise.all([
        api.get("/clientes/?limit=500").catch(() => ({ data: [] })),
        api.get("/tipos-processo/").catch(() => ({ data: [] })),
        api.get("/varas/").catch(() => ({ data: [] })),
      ]).then(([c, t, v]) => {
        setClientes(c.data?.results || c.data || []);
        setTipos(t.data?.results || t.data || []);
        setVaras(v.data?.results || v.data || []);
      });
    }
  }, [showModal]);

  function openModal() {
    setForm(EMPTY_FORM);
    setClienteSearch("");
    setClienteSelecionado(null);
    setShowModal(true);
  }

  function selecionarCliente(c) {
    setClienteSelecionado(c);
    setForm((f) => ({ ...f, cliente: c.id }));
    setClienteSearch(c.nome);
    setShowClienteList(false);
  }

  const clientesFiltrados = clientes.filter((c) =>
    c.nome.toLowerCase().includes(clienteSearch.toLowerCase()) ||
    (c.cpf_cnpj || "").includes(clienteSearch)
  );

  async function handleCreate(e) {
    e.preventDefault();
    if (!form.cliente) { toast.error("Selecione um cliente"); return; }
    try {
      await api.post("/processos/", form);
      toast.success("Processo criado!");
      setShowModal(false);
      fetchProcessos();
    } catch (err) {
      const msg = err.response?.data ? JSON.stringify(err.response.data).slice(0, 140) : "Erro ao criar processo";
      toast.error(msg);
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">⚖️ Processos</h1>
        <div className="flex gap-2">
          <button onClick={() => navigate("/documentos")} className="btn-secondary">Documentos</button>
          <button onClick={openModal} className="btn-primary gap-2">+ Novo Processo</button>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex gap-3 flex-wrap">
        <input
          className="input max-w-xs"
          placeholder="Buscar número, cliente..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="input max-w-xs" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">Todos os status</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>

      {/* Tabela */}
      <div className="table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th className="th">Número</th>
              <th className="th">Cliente</th>
              <th className="th">Tipo</th>
              <th className="th">Polo</th>
              <th className="th">Status</th>
              <th className="th">Valor</th>
              <th className="th">Ações</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="td text-center text-gray-400 py-8">Carregando...</td></tr>
            ) : processos.length === 0 ? (
              <tr><td colSpan={7} className="td text-center text-gray-400 py-8">Nenhum processo encontrado</td></tr>
            ) : processos.map((p) => (
              <tr key={p.id} className="tr-hover">
                <td className="td font-mono text-xs">{p.numero}</td>
                <td className="td font-medium">{p.cliente_nome || p.cliente}</td>
                <td className="td text-xs">{p.tipo_nome || p.tipo_processo_nome || p.tipo_processo}</td>
                <td className="td text-xs">{POLO_LABELS[p.polo] || p.polo}</td>
                <td className="td"><span className={STATUS_BADGE[p.status] || "badge-gray"}>{STATUS_LABELS[p.status] || p.status}</span></td>
                <td className="td text-xs">{p.valor_causa ? `R$ ${Number(p.valor_causa).toLocaleString("pt-BR")}` : "—"}</td>
                <td className="td">
                  <button onClick={() => navigate(`/processos/${p.id}`)} className="text-primary-600 hover:text-primary-800 text-xs font-medium">
                    Ver →
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal Novo Processo */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-lg font-semibold">Novo Processo</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">

                {/* Número */}
                <div>
                  <label className="label">Número do Processo *</label>
                  <input className="input" required placeholder="0000000-00.0000.0.00.0000"
                    value={form.numero} onChange={(e) => setForm({ ...form, numero: e.target.value })} />
                </div>

                {/* Cliente com busca */}
                <div className="relative">
                  <label className="label">Cliente *</label>
                  <input
                    className="input"
                    placeholder="Digite para buscar cliente..."
                    value={clienteSearch}
                    autoComplete="off"
                    onChange={(e) => {
                      setClienteSearch(e.target.value);
                      setForm((f) => ({ ...f, cliente: "" }));
                      setClienteSelecionado(null);
                      setShowClienteList(true);
                    }}
                    onFocus={() => setShowClienteList(true)}
                  />
                  {clienteSelecionado && (
                    <div className="mt-1 text-xs text-green-700 font-medium flex items-center gap-1">
                      <span>✓</span>
                      <span>{clienteSelecionado.nome}</span>
                      {clienteSelecionado.cpf_cnpj && <span className="text-gray-400">— {clienteSelecionado.cpf_cnpj}</span>}
                    </div>
                  )}
                  {showClienteList && clienteSearch.length > 0 && clientesFiltrados.length > 0 && (
                    <ul className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto text-sm">
                      {clientesFiltrados.slice(0, 10).map((c) => (
                        <li
                          key={c.id}
                          className="px-3 py-2 hover:bg-primary-50 cursor-pointer flex justify-between"
                          onMouseDown={() => selecionarCliente(c)}
                        >
                          <span className="font-medium">{c.nome}</span>
                          <span className="text-gray-400 text-xs">{c.cpf_cnpj || c.tipo_pessoa}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {showClienteList && clienteSearch.length > 0 && clientesFiltrados.length === 0 && (
                    <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm text-gray-400">
                      Nenhum cliente encontrado
                    </div>
                  )}
                </div>

                {/* Tipo de Processo */}
                <div>
                  <label className="label">Tipo de Processo *</label>
                  <select className="input" required value={form.tipo_processo}
                    onChange={(e) => setForm({ ...form, tipo_processo: e.target.value })}>
                    <option value="">Selecione o tipo...</option>
                    {tipos.map((t) => (
                      <option key={t.id} value={t.id}>{t.nome}</option>
                    ))}
                  </select>
                </div>

                {/* Polo */}
                <div>
                  <label className="label">Polo</label>
                  <select className="input" value={form.polo}
                    onChange={(e) => setForm({ ...form, polo: e.target.value })}>
                    {Object.entries(POLO_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>

                {/* Parte contrária */}
                <div>
                  <label className="label">Parte Contrária</label>
                  <input className="input" value={form.parte_contraria}
                    onChange={(e) => setForm({ ...form, parte_contraria: e.target.value })} />
                </div>

                {/* Valor da causa */}
                <div>
                  <label className="label">Valor da Causa (R$)</label>
                  <input className="input" type="number" step="0.01" value={form.valor_causa}
                    onChange={(e) => setForm({ ...form, valor_causa: e.target.value })} />
                </div>
              </div>

              {/* Descrição */}
              <div>
                <label className="label">Descrição / Resumo</label>
                <textarea className="input" rows={3} value={form.descricao}
                  onChange={(e) => setForm({ ...form, descricao: e.target.value })} />
              </div>

              <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-xs text-blue-700">
                Upload de documentos foi centralizado na área <strong>Documentos</strong>.
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
                <button type="submit" className="btn-primary">Criar Processo</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
