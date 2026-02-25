import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import api from "../api/axios";
import toast from "react-hot-toast";

const TABS = ["chat","risco","sugestoes"];
const TAB_LABELS = { chat:"💬 Chat Jurídico", risco:"📊 Análise de Risco", sugestoes:"🔍 Sugestões de Jurisprudência" };

function RiskBar({ value }) {
  const color = value >= 70 ? "bg-red-500" : value >= 40 ? "bg-yellow-400" : "bg-green-500";
  return (
    <div className="w-full bg-gray-200 rounded-full h-3">
      <div className={`${color} h-3 rounded-full transition-all duration-700`} style={{ width: `${value}%` }} />
    </div>
  );
}

function ChatTab() {
  const [messages, setMessages] = useState([{ role:"assistant", content:"Olá! Sou a Lola, assistente jurídica da Santos Nobre. Como posso ajudar?" }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior:"smooth" }); }, [messages]);

  async function send(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    const updated = [...messages, { role:"user", content:text }];
    setMessages(updated);
    setLoading(true);
    try {
      const history = updated.slice(-10).map(m => ({ role:m.role, content:m.content }));
      const res = await api.post("/ia/chat/", { mensagem: text, historico: history });
      const reply = res.data?.resposta || res.data?.message || JSON.stringify(res.data);
      setMessages(prev => [...prev, { role:"assistant", content:reply }]);
    } catch (err) {
      toast.error("Erro ao comunicar com IA");
      setMessages(prev => [...prev, { role:"assistant", content:"Desculpe, ocorreu um erro ao processar sua mensagem." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-[600px]">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${m.role === "user" ? "bg-primary-600 text-white rounded-br-sm" : "bg-gray-100 text-gray-800 rounded-bl-sm"}`}>
              {m.role === "assistant" ? <ReactMarkdown>{m.content}</ReactMarkdown> : m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1 items-center">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay:"0ms"}} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay:"150ms"}} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay:"300ms"}} />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={send} className="border-t p-4 flex gap-2">
        <input className="input flex-1" placeholder="Digite sua pergunta jurídica..." value={input} onChange={(e) => setInput(e.target.value)} disabled={loading} />
        <button type="submit" disabled={loading || !input.trim()} className="btn-primary px-5 disabled:opacity-50">Enviar</button>
      </form>
    </div>
  );
}

function RiscoTab() {
  const [processos, setProcessos] = useState([]);
  const [processoId, setProcessoId] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api.get("/processos/?limit=100").then((r) => setProcessos(r.data?.results || r.data || []));
  }, []);

  async function analisar() {
    if (!processoId) { toast.error("Selecione um processo"); return; }
    setLoading(true);
    setResult(null);
    try {
      const res = await api.post("/ia/analises/analisar/", { processo_id: parseInt(processoId) });
      setResult(res.data);
    } catch (err) {
      toast.error(err.response?.data ? JSON.stringify(err.response.data).slice(0,120) : "Erro na análise");
    } finally { setLoading(false); }
  }

  const riskColor = result ? (result.probabilidade_sucesso >= 70 ? "text-green-600" : result.probabilidade_sucesso >= 40 ? "text-yellow-600" : "text-red-600") : "";

  return (
    <div className="p-4 space-y-5">
      <div className="flex gap-3 items-end">
        <div className="flex-1">
          <label className="label">Selecione o Processo</label>
          <select className="input" value={processoId} onChange={(e) => setProcessoId(e.target.value)}>
            <option value="">— escolha um processo —</option>
            {processos.map((p) => <option key={p.id} value={p.id}>{p.numero} — {p.cliente_nome || p.cliente}</option>)}
          </select>
        </div>
        <button onClick={analisar} disabled={loading || !processoId} className="btn-primary h-10 disabled:opacity-50">
          {loading ? "Analisando..." : "Analisar com IA"}
        </button>
      </div>
      {loading && <div className="card text-center text-gray-400 animate-pulse py-10">Consultando modelo de linguagem...</div>}
      {result && (
        <div className="space-y-4 animate-fade-in">
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-800">Probabilidade de Êxito</h3>
              <span className={`text-2xl font-bold ${riskColor}`}>{result.probabilidade_sucesso}%</span>
            </div>
            <RiskBar value={result.probabilidade_sucesso} />
            <p className="mt-2 text-xs text-gray-500">Nível de risco: <span className={`font-semibold uppercase ${riskColor}`}>{result.nivel_risco || (result.probabilidade_sucesso >= 70 ? "baixo" : result.probabilidade_sucesso >= 40 ? "médio" : "alto")}</span></p>
          </div>
          {result.justificativa && (
            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-2">Justificativa da Análise</h3>
              <div className="prose prose-sm max-w-none text-gray-700"><ReactMarkdown>{result.justificativa}</ReactMarkdown></div>
            </div>
          )}
          {result.fatores_risco?.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-2">Fatores de Risco</h3>
              <ul className="space-y-1">{result.fatores_risco.map((f,i) => <li key={i} className="text-sm text-red-700 flex gap-2"><span>⚠</span>{f}</li>)}</ul>
            </div>
          )}
          {result.pontos_favoraveis?.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-2">Pontos Favoráveis</h3>
              <ul className="space-y-1">{result.pontos_favoraveis.map((f,i) => <li key={i} className="text-sm text-green-700 flex gap-2"><span>✓</span>{f}</li>)}</ul>
            </div>
          )}
          {result.recomendacoes?.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-2">Recomendações</h3>
              <ul className="space-y-1">{result.recomendacoes.map((r,i) => <li key={i} className="text-sm text-primary-700 flex gap-2"><span>→</span>{r}</li>)}</ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SugestoesTab() {
  const [processos, setProcessos] = useState([]);
  const [processoId, setProcessoId] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api.get("/processos/?limit=100").then((r) => setProcessos(r.data?.results || r.data || []));
  }, []);

  async function buscar() {
    if (!processoId) { toast.error("Selecione um processo"); return; }
    setLoading(true);
    setResult(null);
    try {
      const res = await api.post("/ia/sugestoes/sugerir/", { processo_id: parseInt(processoId) });
      setResult(res.data);
    } catch (err) {
      toast.error(err.response?.data ? JSON.stringify(err.response.data).slice(0,120) : "Erro ao buscar sugestões");
    } finally { setLoading(false); }
  }

  return (
    <div className="p-4 space-y-5">
      <div className="flex gap-3 items-end">
        <div className="flex-1">
          <label className="label">Selecione o Processo</label>
          <select className="input" value={processoId} onChange={(e) => setProcessoId(e.target.value)}>
            <option value="">— escolha um processo —</option>
            {processos.map((p) => <option key={p.id} value={p.id}>{p.numero} — {p.cliente_nome || p.cliente}</option>)}
          </select>
        </div>
        <button onClick={buscar} disabled={loading || !processoId} className="btn-primary h-10 disabled:opacity-50">
          {loading ? "Buscando..." : "Buscar Sugestões"}
        </button>
      </div>
      {loading && <div className="card text-center text-gray-400 animate-pulse py-10">Buscando jurisprudência relevante...</div>}
      {result && (
        <div className="space-y-3">
          {result.sugestoes?.length > 0 ? result.sugestoes.map((s, i) => (
            <div key={i} className="card space-y-1">
              <div className="flex gap-2 flex-wrap">
                {s.tipo && <span className="badge-blue text-xs">{s.tipo?.replace("_"," ")}</span>}
                {s.tribunal && <span className="badge-gray text-xs font-semibold">{s.tribunal}</span>}
                {s.relevancia && <span className="text-xs text-gray-500">Relevância: {s.relevancia}%</span>}
              </div>
              <h4 className="font-semibold text-gray-900 text-sm">{s.titulo}</h4>
              {s.ementa && <p className="text-xs text-gray-600 leading-relaxed">{s.ementa}</p>}
              {s.justificativa_relevancia && <p className="text-xs text-primary-700 italic">{s.justificativa_relevancia}</p>}
            </div>
          )) : (
            <div className="card">
              {result.resposta_ia ? (
                <div className="prose prose-sm max-w-none text-gray-700"><ReactMarkdown>{result.resposta_ia}</ReactMarkdown></div>
              ) : <p className="text-gray-400 text-center py-4">Nenhuma sugestão encontrada</p>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function IAPreditiva() {
  const [tab, setTab] = useState("chat");

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">🤖 IA Preditiva</h1>
        <span className="badge-blue text-xs">Powered by llama-3.3-70b-versatile</span>
      </div>
      <div className="card p-0 overflow-hidden">
        <div className="flex border-b bg-gray-50">
          {TABS.map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${tab === t ? "bg-white border-b-2 border-primary-600 text-primary-700" : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"}`}>
              {TAB_LABELS[t]}
            </button>
          ))}
        </div>
        {tab === "chat" && <ChatTab />}
        {tab === "risco" && <RiscoTab />}
        {tab === "sugestoes" && <SugestoesTab />}
      </div>
    </div>
  );
}
