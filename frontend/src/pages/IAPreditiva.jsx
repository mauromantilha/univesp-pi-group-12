import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import api from "../api/axios";
import toast from "react-hot-toast";

const TABS = ["chat", "processo", "cliente_demanda", "pecas", "monitor"];
const TAB_LABELS = {
  chat: "💬 Chat Jurídico",
  processo: "⚖️ Análise de Processo",
  cliente_demanda: "👥 Cliente e Demanda",
  pecas: "📝 Assistente de Peças",
  monitor: "🛡️ Monitor IA",
};

function toList(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.results || [];
}

function RiskBar({ value }) {
  const color = value >= 70 ? "bg-green-500" : value >= 40 ? "bg-yellow-400" : "bg-red-500";
  return (
    <div className="w-full bg-gray-200 rounded-full h-3">
      <div className={`${color} h-3 rounded-full transition-all duration-700`} style={{ width: `${value}%` }} />
    </div>
  );
}

function ChatTab() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Olá! Sou a Lola, assistente jurídica da Santos Nobre. Como posso ajudar?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    const updated = [...messages, { role: "user", content: text }];
    setMessages(updated);
    setLoading(true);

    try {
      const historico = updated.slice(-10).map((m) => ({ role: m.role, content: m.content }));
      const res = await api.post("/ia/chat/", { mensagem: text, historico });
      const reply = res.data?.resposta || res.data?.message || JSON.stringify(res.data);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch {
      toast.error("Erro ao comunicar com IA");
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Desculpe, ocorreu um erro ao processar sua mensagem." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-[620px]">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                m.role === "user"
                  ? "bg-primary-600 text-white rounded-br-sm"
                  : "bg-gray-100 text-gray-800 rounded-bl-sm"
              }`}
            >
              {m.role === "assistant" ? <ReactMarkdown>{m.content}</ReactMarkdown> : m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1 items-center">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={send} className="border-t p-4 flex gap-2">
        <input
          className="input flex-1"
          placeholder="Digite sua pergunta jurídica..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()} className="btn-primary px-5 disabled:opacity-50">
          Enviar
        </button>
      </form>
    </div>
  );
}

function ProcessoAnaliseTab() {
  const [processos, setProcessos] = useState([]);
  const [processoId, setProcessoId] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api.get("/processos/?limit=200").then((r) => setProcessos(toList(r.data))).catch(() => setProcessos([]));
  }, []);

  async function analisar() {
    if (!processoId) {
      toast.error("Selecione um processo");
      return;
    }
    setLoading(true);
    try {
      const res = await api.post("/ia/analises/analisar/", { processo_id: Number(processoId) });
      setResult(res.data);
    } catch (err) {
      toast.error(err.response?.data?.error || "Erro ao analisar processo");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  const riscoClass = useMemo(() => {
    const nivel = result?.nivel_risco;
    if (nivel === "baixo") return "text-green-600";
    if (nivel === "medio") return "text-yellow-600";
    return "text-red-600";
  }, [result]);

  return (
    <div className="p-4 space-y-5">
      <div className="flex gap-3 items-end">
        <div className="flex-1">
          <label className="label">Processo</label>
          <select className="input" value={processoId} onChange={(e) => setProcessoId(e.target.value)}>
            <option value="">Selecione...</option>
            {processos.map((p) => (
              <option key={p.id} value={p.id}>
                {p.numero} — {p.cliente_nome || "-"}
              </option>
            ))}
          </select>
        </div>
        <button onClick={analisar} className="btn-primary h-10" disabled={loading || !processoId}>
          {loading ? "Analisando..." : "Analisar"}
        </button>
      </div>

      {result && (
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-800">Previsão de Êxito</h3>
              <span className={`text-2xl font-bold ${riscoClass}`}>{Number(result.probabilidade_sucesso || 0).toFixed(2)}%</span>
            </div>
            <RiskBar value={Number(result.probabilidade_sucesso || 0)} />
            <p className="mt-2 text-xs text-gray-500">
              Nível de risco: <strong className={riscoClass}>{result.nivel_risco || "-"}</strong>
            </p>
          </div>

          {result.justificativa && (
            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-2">Justificativa</h3>
              <div className="prose prose-sm max-w-none text-gray-700">
                <ReactMarkdown>{result.justificativa}</ReactMarkdown>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-2">Fatores de Risco</h3>
              {result.fatores_risco?.length ? (
                <ul className="space-y-1 text-sm">
                  {result.fatores_risco.map((f, i) => (
                    <li key={i} className="text-red-700">• {f}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-400">Sem riscos críticos imediatos.</p>
              )}
            </div>

            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-2">Pontos Favoráveis</h3>
              {result.pontos_favoraveis?.length ? (
                <ul className="space-y-1 text-sm">
                  {result.pontos_favoraveis.map((f, i) => (
                    <li key={i} className="text-green-700">• {f}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-400">Sem pontos favoráveis destacados.</p>
              )}
            </div>
          </div>

          <div className="card">
            <h3 className="font-semibold text-gray-800 mb-2">Demandas Similares Internas</h3>
            {result.similares_internos?.length ? (
              <div className="space-y-2 max-h-56 overflow-y-auto">
                {result.similares_internos.map((s) => (
                  <div key={s.id} className="rounded-lg border border-gray-200 px-3 py-2 text-sm">
                    <div className="font-medium font-mono text-xs">{s.numero}</div>
                    <div className="text-xs text-gray-500">{s.cliente_nome} • {s.tipo_nome}</div>
                    <div className="text-xs text-primary-700">Similaridade: {s.score_similaridade}%</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">Não foram encontrados similares relevantes.</p>
            )}
          </div>

          <div className="card">
            <h3 className="font-semibold text-gray-800 mb-2">Jurisprudência em Tribunais Superiores</h3>
            {result.jurisprudencia_superior?.length ? (
              <div className="space-y-2 max-h-56 overflow-y-auto">
                {result.jurisprudencia_superior.map((j, i) => (
                  <div key={`${j.id || j.consulta_id || i}`} className="rounded-lg border border-gray-200 px-3 py-2 text-sm">
                    <div className="font-medium">{j.titulo || j.numero_processo || "Jurisprudência"}</div>
                    <div className="text-xs text-gray-500">{j.tribunal || "Tribunal superior"}</div>
                    {j.resumo && <div className="text-xs text-gray-600 mt-1">{j.resumo}</div>}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">Sem jurisprudência superior aderente para os termos atuais.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function ClienteDemandaTab() {
  const [modo, setModo] = useState("cliente");
  const [clientes, setClientes] = useState([]);
  const [clienteId, setClienteId] = useState("");
  const [demanda, setDemanda] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api.get("/clientes/?limit=300").then((r) => setClientes(toList(r.data))).catch(() => setClientes([]));
  }, []);

  async function analisar() {
    setLoading(true);
    setResult(null);
    try {
      if (modo === "cliente") {
        if (!clienteId) {
          toast.error("Selecione um cliente");
          setLoading(false);
          return;
        }
        const res = await api.post("/ia/analises/cliente/", { cliente_id: Number(clienteId), demanda });
        setResult(res.data);
      } else {
        if (!demanda.trim()) {
          toast.error("Informe a demanda");
          setLoading(false);
          return;
        }
        const res = await api.post("/ia/analises/demanda/", { demanda });
        setResult(res.data);
      }
    } catch (err) {
      toast.error(err.response?.data?.error || "Erro na análise");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex gap-2">
        <button
          onClick={() => setModo("cliente")}
          className={`btn-secondary text-sm ${modo === "cliente" ? "bg-primary-100 text-primary-800" : ""}`}
        >
          Analisar Cliente
        </button>
        <button
          onClick={() => setModo("demanda")}
          className={`btn-secondary text-sm ${modo === "demanda" ? "bg-primary-100 text-primary-800" : ""}`}
        >
          Analisar Demanda Livre
        </button>
      </div>

      {modo === "cliente" && (
        <div>
          <label className="label">Cliente</label>
          <select className="input" value={clienteId} onChange={(e) => setClienteId(e.target.value)}>
            <option value="">Selecione...</option>
            {clientes.map((c) => (
              <option key={c.id} value={c.id}>{c.nome}</option>
            ))}
          </select>
        </div>
      )}

      <div>
        <label className="label">Demanda (opcional para cliente / obrigatório em demanda livre)</label>
        <textarea className="input" rows={4} value={demanda} onChange={(e) => setDemanda(e.target.value)} />
      </div>

      <button onClick={analisar} className="btn-primary" disabled={loading}>
        {loading ? "Analisando..." : "Executar Análise"}
      </button>

      {result && (
        <div className="space-y-3">
          <div className="card">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-gray-800">Previsão de Êxito</h3>
              <span className="text-2xl font-bold text-primary-700">{Number(result.probabilidade_sucesso || 0).toFixed(2)}%</span>
            </div>
            <RiskBar value={Number(result.probabilidade_sucesso || 0)} />
            <div className="text-xs text-gray-500 mt-2">Risco estimado: {result.nivel_risco || "-"}</div>
          </div>

          {result.resumo && (
            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-2">Resumo do Cliente</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
                <MiniStat label="Processos" value={result.resumo.total_processos} />
                <MiniStat label="Ativos" value={result.resumo.ativos} />
                <MiniStat label="Finalizados" value={result.resumo.finalizados} />
                <MiniStat label="Arquivados" value={result.resumo.arquivados} />
                <MiniStat label="Prazos Críticos" value={result.resumo.prazos_criticos_3_dias} />
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-2">Similares Internos</h3>
              {result.similares_internos?.length ? (
                <div className="space-y-2 max-h-56 overflow-y-auto">
                  {result.similares_internos.map((s) => (
                    <div key={s.id} className="rounded-lg border border-gray-200 px-3 py-2 text-sm">
                      <div className="font-mono text-xs font-semibold">{s.numero}</div>
                      <div className="text-xs text-gray-500">{s.cliente_nome}</div>
                      <div className="text-xs text-primary-700">{s.score_similaridade}% similar</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-400">Nenhum similar encontrado.</p>
              )}
            </div>

            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-2">Jurisprudência Superior</h3>
              {result.jurisprudencia_superior?.length ? (
                <div className="space-y-2 max-h-56 overflow-y-auto">
                  {result.jurisprudencia_superior.map((j, i) => (
                    <div key={`${j.id || j.consulta_id || i}`} className="rounded-lg border border-gray-200 px-3 py-2 text-sm">
                      <div className="font-medium">{j.titulo || j.numero_processo || "Jurisprudência"}</div>
                      <div className="text-xs text-gray-500">{j.tribunal || "Superior"}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-400">Sem sugestões no momento.</p>
              )}
            </div>
          </div>

          {result.recomendacoes?.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-2">Recomendações</h3>
              <ul className="space-y-1 text-sm text-gray-700">
                {result.recomendacoes.map((r, i) => (
                  <li key={i}>• {r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PecasTab() {
  const [processos, setProcessos] = useState([]);
  const [processoId, setProcessoId] = useState("");
  const [tipoPeca, setTipoPeca] = useState("peticao");
  const [objetivo, setObjetivo] = useState("");
  const [tesePrincipal, setTesePrincipal] = useState("");
  const [pedidos, setPedidos] = useState("");
  const [texto, setTexto] = useState("");
  const [revisao, setRevisao] = useState(null);
  const [loadingGeracao, setLoadingGeracao] = useState(false);
  const [loadingRevisao, setLoadingRevisao] = useState(false);

  useEffect(() => {
    api.get("/processos/?limit=200").then((r) => setProcessos(toList(r.data))).catch(() => setProcessos([]));
  }, []);

  async function gerarPeca() {
    setLoadingGeracao(true);
    try {
      const payload = {
        processo_id: processoId ? Number(processoId) : null,
        tipo_peca: tipoPeca,
        objetivo,
        tese_principal: tesePrincipal,
        pedidos: pedidos
          .split("\n")
          .map((p) => p.trim())
          .filter(Boolean),
      };
      const res = await api.post("/ia/analises/redigir-peca/", payload);
      setTexto(res.data?.texto || "");
      setRevisao(null);
      toast.success("Minuta gerada");
    } catch (err) {
      toast.error(err.response?.data?.error || "Erro ao gerar peça");
    } finally {
      setLoadingGeracao(false);
    }
  }

  async function revisarPeca() {
    if (!texto.trim()) {
      toast.error("Escreva ou gere a peça antes de revisar");
      return;
    }
    setLoadingRevisao(true);
    try {
      const res = await api.post("/ia/analises/revisar-peca/", { texto, tipo_peca: tipoPeca });
      setRevisao(res.data);
      toast.success("Revisão concluída");
    } catch (err) {
      toast.error(err.response?.data?.error || "Erro ao revisar peça");
    } finally {
      setLoadingRevisao(false);
    }
  }

  return (
    <div className="p-4 space-y-4">
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="space-y-3">
          <div>
            <label className="label">Processo (opcional)</label>
            <select className="input" value={processoId} onChange={(e) => setProcessoId(e.target.value)}>
              <option value="">Sem vínculo direto</option>
              {processos.map((p) => (
                <option key={p.id} value={p.id}>{p.numero} — {p.cliente_nome || "-"}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Tipo de Peça</label>
            <select className="input" value={tipoPeca} onChange={(e) => setTipoPeca(e.target.value)}>
              <option value="defesa">Defesa</option>
              <option value="recurso">Recurso</option>
              <option value="peticao">Petição</option>
              <option value="manifestacao">Manifestação</option>
              <option value="outro">Outro</option>
            </select>
          </div>
          <div>
            <label className="label">Objetivo</label>
            <textarea className="input" rows={2} value={objetivo} onChange={(e) => setObjetivo(e.target.value)} />
          </div>
          <div>
            <label className="label">Tese Principal</label>
            <textarea className="input" rows={2} value={tesePrincipal} onChange={(e) => setTesePrincipal(e.target.value)} />
          </div>
          <div>
            <label className="label">Pedidos (um por linha)</label>
            <textarea className="input" rows={3} value={pedidos} onChange={(e) => setPedidos(e.target.value)} />
          </div>
          <div className="flex gap-2">
            <button className="btn-primary" onClick={gerarPeca} disabled={loadingGeracao}>
              {loadingGeracao ? "Gerando..." : "Gerar Minuta"}
            </button>
            <button className="btn-secondary" onClick={revisarPeca} disabled={loadingRevisao || !texto.trim()}>
              {loadingRevisao ? "Revisando..." : "Revisar Texto"}
            </button>
          </div>
        </div>

        <div>
          <label className="label">Texto da Peça</label>
          <textarea className="input min-h-[430px] font-mono text-xs" value={texto} onChange={(e) => setTexto(e.target.value)} />
        </div>
      </div>

      {revisao && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <div className="card">
            <h3 className="font-semibold text-gray-800 mb-2">Score de Qualidade</h3>
            <div className="text-3xl font-bold text-primary-700">{revisao.score_qualidade}/100</div>
            <RiskBar value={Number(revisao.score_qualidade || 0)} />
          </div>

          <div className="card">
            <h3 className="font-semibold text-gray-800 mb-2">Riscos de Indeferimento</h3>
            {revisao.riscos_indeferimento?.length ? (
              <ul className="space-y-1 text-sm text-red-700">
                {revisao.riscos_indeferimento.map((i, idx) => (
                  <li key={idx}>• {i}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400">Sem riscos críticos identificados.</p>
            )}
          </div>

          <div className="card">
            <h3 className="font-semibold text-gray-800 mb-2">Erros de Gramática</h3>
            {revisao.erros_gramatica?.length ? (
              <ul className="space-y-1 text-sm text-amber-700">
                {revisao.erros_gramatica.map((i, idx) => (
                  <li key={idx}>• {i}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400">Não foram encontrados erros relevantes.</p>
            )}
          </div>

          <div className="card">
            <h3 className="font-semibold text-gray-800 mb-2">Erros de Lógica Jurídica</h3>
            {revisao.erros_logica?.length ? (
              <ul className="space-y-1 text-sm text-red-700">
                {revisao.erros_logica.map((i, idx) => (
                  <li key={idx}>• {i}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400">Estrutura lógica sem inconsistências críticas.</p>
            )}
          </div>

          {revisao.sugestoes?.length > 0 && (
            <div className="card xl:col-span-2">
              <h3 className="font-semibold text-gray-800 mb-2">Sugestões da IA</h3>
              <ul className="space-y-1 text-sm text-gray-700">
                {revisao.sugestoes.map((s, i) => (
                  <li key={i}>• {s}</li>
                ))}
              </ul>
              {revisao.comentario_ia && (
                <div className="mt-3 prose prose-sm max-w-none text-gray-700">
                  <ReactMarkdown>{revisao.comentario_ia}</ReactMarkdown>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function MonitorTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  async function carregar() {
    setLoading(true);
    try {
      const res = await api.get("/ia/analises/monitoramento/");
      setData(res.data);
    } catch {
      toast.error("Erro ao carregar monitoramento IA");
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    carregar();
  }, []);

  if (loading) return <div className="text-center text-gray-400 py-12">Carregando monitoramento...</div>;

  if (!data) return <div className="text-center text-gray-400 py-12">Sem dados de monitoramento.</div>;

  return (
    <div className="p-4 space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MiniStat label="Prazos Atrasados" value={data.prazos?.atrasados_total || 0} danger />
        <MiniStat label="Prazos 7 dias" value={data.prazos?.proximos_7_dias_total || 0} />
        <MiniStat label="Contas a Pagar" value={data.financeiro?.contas_pagar_pendentes || 0} />
        <MiniStat label="Contas a Receber" value={data.financeiro?.contas_receber_pendentes || 0} />
      </div>

      <div className="card">
        <h3 className="font-semibold text-gray-800 mb-2">Alertas de Prazos</h3>
        {data.prazos?.atrasados?.length || data.prazos?.proximos?.length ? (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {data.prazos.atrasados?.map((p) => (
              <div key={`a-${p.id}`} className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm">
                <div className="font-medium">{p.titulo}</div>
                <div className="text-xs text-red-700">Atrasado • {p.data} • {p.processo_numero || "-"}</div>
              </div>
            ))}
            {data.prazos.proximos?.map((p) => (
              <div key={`p-${p.id}`} className="rounded-lg border border-yellow-200 bg-yellow-50 px-3 py-2 text-sm">
                <div className="font-medium">{p.titulo}</div>
                <div className="text-xs text-yellow-700">Próximo • {p.data} • {p.processo_numero || "-"}</div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">Sem alertas críticos de prazo.</p>
        )}
      </div>

      <div className="card">
        <h3 className="font-semibold text-gray-800 mb-2">Erros e Eventos do Sistema</h3>
        {data.sistema?.eventos?.length ? (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {data.sistema.eventos.map((e) => (
              <div key={e.id} className="rounded-lg border border-gray-200 px-3 py-2 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium">{e.mensagem}</span>
                  <span className={`text-xs ${e.severidade === "critico" ? "text-red-700" : e.severidade === "alerta" ? "text-amber-700" : "text-blue-700"}`}>
                    {e.severidade_display || e.severidade}
                  </span>
                </div>
                <div className="text-xs text-gray-500">{e.tipo_display || e.tipo} • {e.rota || "-"}</div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">Nenhum evento aberto no monitoramento.</p>
        )}
      </div>

      <button className="btn-secondary" onClick={carregar}>Atualizar Monitoramento</button>
    </div>
  );
}

function MiniStat({ label, value, danger = false }) {
  return (
    <div className={`rounded-xl border px-3 py-3 ${danger ? "border-red-200 bg-red-50" : "border-gray-200 bg-white"}`}>
      <div className={`text-2xl font-bold ${danger ? "text-red-700" : "text-gray-800"}`}>{value ?? 0}</div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
    </div>
  );
}

export default function IAPreditiva() {
  const [tab, setTab] = useState("chat");

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-bold text-gray-900">🤖 IA Jurídica</h1>
        <span className="badge-blue text-xs">Análise de processos, clientes, peças e monitoramento</span>
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="flex flex-wrap border-b bg-gray-50">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-3 text-sm font-medium transition-colors ${
                tab === t ? "bg-white border-b-2 border-primary-600 text-primary-700" : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
              }`}
            >
              {TAB_LABELS[t]}
            </button>
          ))}
        </div>

        {tab === "chat" && <ChatTab />}
        {tab === "processo" && <ProcessoAnaliseTab />}
        {tab === "cliente_demanda" && <ClienteDemandaTab />}
        {tab === "pecas" && <PecasTab />}
        {tab === "monitor" && <MonitorTab />}
      </div>
    </div>
  );
}
