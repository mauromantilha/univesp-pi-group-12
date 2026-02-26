import { useEffect, useState } from "react";
import api from "../api/axios";
import toast from "react-hot-toast";

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

function docName(doc) {
  return doc.titulo || doc.nome_original || doc.arquivo?.split("/").pop() || `Documento #${doc.id}`;
}

function buildPreviewUrl(url) {
  if (!url) return "";
  const lower = String(url).toLowerCase();
  if (lower.includes(".pdf")) return `${url}#toolbar=0&navpanes=0&scrollbar=1`;
  return url;
}

function PreviewPanel({ preview }) {
  return (
    <div className="card h-full flex flex-col">
      <h3 className="text-sm font-semibold text-gray-800 mb-3">Pré-visualização</h3>
      {!preview ? (
        <div className="flex-1 rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-sm text-gray-500">
          Selecione um documento para visualizar em iframe.
        </div>
      ) : (
        <div className="flex-1 min-h-[460px]">
          <div className="text-xs text-gray-500 mb-2 truncate">{preview.nome}</div>
          <iframe
            title="visualizacao-documento"
            src={preview.url}
            className="w-full h-[430px] rounded-lg border border-gray-200 bg-white"
          />
          <p className="text-[11px] text-gray-400 mt-2">
            Visualização embutida. O sistema não exibe botão de download nesta tela.
          </p>
        </div>
      )}
    </div>
  );
}

