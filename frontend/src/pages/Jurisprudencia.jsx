import { useState, useEffect, useCallback } from "react";
import { format, parseISO } from "date-fns";
import { ptBR } from "date-fns/locale";
import api from "../api/axios";
import toast from "react-hot-toast";

const TIPOS = ["acordao","sumula","decisao_monocratica","ementa","outros"];
const RESULTADOS = ["procedente","improcedente","parcialmente_procedente","extinto","outros"];
const TRIBUNAIS = ["STF","STJ","TST","TRF","TJSP","TJRJ","TJMG","TJRS","TJBA","TJPE","outros"];

function badgeTipo(t) {
  const m = { acordao:"badge-blue", sumula:"badge-green", decisao_monocratica:"badge-yellow", ementa:"badge-gray", outros:"badge-gray" };
  return m[t] || "badge-gray";
}
function badgeRes(r) {
  const m = { procedente:"badge-green", improcedente:"badge-red", parcialmente_procedente:"badge-yellow", extinto:"badge-gray", outros:"badge-gray" };
  return m[r] || "badge-gray";
}

export default function Jurisprudencia() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterTipo, setFilterTipo] = useState("");
  const [filterTribunal, setFilterTribunal] = useState("");
  const [expanded, setExpanded] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ titulo:"", tipo:"acordao", tribunal:"STJ", numero_processo:"", resultado:"procedente", data_julgamento:"", ementa:"", texto_completo:"", palavras_chave:"" });

  const fetch = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.append("search", search);
    if (filterTipo) params.append("tipo", filterTipo);
    if (filterTribunal) params.append("tribunal", filterTribunal);
    api.get(`/documentos/?${params}`).then((r) => setDocs(r.data?.results || r.data || [])).finally(() => setLoading(false));
  }, [search, filterTipo, filterTribunal]);

  useEffect(() => { fetch(); }, [fetch]);

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      const payload = {...form};
      if (!payload.data_julgamento) delete payload.data_julgamento;
      await api.post("/documentos/", payload);
      toast.success("Documento adicionado!");
      setShowModal(false);
      fetch();
    } catch (err) {
      toast.error(err.response?.data ? JSON.stringify(err.response.data).slice(0,140) : "Erro ao salvar");
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">⚖️ Jurisprudência</h1>
        <button onClick={() => { setForm({ titulo:"", tipo:"acordao", tribunal:"STJ", numero_processo:"", resultado:"procedente", data_julgamento:"", ementa:"", texto_completo:"", palavras_chave:"" }); setShowModal(true); }} className="btn-primary">+ Adicionar</button>
      </div>

      <div className="flex flex-wrap gap-3">
        <input className="input flex-1 min-w-48" placeholder="Buscar na jurisprudência..." value={search} onChange={(e) => setSearch(e.target.value)} />
        <select className="input w-44" value={filterTipo} onChange={(e) => setFilterTipo(e.target.value)}>
          <option value="">Todos tipos</option>
          {TIPOS.map((t) => <option key={t} value={t}>{t.replace("_"," ").replace(/\b\w/g, c => c.toUpperCase())}</option>)}
        </select>
        <select className="input w-40" value={filterTribunal} onChange={(e) => setFilterTribunal(e.target.value)}>
          <option value="">Todos tribunais</option>
          {TRIBUNAIS.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      <div className="space-y-3">
        {loading ? <div className="card text-center text-gray-400 py-8">Carregando...</div>
        : docs.length === 0 ? <div className="card text-center text-gray-400 py-8">Nenhum documento encontrado</div>
        : docs.map((d) => (
          <div key={d.id} className="card cursor-pointer hover:shadow-md transition-shadow" onClick={() => setExpanded(expanded === d.id ? null : d.id)}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap gap-2 mb-1">
                  <span className={badgeTipo(d.tipo)}>{d.tipo?.replace("_"," ")}</span>
                  <span className="badge-gray font-semibold">{d.tribunal}</span>
                  {d.resultado && <span className={badgeRes(d.resultado)}>{d.resultado?.replace("_"," ")}</span>}
                </div>
                <h3 className="font-semibold text-gray-900 truncate">{d.titulo}</h3>
                {d.numero_processo && <p className="text-xs text-gray-500 font-mono mt-0.5">{d.numero_processo}</p>}
              </div>
              <div className="text-right text-xs text-gray-400 shrink-0">
                {d.data_julgamento && format(parseISO(d.data_julgamento), "dd/MM/yyyy", { locale: ptBR })}
                <div className="mt-1">{expanded === d.id ? "▲" : "▼"}</div>
              </div>
            </div>
            {expanded === d.id && (
              <div className="mt-3 pt-3 border-t space-y-2">
                {d.ementa && <div><p className="text-xs font-semibold text-gray-500 uppercase mb-1">Ementa</p><p className="text-sm text-gray-700 leading-relaxed">{d.ementa}</p></div>}
                {d.palavras_chave && <div><p className="text-xs font-semibold text-gray-500 uppercase mb-1">Palavras-chave</p><p className="text-sm text-gray-600">{d.palavras_chave}</p></div>}
                {d.texto_completo && <div><p className="text-xs font-semibold text-gray-500 uppercase mb-1">Texto Completo</p><p className="text-sm text-gray-700 leading-relaxed max-h-40 overflow-y-auto">{d.texto_completo}</p></div>}
              </div>
            )}
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-screen overflow-y-auto">
            <div className="p-6 border-b flex justify-between items-center">
              <h2 className="text-lg font-semibold">Adicionar Documento</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2"><label className="label">Título *</label><input className="input" required value={form.titulo} onChange={(e) => setForm({...form, titulo: e.target.value})} /></div>
                <div><label className="label">Tipo *</label><select className="input" value={form.tipo} onChange={(e) => setForm({...form, tipo: e.target.value})}>{TIPOS.map((t) => <option key={t} value={t}>{t.replace("_"," ")}</option>)}</select></div>
                <div><label className="label">Tribunal *</label><select className="input" value={form.tribunal} onChange={(e) => setForm({...form, tribunal: e.target.value})}>{TRIBUNAIS.map((t) => <option key={t} value={t}>{t}</option>)}</select></div>
                <div><label className="label">Nº Processo</label><input className="input" value={form.numero_processo} onChange={(e) => setForm({...form, numero_processo: e.target.value})} /></div>
                <div><label className="label">Resultado</label><select className="input" value={form.resultado} onChange={(e) => setForm({...form, resultado: e.target.value})}>{RESULTADOS.map((r) => <option key={r} value={r}>{r.replace("_"," ")}</option>)}</select></div>
                <div className="col-span-2"><label className="label">Data do Julgamento</label><input className="input" type="date" value={form.data_julgamento} onChange={(e) => setForm({...form, data_julgamento: e.target.value})} /></div>
                <div className="col-span-2"><label className="label">Ementa *</label><textarea className="input" rows={3} required value={form.ementa} onChange={(e) => setForm({...form, ementa: e.target.value})} /></div>
                <div className="col-span-2"><label className="label">Palavras-chave</label><input className="input" placeholder="separadas por vírgula" value={form.palavras_chave} onChange={(e) => setForm({...form, palavras_chave: e.target.value})} /></div>
                <div className="col-span-2"><label className="label">Texto Completo</label><textarea className="input" rows={4} value={form.texto_completo} onChange={(e) => setForm({...form, texto_completo: e.target.value})} /></div>
              </div>
              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
                <button type="submit" className="btn-primary">Adicionar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
