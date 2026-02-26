import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";
import toast from "react-hot-toast";

function KPICard({ icon, label, value, color = "blue", subtitle, onClick }) {
  const colors = {
    blue:   "bg-blue-50   text-blue-700   border-blue-200",
    green:  "bg-green-50  text-green-700  border-green-200",
    red:    "bg-red-50    text-red-700    border-red-200",
    yellow: "bg-yellow-50 text-yellow-700 border-yellow-200",
  };
  return (
    <div
      onClick={onClick}
      className={`card border ${colors[color]} ${onClick ? "cursor-pointer hover:shadow-md" : ""} transition-shadow`}
    >
      <div className="text-3xl mb-2">{icon}</div>
      <div className="text-2xl font-bold">{value ?? "—"}</div>
      <div className="text-sm font-medium mt-1">{label}</div>
      {subtitle && <div className="text-xs mt-1 opacity-70">{subtitle}</div>}
    </div>
  );
}

function BarChart({ data }) {
  if (!data || data.length === 0) return <p className="text-sm text-gray-400">Sem dados</p>;
  const maxVal = Math.max(...data.flatMap((d) => [d.receitas, d.despesas]), 1);

  return (
    <div className="w-full">
      <div className="flex items-end gap-1 h-40">
        {data.map((d, i) => (
          <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
            <div className="w-full flex gap-0.5 items-end h-32">
              <div
                className="flex-1 bg-green-400 rounded-t transition-all"
                style={{ height: `${(d.receitas / maxVal) * 100}%` }}
                title={`Receitas: R$ ${Number(d.receitas).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`}
              />
              <div
                className="flex-1 bg-red-400 rounded-t transition-all"
                style={{ height: `${(d.despesas / maxVal) * 100}%` }}
                title={`Despesas: R$ ${Number(d.despesas).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`}
              />
            </div>
            <span className="text-xs text-gray-500 truncate w-full text-center">{d.mes}</span>
          </div>
        ))}
      </div>
      <div className="flex gap-4 mt-3 justify-center">
        <span className="flex items-center gap-1 text-xs text-gray-600">
          <span className="w-3 h-3 rounded bg-green-400 inline-block" /> Receitas
        </span>
        <span className="flex items-center gap-1 text-xs text-gray-600">
          <span className="w-3 h-3 rounded bg-red-400 inline-block" /> Despesas
        </span>
      </div>
    </div>
  );
}

function fmtBRL(v) {
  return Number(v || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export default function DashboardFinanceiro() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/financeiro/lancamentos/dashboard/")
      .then((r) => setData(r.data))
      .catch(() => toast.error("Erro ao carregar dashboard financeiro"))
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <div className="flex justify-center items-center h-64">
        <span className="text-gray-400 animate-pulse">Carregando...</span>
      </div>
    );

  const grafico = data?.grafico_6_meses || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">💰 Dashboard Financeiro</h1>
          <p className="text-sm text-gray-500 mt-1">Visão geral das finanças do escritório</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate("/financeiro/lancamentos")}
            className="btn-primary text-sm"
          >
            + Novo Lançamento
          </button>
          <button
            onClick={() => navigate("/financeiro/cobranca")}
            className="btn-secondary text-sm"
          >
            Cobrança & Time
          </button>
          <button
            onClick={() => navigate("/financeiro/contas")}
            className="btn-secondary text-sm"
          >
            Ver Contas
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard
          icon="💳"
          label="Saldo Total"
          value={fmtBRL(data?.saldo_total)}
          color="blue"
          onClick={() => navigate("/financeiro/contas")}
        />
        <KPICard
          icon="📈"
          label="A Receber"
          value={fmtBRL(data?.a_receber_mes)}
          color="green"
          onClick={() => navigate("/financeiro/lancamentos?tipo=receber")}
        />
        <KPICard
          icon="📉"
          label="A Pagar"
          value={fmtBRL(data?.a_pagar_mes)}
          color="red"
          onClick={() => navigate("/financeiro/lancamentos?tipo=pagar")}
        />
        <KPICard
          icon="⚠️"
          label="Atrasados"
          value={fmtBRL(data?.atrasados_valor)}
          color="yellow"
          subtitle={`${data?.atrasados_count || 0} lançamento(s)`}
          onClick={() => navigate("/financeiro/lancamentos?status=atrasado")}
        />
      </div>

      {/* Gráfico + Lançamentos recentes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-base font-semibold text-gray-800 mb-4">📊 Receitas × Despesas — 6 Meses</h2>
          <BarChart data={grafico} />
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-800">🕐 Próximos Vencimentos</h2>
            <button
              onClick={() => navigate("/financeiro/lancamentos")}
              className="text-xs text-primary-600 hover:underline"
            >
              Ver todos →
            </button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-green-50 rounded-lg p-3 text-center">
              <div className="text-xs text-green-600 font-medium">Receitas do Mês</div>
              <div className="text-lg font-bold text-green-700 mt-1">{fmtBRL(data?.receitas_mes)}</div>
            </div>
            <div className="bg-red-50 rounded-lg p-3 text-center">
              <div className="text-xs text-red-600 font-medium">Despesas do Mês</div>
              <div className="text-lg font-bold text-red-700 mt-1">{fmtBRL(data?.despesas_mes)}</div>
            </div>
          </div>
          <div className="mt-4">
            <button
              onClick={() => navigate("/financeiro/lancamentos")}
              className="w-full text-sm text-center text-primary-600 hover:text-primary-700 font-medium py-2 border border-primary-200 rounded-lg hover:bg-primary-50 transition-colors"
            >
              Ver todos os lançamentos →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