function ClienteDocs({ setPreview }) {
  const [query, setQuery] = useState("");
  const [resultados, setResultados] = useState([]);
  const [mostrarLista, setMostrarLista] = useState(false);
  const [cliente, setCliente] = useState(null);
  const [documentos, setDocumentos] = useState([]);
  const [arquivos, setArquivos] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [docBusca, setDocBusca] = useState("");
  const [meta, setMeta] = useState({
    template: "",
    titulo: "",
    documento_referencia: "",
    categoria: "",
    descricao: "",
  });
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    api
      .get("/clientes/documentos-templates/")
      .then((r) => setTemplates(toList(r.data)))
      .catch(() => setTemplates([]));
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      const params = new URLSearchParams();
      if (query.trim()) params.set("search", query.trim());
      params.set("limit", "20");
      api
        .get(`/clientes/?${params.toString()}`)
        .then((r) => setResultados(toList(r.data)))
        .catch(() => setResultados([]));
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    if (!cliente?.id) return;
    const timer = setTimeout(() => {
      carregarDocumentos(cliente.id, docBusca);
    }, 250);
    return () => clearTimeout(timer);
  }, [docBusca]);

  async function carregarDocumentos(clienteId, termo = "") {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (termo.trim()) params.set("q", termo.trim());
      const sufixo = params.toString() ? `?${params.toString()}` : "";
      const r = await api.get(`/clientes/${clienteId}/arquivos/${sufixo}`);
      setDocumentos(toList(r.data));
    } catch {
      toast.error("Erro ao carregar documentos do cliente");
      setDocumentos([]);
    } finally {
      setLoading(false);
    }
  }

  function selecionarCliente(c) {
    setCliente(c);
    setQuery(c.nome || "");
    setMostrarLista(false);
    setPreview(null);
    carregarDocumentos(c.id, docBusca);
  }

  async function enviarArquivos() {
    if (!cliente?.id) {
      toast.error("Selecione um cliente");
      return;
    }
    if (!arquivos.length) {
      toast.error("Selecione ao menos um arquivo");
      return;
    }

    const formData = new FormData();
    arquivos.forEach((a) => formData.append("arquivos", a));
    if (meta.template) formData.append("template", meta.template);
    if (meta.titulo) formData.append("titulo", meta.titulo);
    if (meta.documento_referencia) formData.append("documento_referencia", meta.documento_referencia);
    if (meta.categoria) formData.append("categoria", meta.categoria);
    if (meta.descricao) formData.append("descricao", meta.descricao);

    setUploading(true);
    try {
      await api.post(`/clientes/${cliente.id}/arquivos/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Documentos do cliente enviados");
      setArquivos([]);
      setMeta({ template: "", titulo: "", documento_referencia: "", categoria: "", descricao: "" });
      await carregarDocumentos(cliente.id, docBusca);
    } catch {
      toast.error("Falha ao enviar documentos do cliente");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="card space-y-4">
      <div>
        <h3 className="text-base font-semibold text-gray-800">Documentos Clientes</h3>
        <p className="text-xs text-gray-500 mt-1">
          Busca por cliente, versionamento automático, templates e busca por metadados.
        </p>
      </div>

      <div className="relative">
        <label className="label">Buscar Cliente</label>
        <input
          className="input"
          placeholder="Digite nome, CPF/CNPJ..."
          value={query}
          onFocus={() => setMostrarLista(true)}
          onChange={(e) => {
            setQuery(e.target.value);
            setMostrarLista(true);
          }}
        />
        {mostrarLista && resultados.length > 0 && (
          <ul className="absolute z-20 mt-1 w-full max-h-56 overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg text-sm">
            {resultados.map((c) => (
              <li
                key={c.id}
                className="px-3 py-2 hover:bg-primary-50 cursor-pointer"
                onMouseDown={() => selecionarCliente(c)}
              >
                <div className="font-medium">{c.nome}</div>
                <div className="text-xs text-gray-400">{c.cpf_cnpj || "-"}</div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm">
        <div><strong>Cliente selecionado:</strong> {cliente?.nome || "-"}</div>
        <div className="text-xs text-gray-500 mt-1">CPF/CNPJ: {cliente?.cpf_cnpj || "-"}</div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label className="label">Template</label>
          <select className="input" value={meta.template} onChange={(e) => setMeta({ ...meta, template: e.target.value })}>
            <option value="">Sem template</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>{t.nome}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Título</label>
          <input className="input" value={meta.titulo} onChange={(e) => setMeta({ ...meta, titulo: e.target.value })} />
        </div>
        <div>
          <label className="label">Referência Documento</label>
          <input className="input" value={meta.documento_referencia} onChange={(e) => setMeta({ ...meta, documento_referencia: e.target.value })} placeholder="Ex.: contrato_social" />
        </div>
        <div>
          <label className="label">Categoria</label>
          <input className="input" value={meta.categoria} onChange={(e) => setMeta({ ...meta, categoria: e.target.value })} />
        </div>
      </div>

      <div>
        <label className="label">Descrição</label>
        <textarea className="input" rows={2} value={meta.descricao} onChange={(e) => setMeta({ ...meta, descricao: e.target.value })} />
      </div>

      <div>
        <label className="label">Upload múltiplo</label>
        <input
          type="file"
          multiple
          className="input"
          onChange={(e) => setArquivos(Array.from(e.target.files || []))}
        />
        <p className="text-xs text-gray-500 mt-1">{arquivos.length} arquivo(s) selecionado(s)</p>
      </div>

      <button onClick={enviarArquivos} disabled={uploading} className="btn-primary w-full">
        {uploading ? "Enviando..." : "Enviar Documentos do Cliente"}
      </button>

      <div>
        <div className="flex items-end justify-between gap-3 mb-2">
          <h4 className="text-sm font-semibold text-gray-800">Documentos vinculados</h4>
          <input
            className="input max-w-xs"
            placeholder="Buscar por nome, versão, template..."
            value={docBusca}
            onChange={(e) => setDocBusca(e.target.value)}
          />
        </div>
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {loading ? (
            <p className="text-sm text-gray-400">Carregando...</p>
          ) : documentos.length === 0 ? (
            <p className="text-sm text-gray-400">Nenhum documento encontrado para este cliente.</p>
          ) : (
            documentos.map((d) => (
              <div key={d.id} className="rounded-lg border border-gray-200 p-2 text-sm flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="font-medium truncate">{docName(d)} <span className="text-xs text-gray-400">v{d.versao || 1}</span></div>
                  <div className="text-xs text-gray-500 truncate">Ref: {d.documento_referencia || "-"} • Template: {d.template_nome_resolvido || "-"}</div>
                  <div className="text-xs text-gray-400">{fmtDate(d.criado_em)}</div>
                </div>
                <button
                  className="btn-secondary text-xs px-3 py-1"
                  onClick={() => setPreview({ nome: docName(d), url: buildPreviewUrl(d.arquivo_url || d.arquivo) })}
                >
                  Visualizar
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function ProcessoDocs({ setPreview }) {
  const [query, setQuery] = useState("");
  const [resultados, setResultados] = useState([]);
  const [mostrarLista, setMostrarLista] = useState(false);
  const [processo, setProcesso] = useState(null);
  const [documentos, setDocumentos] = useState([]);
  const [arquivos, setArquivos] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [docBusca, setDocBusca] = useState("");
  const [meta, setMeta] = useState({
    template: "",
    titulo: "",
    documento_referencia: "",
    categoria: "",
    descricao: "",
  });
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    api
      .get("/processos/documentos-templates/")
      .then((r) => setTemplates(toList(r.data)))
      .catch(() => setTemplates([]));
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      const params = new URLSearchParams();
      if (query.trim()) params.set("search", query.trim());
      params.set("limit", "20");
      api
        .get(`/processos/?${params.toString()}`)
        .then((r) => setResultados(toList(r.data)))
        .catch(() => setResultados([]));
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    if (!processo?.id) return;
    const timer = setTimeout(() => {
      carregarDocumentos(processo.id, docBusca);
    }, 250);
    return () => clearTimeout(timer);
  }, [docBusca]);

  async function carregarDocumentos(processoId, termo = "") {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (termo.trim()) params.set("q", termo.trim());
      const sufixo = params.toString() ? `?${params.toString()}` : "";
      const r = await api.get(`/processos/${processoId}/arquivos/${sufixo}`);
      setDocumentos(toList(r.data));
    } catch {
      toast.error("Erro ao carregar documentos do processo");
      setDocumentos([]);
    } finally {
      setLoading(false);
    }
  }

  function selecionarProcesso(p) {
    setProcesso(p);
    setQuery(p.numero || "");
    setMostrarLista(false);
    setPreview(null);
    carregarDocumentos(p.id, docBusca);
  }

  async function enviarArquivos() {
    if (!processo?.id) {
      toast.error("Selecione um processo");
      return;
    }
    if (!arquivos.length) {
      toast.error("Selecione ao menos um arquivo");
      return;
    }

    const formData = new FormData();
    arquivos.forEach((a) => formData.append("arquivos", a));
    if (meta.template) formData.append("template", meta.template);
    if (meta.titulo) formData.append("titulo", meta.titulo);
    if (meta.documento_referencia) formData.append("documento_referencia", meta.documento_referencia);
    if (meta.categoria) formData.append("categoria", meta.categoria);
    if (meta.descricao) formData.append("descricao", meta.descricao);

    setUploading(true);
    try {
      await api.post(`/processos/${processo.id}/arquivos/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Documentos do processo enviados");
      setArquivos([]);
      setMeta({ template: "", titulo: "", documento_referencia: "", categoria: "", descricao: "" });
      await carregarDocumentos(processo.id, docBusca);
    } catch {
      toast.error("Falha ao enviar documentos do processo");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="card space-y-4">
      <div>
        <h3 className="text-base font-semibold text-gray-800">Documentos Processos</h3>
        <p className="text-xs text-gray-500 mt-1">
          Busca por processo, versionamento automático, templates e busca por metadados.
        </p>
      </div>

      <div className="relative">
        <label className="label">Buscar Processo</label>
        <input
          className="input"
          placeholder="Digite número do processo ou cliente..."
          value={query}
          onFocus={() => setMostrarLista(true)}
          onChange={(e) => {
            setQuery(e.target.value);
            setMostrarLista(true);
          }}
        />
        {mostrarLista && resultados.length > 0 && (
          <ul className="absolute z-20 mt-1 w-full max-h-56 overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg text-sm">
            {resultados.map((p) => (
              <li
                key={p.id}
                className="px-3 py-2 hover:bg-primary-50 cursor-pointer"
                onMouseDown={() => selecionarProcesso(p)}
              >
                <div className="font-mono text-xs font-semibold">{p.numero}</div>
                <div className="text-xs text-gray-500">Cliente: {p.cliente_nome || "-"}</div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm">
        <div><strong>Processo selecionado:</strong> {processo?.numero || "-"}</div>
        <div className="text-xs text-gray-500 mt-1">Cliente atrelado: {processo?.cliente_nome || "-"}</div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label className="label">Template</label>
          <select className="input" value={meta.template} onChange={(e) => setMeta({ ...meta, template: e.target.value })}>
            <option value="">Sem template</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>{t.nome}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Título</label>
          <input className="input" value={meta.titulo} onChange={(e) => setMeta({ ...meta, titulo: e.target.value })} />
        </div>
        <div>
          <label className="label">Referência Documento</label>
          <input className="input" value={meta.documento_referencia} onChange={(e) => setMeta({ ...meta, documento_referencia: e.target.value })} placeholder="Ex.: peticao_inicial" />
        </div>
        <div>
          <label className="label">Categoria</label>
          <input className="input" value={meta.categoria} onChange={(e) => setMeta({ ...meta, categoria: e.target.value })} />
        </div>
      </div>

      <div>
        <label className="label">Descrição</label>
        <textarea className="input" rows={2} value={meta.descricao} onChange={(e) => setMeta({ ...meta, descricao: e.target.value })} />
      </div>

      <div>
        <label className="label">Upload múltiplo</label>
        <input
          type="file"
          multiple
          className="input"
          onChange={(e) => setArquivos(Array.from(e.target.files || []))}
        />
        <p className="text-xs text-gray-500 mt-1">{arquivos.length} arquivo(s) selecionado(s)</p>
      </div>

      <button onClick={enviarArquivos} disabled={uploading} className="btn-primary w-full">
        {uploading ? "Enviando..." : "Enviar Documentos do Processo"}
      </button>

      <div>
        <div className="flex items-end justify-between gap-3 mb-2">
          <h4 className="text-sm font-semibold text-gray-800">Documentos vinculados</h4>
          <input
            className="input max-w-xs"
            placeholder="Buscar por nome, versão, template..."
            value={docBusca}
            onChange={(e) => setDocBusca(e.target.value)}
          />
        </div>
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {loading ? (
            <p className="text-sm text-gray-400">Carregando...</p>
          ) : documentos.length === 0 ? (
            <p className="text-sm text-gray-400">Nenhum documento encontrado para este processo.</p>
          ) : (
            documentos.map((d) => (
              <div key={d.id} className="rounded-lg border border-gray-200 p-2 text-sm flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="font-medium truncate">{docName(d)} <span className="text-xs text-gray-400">v{d.versao || 1}</span></div>
                  <div className="text-xs text-gray-500 truncate">Ref: {d.documento_referencia || "-"} • Template: {d.template_nome_resolvido || "-"}</div>
                  <div className="text-xs text-gray-400">{fmtDate(d.criado_em)}</div>
                </div>
                <button
                  className="btn-secondary text-xs px-3 py-1"
                  onClick={() => setPreview({ nome: docName(d), url: buildPreviewUrl(d.arquivo_url || d.arquivo) })}
                >
                  Visualizar
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default function Documentos() {
  const [tab, setTab] = useState("clientes");
  const [preview, setPreview] = useState(null);

  useEffect(() => {
    setPreview(null);
  }, [tab]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">📂 Documentos</h1>
        <p className="text-sm text-gray-500 mt-1">
          Área centralizada de upload e visualização com versionamento, templates e busca de documentos.
        </p>
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="flex border-b bg-gray-50">
          <button
            className={`px-4 py-3 text-sm font-medium ${tab === "clientes" ? "bg-white border-b-2 border-primary-600 text-primary-700" : "text-gray-500 hover:text-gray-700"}`}
            onClick={() => setTab("clientes")}
          >
            Documentos Clientes
          </button>
          <button
            className={`px-4 py-3 text-sm font-medium ${tab === "processos" ? "bg-white border-b-2 border-primary-600 text-primary-700" : "text-gray-500 hover:text-gray-700"}`}
            onClick={() => setTab("processos")}
          >
            Documentos Processos
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div className="xl:col-span-1">
            {tab === "clientes" ? (
              <ClienteDocs setPreview={setPreview} />
            ) : (
              <ProcessoDocs setPreview={setPreview} />
            )}
          </div>
          <div className="xl:col-span-1">
            <PreviewPanel preview={preview} />
          </div>
        </div>
      </div>
    </div>
  );
}
