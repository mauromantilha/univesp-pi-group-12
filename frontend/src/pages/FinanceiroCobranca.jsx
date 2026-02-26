import { useCallback, useEffect, useMemo, useState } from "react";
import api from "../api/axios";
import toast from "react-hot-toast";

function toList(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.results || [];
}

function fmtBRL(v) {
  return Number(v || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function fmtDate(v) {
  if (!v) return "-";
  try {
    return new Date(v).toLocaleDateString("pt-BR");
  } catch {
    return v;
  }
}

const STATUS_FATURA = {
  rascunho: "badge-gray",
  enviada: "badge-blue",
  paga: "badge-green",
  vencida: "badge-yellow",
  cancelada: "badge-red",
};

export default function FinanceiroCobranca() {
  const [loading, setLoading] = useState(true);
  const [clientes, setClientes] = useState([]);
  const [processos, setProcessos] = useState([]);
  const [regras, setRegras] = useState([]);
  const [apontamentos, setApontamentos] = useState([]);
  const [faturas, setFaturas] = useState([]);
  const [resumo, setResumo] = useState({ total_horas: 0, total_minutos: 0 });

  const [regraForm, setRegraForm] = useState({
    cliente: "",
    processo: "",
    titulo: "",
    tipo_cobranca: "hora",
    valor_hora: "",
    percentual_exito: "",
    valor_pacote: "",
    valor_recorrente: "",
    dia_vencimento_recorrencia: "",
    observacoes: "",
  });

  const [apForm, setApForm] = useState({
    cliente: "",
    processo: "",
    regra_cobranca: "",
    data: new Date().toISOString().slice(0, 10),
    descricao: "",
    minutos: "60",
    valor_hora: "",
  });

  const [faturaForm, setFaturaForm] = useState({
    cliente: "",
    processo: "",
    regra_cobranca: "",
    periodo_inicio: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().slice(0, 10),
    periodo_fim: new Date().toISOString().slice(0, 10),
    data_vencimento: "",
    incluir_despesas_reembolsaveis: true,
    valor_base_exito: "",
    adicional_valor: "",
    adicional_descricao: "",
  });

  const regrasCliente = useMemo(() => {
    if (!faturaForm.cliente) return regras;
    return regras.filter((r) => String(r.cliente) === String(faturaForm.cliente));
  }, [regras, faturaForm.cliente]);

  const processosCliente = useMemo(() => {
    if (!faturaForm.cliente) return processos;
    return processos.filter((p) => String(p.cliente) === String(faturaForm.cliente));
  }, [processos, faturaForm.cliente]);

  const fetchTudo = useCallback(() => {
    setLoading(true);
    Promise.all([
      api.get("/clientes/?limit=500").catch(() => ({ data: [] })),
      api.get("/processos/?limit=500").catch(() => ({ data: [] })),
      api.get("/financeiro/regras-cobranca/?limit=300").catch(() => ({ data: [] })),
      api.get("/financeiro/apontamentos-tempo/?limit=300").catch(() => ({ data: [] })),
      api.get("/financeiro/apontamentos-tempo/resumo/?faturado=false").catch(() => ({ data: {} })),
      api.get("/financeiro/faturas/?limit=200").catch(() => ({ data: [] })),
    ])
      .then(([c, p, r, a, rs, f]) => {
        setClientes(toList(c.data));
        setProcessos(toList(p.data));
        setRegras(toList(r.data));
        setApontamentos(toList(a.data));
        setResumo(rs.data || { total_horas: 0, total_minutos: 0 });
        setFaturas(toList(f.data));
      })
      .catch(() => toast.error("Erro ao carregar cobrança e time tracking"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchTudo();
  }, [fetchTudo]);

  async function criarRegra(e) {
    e.preventDefault();
    if (!regraForm.cliente || !regraForm.titulo) {
      toast.error("Cliente e título são obrigatórios");
      return;
    }
    try {
      await api.post("/financeiro/regras-cobranca/", {
        ...regraForm,
        processo: regraForm.processo || null,
        valor_hora: regraForm.valor_hora || null,
        percentual_exito: regraForm.percentual_exito || null,
        valor_pacote: regraForm.valor_pacote || null,
        valor_recorrente: regraForm.valor_recorrente || null,
        dia_vencimento_recorrencia: regraForm.dia_vencimento_recorrencia || null,
      });
      toast.success("Regra de cobrança criada");
      setRegraForm({
        cliente: "",
        processo: "",
        titulo: "",
        tipo_cobranca: "hora",
        valor_hora: "",
        percentual_exito: "",
        valor_pacote: "",
        valor_recorrente: "",
        dia_vencimento_recorrencia: "",
        observacoes: "",
      });
      fetchTudo();
    } catch (err) {
      toast.error(err.response?.data ? JSON.stringify(err.response.data).slice(0, 180) : "Erro ao criar regra");
    }
  }

  async function criarApontamento(e) {
    e.preventDefault();
    if (!apForm.cliente || !apForm.descricao || !apForm.minutos) {
      toast.error("Preencha cliente, descrição e minutos");
      return;
    }
    try {
      await api.post("/financeiro/apontamentos-tempo/", {
        ...apForm,
        processo: apForm.processo || null,
        regra_cobranca: apForm.regra_cobranca || null,
        valor_hora: apForm.valor_hora || null,
        minutos: Number(apForm.minutos || 0),
      });
      toast.success("Apontamento registrado");
      setApForm((prev) => ({ ...prev, descricao: "", minutos: "60", valor_hora: "" }));
      fetchTudo();
    } catch (err) {
      toast.error(err.response?.data ? JSON.stringify(err.response.data).slice(0, 180) : "Erro ao registrar apontamento");
    }
  }

  async function gerarFatura(e) {
    e.preventDefault();
    if (!faturaForm.cliente) {
      toast.error("Selecione o cliente da fatura");
      return;
    }
    try {
      await api.post("/financeiro/faturas/gerar/", {
        ...faturaForm,
        processo: faturaForm.processo || null,
        regra_cobranca: faturaForm.regra_cobranca || null,
        data_vencimento: faturaForm.data_vencimento || null,
        valor_base_exito: faturaForm.valor_base_exito || null,
        adicional_valor: faturaForm.adicional_valor || null,
      });
      toast.success("Fatura gerada");
      fetchTudo();
    } catch (err) {
      toast.error(err.response?.data ? JSON.stringify(err.response.data).slice(0, 220) : "Erro ao gerar fatura");
    }
  }

  async function acaoFatura(id, acao, payload = {}) {
    try {
      await api.post(`/financeiro/faturas/${id}/${acao}/`, payload);
      toast.success("Fatura atualizada");
      fetchTudo();
    } catch (err) {
      toast.error(err.response?.data ? JSON.stringify(err.response.data).slice(0, 180) : "Erro na ação da fatura");
    }
  }

  if (loading) return <div className="text-gray-400 py-16 text-center">Carregando módulo de cobrança...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🧾 Gestão de Cobrança e Faturamento</h1>
          <p className="text-sm text-gray-500 mt-1">Regras de cobrança, apontamentos de tempo, faturas e recebimento online.</p>
        </div>
        <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-700">
          Horas não faturadas: <strong>{Number(resumo.total_horas || 0).toFixed(2)}h</strong>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="card space-y-3">
          <h2 className="text-base font-semibold">Regras de Cobrança</h2>
          <form className="space-y-3" onSubmit={criarRegra}>
            <select className="input" value={regraForm.cliente} onChange={(e) => setRegraForm({ ...regraForm, cliente: e.target.value })}>
              <option value="">Cliente*</option>
              {clientes.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
            </select>
            <select className="input" value={regraForm.processo} onChange={(e) => setRegraForm({ ...regraForm, processo: e.target.value })}>
              <option value="">Processo (opcional)</option>
              {processos.map((p) => <option key={p.id} value={p.id}>{p.numero} - {p.cliente_nome}</option>)}
            </select>
            <input className="input" placeholder="Título da regra*" value={regraForm.titulo} onChange={(e) => setRegraForm({ ...regraForm, titulo: e.target.value })} />
            <select className="input" value={regraForm.tipo_cobranca} onChange={(e) => setRegraForm({ ...regraForm, tipo_cobranca: e.target.value })}>
              <option value="hora">Hora</option>
              <option value="exito">Êxito</option>
              <option value="pacote">Pacote</option>
              <option value="recorrencia">Recorrência</option>
            </select>
            <div className="grid grid-cols-2 gap-2">
              <input className="input" type="number" step="0.01" placeholder="Valor/Hora" value={regraForm.valor_hora} onChange={(e) => setRegraForm({ ...regraForm, valor_hora: e.target.value })} />
              <input className="input" type="number" step="0.01" placeholder="% Êxito" value={regraForm.percentual_exito} onChange={(e) => setRegraForm({ ...regraForm, percentual_exito: e.target.value })} />
              <input className="input" type="number" step="0.01" placeholder="Valor Pacote" value={regraForm.valor_pacote} onChange={(e) => setRegraForm({ ...regraForm, valor_pacote: e.target.value })} />
              <input className="input" type="number" step="0.01" placeholder="Valor Recorrente" value={regraForm.valor_recorrente} onChange={(e) => setRegraForm({ ...regraForm, valor_recorrente: e.target.value })} />
            </div>
            <button className="btn-primary w-full" type="submit">Salvar Regra</button>
          </form>

          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {regras.map((r) => (
              <div key={r.id} className="rounded-lg border border-gray-200 p-2 text-sm">
                <div className="font-medium">{r.titulo}</div>
                <div className="text-xs text-gray-500">{r.tipo_cobranca_display} • {r.cliente_nome}</div>
              </div>
            ))}
            {regras.length === 0 && <p className="text-sm text-gray-400">Sem regras cadastradas.</p>}
          </div>
        </div>

        <div className="card space-y-3">
          <h2 className="text-base font-semibold">Time Tracking</h2>
          <form className="space-y-3" onSubmit={criarApontamento}>
            <select className="input" value={apForm.cliente} onChange={(e) => setApForm({ ...apForm, cliente: e.target.value })}>
              <option value="">Cliente*</option>
              {clientes.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
            </select>
            <select className="input" value={apForm.processo} onChange={(e) => setApForm({ ...apForm, processo: e.target.value })}>
              <option value="">Processo (opcional)</option>
              {processos.map((p) => <option key={p.id} value={p.id}>{p.numero} - {p.cliente_nome}</option>)}
            </select>
            <select className="input" value={apForm.regra_cobranca} onChange={(e) => setApForm({ ...apForm, regra_cobranca: e.target.value })}>
              <option value="">Regra (opcional)</option>
              {regras.map((r) => <option key={r.id} value={r.id}>{r.titulo}</option>)}
            </select>
            <input className="input" type="date" value={apForm.data} onChange={(e) => setApForm({ ...apForm, data: e.target.value })} />
            <input className="input" placeholder="Descrição*" value={apForm.descricao} onChange={(e) => setApForm({ ...apForm, descricao: e.target.value })} />
            <div className="grid grid-cols-2 gap-2">
              <input className="input" type="number" min="1" placeholder="Minutos*" value={apForm.minutos} onChange={(e) => setApForm({ ...apForm, minutos: e.target.value })} />
              <input className="input" type="number" step="0.01" placeholder="Valor/hora" value={apForm.valor_hora} onChange={(e) => setApForm({ ...apForm, valor_hora: e.target.value })} />
            </div>
            <button className="btn-primary w-full" type="submit">Registrar Tempo</button>
          </form>

          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {apontamentos.slice(0, 20).map((a) => (
              <div key={a.id} className="rounded-lg border border-gray-200 p-2 text-sm">
                <div className="font-medium">{a.descricao}</div>
                <div className="text-xs text-gray-500">{a.cliente_nome} • {a.minutos} min • {fmtDate(a.data)}</div>
                <div className="text-xs text-gray-400">Estimado: {fmtBRL(a.valor_estimado)}</div>
              </div>
            ))}
            {apontamentos.length === 0 && <p className="text-sm text-gray-400">Sem apontamentos.</p>}
          </div>
        </div>

        <div className="card space-y-3">
          <h2 className="text-base font-semibold">Gerar Fatura</h2>
          <form className="space-y-3" onSubmit={gerarFatura}>
            <select className="input" value={faturaForm.cliente} onChange={(e) => setFaturaForm({ ...faturaForm, cliente: e.target.value, processo: "", regra_cobranca: "" })}>
              <option value="">Cliente*</option>
              {clientes.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
            </select>
            <select className="input" value={faturaForm.processo} onChange={(e) => setFaturaForm({ ...faturaForm, processo: e.target.value })}>
              <option value="">Processo (opcional)</option>
              {processosCliente.map((p) => <option key={p.id} value={p.id}>{p.numero}</option>)}
            </select>
            <select className="input" value={faturaForm.regra_cobranca} onChange={(e) => setFaturaForm({ ...faturaForm, regra_cobranca: e.target.value })}>
              <option value="">Regra (opcional)</option>
              {regrasCliente.map((r) => <option key={r.id} value={r.id}>{r.titulo}</option>)}
            </select>
            <div className="grid grid-cols-2 gap-2">
              <input className="input" type="date" value={faturaForm.periodo_inicio} onChange={(e) => setFaturaForm({ ...faturaForm, periodo_inicio: e.target.value })} />
              <input className="input" type="date" value={faturaForm.periodo_fim} onChange={(e) => setFaturaForm({ ...faturaForm, periodo_fim: e.target.value })} />
              <input className="input" type="date" value={faturaForm.data_vencimento} onChange={(e) => setFaturaForm({ ...faturaForm, data_vencimento: e.target.value })} />
              <input className="input" type="number" step="0.01" placeholder="Base êxito" value={faturaForm.valor_base_exito} onChange={(e) => setFaturaForm({ ...faturaForm, valor_base_exito: e.target.value })} />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <input className="input" type="number" step="0.01" placeholder="Ajuste R$" value={faturaForm.adicional_valor} onChange={(e) => setFaturaForm({ ...faturaForm, adicional_valor: e.target.value })} />
              <input className="input" placeholder="Descrição ajuste" value={faturaForm.adicional_descricao} onChange={(e) => setFaturaForm({ ...faturaForm, adicional_descricao: e.target.value })} />
            </div>
            <label className="text-sm flex items-center gap-2">
              <input
                type="checkbox"
                checked={faturaForm.incluir_despesas_reembolsaveis}
                onChange={(e) => setFaturaForm({ ...faturaForm, incluir_despesas_reembolsaveis: e.target.checked })}
              />
              Incluir despesas reembolsáveis
            </label>
            <button className="btn-primary w-full" type="submit">Gerar Fatura</button>
          </form>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold">Faturas e Recebimento Online</h2>
          <div className="text-xs text-gray-500">{faturas.length} fatura(s)</div>
        </div>

        <div className="space-y-3">
          {faturas.length === 0 && <p className="text-sm text-gray-400">Nenhuma fatura criada.</p>}
          {faturas.map((f) => (
            <div key={f.id} className="rounded-lg border border-gray-200 p-3 text-sm">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div>
                  <div className="font-semibold">{f.numero} • {f.cliente_nome}</div>
                  <div className="text-xs text-gray-500">Vencimento: {fmtDate(f.data_vencimento)} • Total: {fmtBRL(f.total)}</div>
                  <div className="text-xs text-gray-400">Online: {f.online_status_display || f.online_status}</div>
                </div>
                <div className="flex items-center gap-2 flex-wrap justify-end">
                  <span className={STATUS_FATURA[f.status] || "badge-gray"}>{f.status_display || f.status}</span>
                  {f.status === "rascunho" && (
                    <button className="btn-secondary text-xs" onClick={() => acaoFatura(f.id, "enviar")}>Enviar</button>
                  )}
                  {f.status !== "cancelada" && f.status !== "paga" && (
                    <button className="btn-secondary text-xs" onClick={() => acaoFatura(f.id, "gerar-link", { gateway: "manual" })}>Gerar Link</button>
                  )}
                  {f.status !== "paga" && f.status !== "cancelada" && (
                    <button className="btn-secondary text-xs text-green-700" onClick={() => acaoFatura(f.id, "marcar_paga")}>Marcar Paga</button>
                  )}
                </div>
              </div>
              {f.online_url && (
                <div className="mt-2 text-xs">
                  <a className="text-primary-700 hover:text-primary-900 underline break-all" href={f.online_url} target="_blank" rel="noreferrer">
                    {f.online_url}
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
