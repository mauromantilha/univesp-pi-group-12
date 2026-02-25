import { useState, useEffect } from "react";
import { toast } from "react-hot-toast";
import api from "../api/axios";

export default function ConsultaTribunais() {
  const [tribunais, setTribunais] = useState([]);
  const [consultas, setConsultas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [consultaSelecionada, setConsultaSelecionada] = useState(null);
  const [pergunta, setPergunta] = useState("");
  const [tipoBusca, setTipoBusca] = useState("numero"); // "numero" ou "avancado"
  const [resultadosBusca, setResultadosBusca] = useState([]);
  
  const [form, setForm] = useState({
    tribunal_id: "",
    numero_processo: "",
    classe: "",
    orgao_julgador: "",
    assunto: "",
    data_inicio: "",
    data_fim: "",
    analisar_com_ia: true,
  });

  useEffect(() => {
    carregarTribunais();
    carregarConsultas();
  }, []);

  async function carregarTribunais() {
    try {
      const { data } = await api.get("/tribunais/");
      setTribunais(data.results || []);
    } catch (err) {
      toast.error("Erro ao carregar tribunais");
    }
  }

  async function carregarConsultas() {
    try {
      const { data } = await api.get("/consultas-processos/");
      setConsultas(data.results || []);
    } catch (err) {
      console.error("Erro ao carregar consultas:", err);
    }
  }

  async function handleConsultar(e) {
    e.preventDefault();
    
    if (!form.tribunal_id) {
      toast.error("Selecione um tribunal");
      return;
    }

    if (tipoBusca === "numero" && !form.numero_processo) {
      toast.error("Informe o número do processo");
      return;
    }

    setLoading(true);
    try {
      if (tipoBusca === "avancado") {
        // Busca avançada
        const filtros = {};
        if (form.classe) filtros.classe = form.classe;
        if (form.orgao_julgador) filtros.orgao_julgador = form.orgao_julgador;
        if (form.assunto) filtros.assunto = form.assunto;
        if (form.data_inicio) filtros.data_inicio = form.data_inicio.replace(/-/g, '');
        if (form.data_fim) filtros.data_fim = form.data_fim.replace(/-/g, '');
        
        if (Object.keys(filtros).length === 0) {
          toast.error("Preencha pelo menos um filtro de busca");
          setLoading(false);
          return;
        }
        
        const { data } = await api.post("/consultas-processos/buscar_avancado/", {
          tribunal_id: form.tribunal_id,
          ...filtros,
          max_results: 20
        });
        
        setResultadosBusca(data.processos || []);
        toast.success(`${data.total} processo(s) encontrado(s)`);
        
        if (data.aviso) {
          toast(data.aviso, { icon: 'ℹ️', duration: 5000 });
        }
      } else {
        // Busca por número
        const { data } = await api.post("/consultas-processos/consultar/", {
          tribunal_id: form.tribunal_id,
          numero_processo: form.numero_processo,
          analisar_com_ia: form.analisar_com_ia
        });
        
        toast.success("Consulta realizada com sucesso!");
        setConsultaSelecionada(data);
        setResultadosBusca([]);
        carregarConsultas();
        setForm({ ...form, numero_processo: "" });
      }
    } catch (err) {
      const msg = err.response?.data?.error || "Erro ao consultar";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  async function consultarProcessoEspecifico(numeroProcesso) {
    setLoading(true);
    try {
      const { data } = await api.post("/consultas-processos/consultar/", {
        tribunal_id: form.tribunal_id,
        numero_processo: numeroProcesso,
        analisar_com_ia: form.analisar_com_ia
      });
      
      toast.success("Consulta realizada com sucesso!");
      setConsultaSelecionada(data);
      setResultadosBusca([]);
      carregarConsultas();
    } catch (err) {
      const msg = err.response?.data?.error || "Erro ao consultar processo";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handlePergunta(e) {
    e.preventDefault();
    
    if (!pergunta.trim()) {
      toast.error("Digite uma pergunta");
      return;
    }

    try {
      const { data } = await api.post(
        `/consultas-processos/${consultaSelecionada.id}/fazer_pergunta/`,
        { pergunta }
      );
      
      // Atualiza a consulta com a nova pergunta
      setConsultaSelecionada({
        ...consultaSelecionada,
        perguntas: [...(consultaSelecionada.perguntas || []), data]
      });
      
      setPergunta("");
      toast.success("Pergunta respondida!");
    } catch (err) {
      const msg = err.response?.data?.error || "Erro ao processar pergunta";
      toast.error(msg);
    }
  }

  function formatarData(data) {
    return new Date(data).toLocaleString("pt-BR");
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <span className="text-3xl">🏛️</span>
          Consulta de Tribunais
        </h1>
        <p className="text-gray-600 mt-2">
          Consulte processos diretamente nos tribunais e obtenha análises inteligentes com IA
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Formulário de Consulta */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Nova Consulta</h2>
          
          <form onSubmit={handleConsultar} className="space-y-4">
            <div>
              <label className="label">Tribunal</label>
              <select
                className="input"
                value={form.tribunal_id}
                onChange={(e) => setForm({ ...form, tribunal_id: e.target.value })}
                required
              >
                <option value="">Selecione...</option>
                {tribunais.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.sigla} - {t.nome}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Tipo de Busca</label>
              <div className="flex gap-4 mb-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="tipoBusca"
                    value="numero"
                    checked={tipoBusca === "numero"}
                    onChange={(e) => setTipoBusca(e.target.value)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">Por Número do Processo</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="tipoBusca"
                    value="avancado"
                    checked={tipoBusca === "avancado"}
                    onChange={(e) => setTipoBusca(e.target.value)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">Busca Avançada</span>
                </label>
              </div>
            </div>

            {tipoBusca === "numero" ? (
              <div>
                <label className="label">Número do Processo</label>
                <input
                  type="text"
                  className="input"
                  placeholder="0000000-00.0000.5.02.0000"
                  value={form.numero_processo}
                  onChange={(e) => setForm({ ...form, numero_processo: e.target.value })}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Formato CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p className="text-xs text-yellow-800">
                    ℹ️ <strong>Importante:</strong> A API pública do DataJud não possui dados de partes/advogados.
                    Use os filtros abaixo para buscar por classe, órgão, assunto ou período.
                  </p>
                </div>
                
                <div>
                  <label className="label">Classe Processual</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="Ex: Reclamação Trabalhista, Recurso Ordinário"
                    value={form.classe}
                    onChange={(e) => setForm({ ...form, classe: e.target.value })}
                  />
                </div>

                <div>
                  <label className="label">Órgão Julgador</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="Ex: 1ª Vara do Trabalho"
                    value={form.orgao_julgador}
                    onChange={(e) => setForm({ ...form, orgao_julgador: e.target.value })}
                  />
                </div>

                <div>
                  <label className="label">Assunto</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="Ex: Horas Extras, Adicional Noturno"
                    value={form.assunto}
                    onChange={(e) => setForm({ ...form, assunto: e.target.value })}
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="label">Data Inicial</label>
                    <input
                      type="date"
                      className="input"
                      value={form.data_inicio}
                      onChange={(e) => setForm({ ...form, data_inicio: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="label">Data Final</label>
                    <input
                      type="date"
                      className="input"
                      value={form.data_fim}
                      onChange={(e) => setForm({ ...form, data_fim: e.target.value })}
                    />
                  </div>
                </div>
                
                <p className="text-xs text-gray-500">
                  Preencha pelo menos um filtro para realizar a busca
                </p>
              </div>
            )}

            {tipoBusca === "numero" && (
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="analisar_ia"
                  checked={form.analisar_com_ia}
                  onChange={(e) => setForm({ ...form, analisar_com_ia: e.target.checked })}
                  className="w-4 h-4"
                />
                <label htmlFor="analisar_ia" className="text-sm text-gray-700">
                  Analisar com Inteligência Artificial
                </label>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full"
            >
              {loading ? "Buscando..." : tipoBusca === "avancado" ? "🔍 Buscar Processos" : "🔍 Consultar Processo"}
            </button>
          </form>
        </div>

        {/* Histórico de Consultas */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Histórico de Consultas</h2>
          
          <div className="space-y-3 max-h-[400px] overflow-y-auto">
            {consultas.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                Nenhuma consulta realizada ainda
              </p>
            ) : (
              consultas.map((c) => (
                <div
                  key={c.id}
                  onClick={() => setConsultaSelecionada(c)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    consultaSelecionada?.id === c.id
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-blue-300"
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <p className="font-semibold text-gray-800">{c.numero_processo}</p>
                      <p className="text-sm text-gray-600">{c.tribunal_nome}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {formatarData(c.data_consulta)}
                      </p>
                    </div>
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        c.status === "sucesso"
                          ? "bg-green-100 text-green-800"
                          : c.status === "erro"
                          ? "bg-red-100 text-red-800"
                          : "bg-yellow-100 text-yellow-800"
                      }`}
                    >
                      {c.status_display}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Resultados da Busca por Nome */}
      {resultadosBusca.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">
            📋 Resultados da Busca ({resultadosBusca.length} processo{resultadosBusca.length !== 1 ? 's' : ''})
          </h2>
          
          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {resultadosBusca.map((processo, idx) => (
              <div
                key={idx}
                className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-all"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <p className="font-semibold text-gray-800 mb-2">
                      {processo.numeroProcesso || 'Número não informado'}
                    </p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-600 mb-3">
                      {processo.classe?.nome && (
                        <div>
                          <span className="font-medium">Classe:</span> {processo.classe.nome}
                        </div>
                      )}
                      {processo.orgaoJulgador?.nome && (
                        <div>
                          <span className="font-medium">Órgão:</span> {processo.orgaoJulgador.nome}
                        </div>
                      )}
                      {processo.dataAjuizamento && (
                        <div>
                          <span className="font-medium">Ajuizamento:</span> {processo.dataAjuizamento}
                        </div>
                      )}
                      {processo.valorCausa && (
                        <div>
                          <span className="font-medium">Valor:</span> R$ {processo.valorCausa.toLocaleString('pt-BR')}
                        </div>
                      )}
                    </div>

                    {processo.assuntos && processo.assuntos.length > 0 && (
                      <div className="text-sm mb-2">
                        <span className="font-medium text-gray-700">Assuntos:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {processo.assuntos.slice(0, 3).map((assunto, i) => (
                            <span key={i} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                              {assunto.nome}
                            </span>
                          ))}
                          {processo.assuntos.length > 3 && (
                            <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                              +{processo.assuntos.length - 3}
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <button
                    onClick={() => consultarProcessoEspecifico(processo.numeroProcesso)}
                    className="ml-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
                    disabled={loading}
                  >
                    Analisar
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detalhes da Consulta Selecionada */}
      {consultaSelecionada && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-gray-800">
              Processo: {consultaSelecionada.numero_processo}
            </h2>
            <span
              className={`px-3 py-1 rounded-lg text-sm font-semibold ${
                consultaSelecionada.status === "sucesso"
                  ? "bg-green-100 text-green-800"
                  : consultaSelecionada.status === "erro"
                  ? "bg-red-100 text-red-800"
                  : "bg-yellow-100 text-yellow-800"
              }`}
            >
              {consultaSelecionada.status_display || consultaSelecionada.status}
            </span>
          </div>

          {consultaSelecionada.status === "erro" ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800 font-semibold">❌ Erro na Consulta</p>
              <p className="text-red-700 text-sm mt-1">
                {consultaSelecionada.erro_mensagem || 'Erro desconhecido'}
              </p>
            </div>
          ) : consultaSelecionada.status === "processando" ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-yellow-800 font-semibold">⏳ Processando...</p>
              <p className="text-yellow-700 text-sm mt-1">
                A consulta está sendo processada. Por favor, aguarde.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Dados do Processo */}
              {consultaSelecionada.dados_formatados && (
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-bold text-gray-800 mb-3">📋 Dados do Processo</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Classe:</span>
                      <p className="font-semibold">{consultaSelecionada.dados_formatados.classe}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Órgão Julgador:</span>
                      <p className="font-semibold">{consultaSelecionada.dados_formatados.orgao_julgador}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Data Ajuizamento:</span>
                      <p className="font-semibold">{consultaSelecionada.dados_formatados.data_ajuizamento}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Grau:</span>
                      <p className="font-semibold">{consultaSelecionada.dados_formatados.grau}º Grau</p>
                    </div>
                    {consultaSelecionada.dados_formatados.valor_causa > 0 && (
                      <div>
                        <span className="text-gray-600">Valor da Causa:</span>
                        <p className="font-semibold">
                          R$ {consultaSelecionada.dados_formatados.valor_causa.toLocaleString("pt-BR")}
                        </p>
                      </div>
                    )}
                    {consultaSelecionada.dados_formatados.assuntos?.length > 0 && (
                      <div className="col-span-2">
                        <span className="text-gray-600">Assuntos:</span>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {consultaSelecionada.dados_formatados.assuntos.map((a, i) => (
                            <span key={i} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                              {a}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Análise da IA */}
              {consultaSelecionada.analise_ia && (
                <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                  <h3 className="font-bold text-blue-900 mb-3 flex items-center gap-2">
                    <span className="text-xl">🤖</span>
                    Análise Inteligente
                  </h3>
                  <div className="prose prose-sm max-w-none text-gray-800 whitespace-pre-wrap">
                    {consultaSelecionada.analise_ia}
                  </div>
                  <p className="text-xs text-blue-700 mt-3">
                    Atualizado em: {formatarData(consultaSelecionada.analise_atualizada_em)}
                  </p>
                </div>
              )}

              {/* Chat com IA */}
              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-bold text-gray-800 mb-3">💬 Perguntas sobre o Processo</h3>
                
                {/* Histórico de Perguntas */}
                <div className="space-y-3 mb-4 max-h-[300px] overflow-y-auto">
                  {consultaSelecionada.perguntas?.map((p) => (
                    <div key={p.id} className="space-y-2">
                      <div className="bg-gray-100 rounded-lg p-3">
                        <p className="text-sm text-gray-800 font-semibold">
                          👤 {p.pergunta}
                        </p>
                      </div>
                      <div className="bg-blue-100 rounded-lg p-3">
                        <p className="text-sm text-gray-800">
                          🤖 {p.resposta}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Formulário de Pergunta */}
                <form onSubmit={handlePergunta} className="flex gap-2">
                  <input
                    type="text"
                    className="input flex-1"
                    placeholder="Faça uma pergunta sobre este processo..."
                    value={pergunta}
                    onChange={(e) => setPergunta(e.target.value)}
                  />
                  <button type="submit" className="btn-primary">
                    Enviar
                  </button>
                </form>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
