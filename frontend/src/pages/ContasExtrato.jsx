import { useState, useEffect } from "react";
import api from "../api/axios";
import toast from "react-hot-toast";

function fmtBRL(v) {
  return Number(v || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
function fmtDate(d) {
  if (!d) return "—";
  return new Date(d + "T00:00:00").toLocaleDateString("pt-BR");
}

// Modal Nova Conta
function ModalNovaConta({ onClose, onSaved }) {
  const [form, setForm] = useState({ nome: "", banco: "", agencia: "", conta_numero: "", saldo_inicial: "0" });
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/financeiro/contas/", {
        ...form,
        saldo_inicial: parseFloat(form.saldo_inicial.replace(",", ".")) || 0,
      });
      toast.success("Conta criada!");
      onSaved();
    } catch {
      toast.error("Erro ao criar conta");
    } finally {
      setSaving(false);
    }
  }

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })); }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Nova Conta Bancária</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="label">Nome da Conta *</label>
            <input className="input" value={form.nome} onChange={(e) => set("nome", e.target.value)} placeholder="ex: Conta Corrente Itaú" required />
          </div>
          <div>
            <label className="label">Banco</label>
            <input className="input" value={form.banco} onChange={(e) => set("banco", e.target.value)} placeholder="ex: Itaú" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Agência</label>
              <input className="input" value={form.agencia} onChange={(e) => set("agencia", e.target.value)} />
            </div>
            <div>
              <label className="label">Nº da Conta</label>
              <input className="input" value={form.conta_numero} onChange={(e) => set("conta_numero", e.target.value)} />
            </div>
          </div>
          <div>
            <label className="label">Saldo Inicial (R$)</label>
            <input className="input" type="number" step="0.01" value={form.saldo_inicial} onChange={(e) => set("saldo_inicial", e.target.value)} />
          </div>
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary flex-1">
              {saving ? "Salvando..." : "Criar Conta"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function ContasExtrato() {
  const [contas, setContas] = useState([]);
  const [contaSel, setContaSel] = useState(null);
  const [extrato, setExtrato] = useState([]);
  const [loadingContas, setLoadingContas] = useState(true);
  const [loadingExtrato, setLoadingExtrato] = useState(false);
  const [modalNova, setModalNova] = useState(false);

  function fetchContas() {
    setLoadingContas(true);
    api
      .get("/financeiro/contas/")
      .then((r) => {
        const list = r.data?.results ?? r.data ?? [];
        setContas(list);
        if (list.length > 0 && !contaSel) setContaSel(list[0]);
      })
      .catch(() => toast.error("Erro ao carregar contas"))
      .finally(() => setLoadingContas(false));
  }

  useEffect(() => {
    fetchContas();
  }, []);

  useEffect(() => {
    if (!contaSel) return;
    setLoadingExtrato(true);
    api
      .get(`/financeiro/contas/${contaSel.id}/extrato/`)
      .then((r) => setExtrato(r.data?.extrato ?? r.data ?? []))
      .catch(() => toast.error("Erro ao carregar extrato"))
      .finally(() => setLoadingExtrato(false));
  }, [contaSel]);

  const saldoTotal = contas.reduce((s, c) => s + Number(c.saldo || 0), 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🏦 Contas & Extrato</h1>
          <p className="text-sm text-gray-500 mt-1">Saldo total: <span className="font-semibold text-blue-600">{fmtBRL(saldoTotal)}</span></p>
        </div>
        <button onClick={() => setModalNova(true)} className="btn-primary text-sm">
          + Nova Conta
        </button>
      </div>

      <div className="flex gap-6 h-full">
        {/* Sidebar Contas */}
        <div className="w-72 shrink-0 space-y-2">
          {loadingContas ? (
            <div className="text-sm text-gray-400 animate-pulse p-4">Carregando contas...</div>
          ) : contas.length === 0 ? (
            <div className="card text-sm text-gray-400 text-center py-8">
              Nenhuma conta cadastrada
              <br />
              <button onClick={() => setModalNova(true)} className="text-primary-600 hover:underline mt-2 block">
                + Criar conta
              </button>
            </div>
          ) : (
            contas.map((c) => (
              <button
                key={c.id}
                onClick={() => setContaSel(c)}
                className={`w-full text-left rounded-xl border p-4 transition-all ${
                  contaSel?.id === c.id
                    ? "border-primary-500 bg-primary-50 shadow-sm"
                    : "border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-semibold text-gray-800 text-sm">{c.nome}</div>
                    {c.banco && <div className="text-xs text-gray-500 mt-0.5">{c.banco}</div>}
                    {c.agencia && (
                      <div className="text-xs text-gray-400">
                        Ag. {c.agencia} · C/C {c.conta_numero}
                      </div>
                    )}
                  </div>
                  <span className="text-lg">🏦</span>
                </div>
                <div className={`mt-3 font-bold text-base ${Number(c.saldo) >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {fmtBRL(c.saldo)}
                </div>
              </button>
            ))
          )}
        </div>

        {/* Extrato */}
        <div className="flex-1">
          {!contaSel ? (
            <div className="card text-center text-gray-400 py-16">
              Selecione uma conta para ver o extrato
            </div>
          ) : (
            <div className="card p-0 overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50">
                <div>
                  <h2 className="font-semibold text-gray-800">{contaSel.nome}</h2>
                  <p className="text-xs text-gray-500">Extrato de lançamentos pagos</p>
                </div>
                <span className={`font-bold text-lg ${Number(contaSel.saldo) >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {fmtBRL(contaSel.saldo)}
                </span>
              </div>

              {loadingExtrato ? (
                <div className="text-center py-16 text-gray-400 animate-pulse">Carregando extrato...</div>
              ) : extrato.length === 0 ? (
                <div className="text-center py-16 text-gray-400">Nenhum lançamento registrado nesta conta</div>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {extrato.map((item, i) => (
                    <li key={item.id ?? i} className="flex items-start gap-4 px-5 py-4 hover:bg-gray-50 transition-colors">
                      {/* Linha do tempo */}
                      <div className="flex flex-col items-center mt-1">
                        <span
                          className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0 ${
                            item.tipo === "receita" ? "bg-green-500" : "bg-red-500"
                          }`}
                        >
                          {item.tipo === "receita" ? "+" : "−"}
                        </span>
                        {i < extrato.length - 1 && (
                          <div className="w-px flex-1 bg-gray-200 mt-1 min-h-4" />
                        )}
                      </div>

                      {/* Conteúdo */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <div className="font-medium text-gray-800 text-sm truncate">{item.descricao}</div>
                            <div className="text-xs text-gray-400 mt-0.5">
                              {item.categoria_nome && <span>{item.categoria_nome} · </span>}
                              {item.cliente_nome && <span>{item.cliente_nome} · </span>}
                              {fmtDate(item.data_pagamento)}
                            </div>
                          </div>
                          <span
                            className={`font-bold text-sm shrink-0 ${
                              item.tipo === "receita" ? "text-green-600" : "text-red-600"
                            }`}
                          >
                            {item.tipo === "receita" ? "+" : "-"}
                            {fmtBRL(item.valor)}
                          </span>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </div>

      {modalNova && (
        <ModalNovaConta
          onClose={() => setModalNova(false)}
          onSaved={() => { setModalNova(false); fetchContas(); }}
        />
      )}
    </div>
  );
}
