import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Processos from "./pages/Processos";
import ProcessoDetail from "./pages/ProcessoDetail";
import Clientes from "./pages/Clientes";
import ClienteDetail from "./pages/ClienteDetail";
import Agenda from "./pages/Agenda";
import Jurisprudencia from "./pages/Jurisprudencia";
import IAPreditiva from "./pages/IAPreditiva";
import DashboardFinanceiro from "./pages/DashboardFinanceiro";
import Lancamentos from "./pages/Lancamentos";
import ContasExtrato from "./pages/ContasExtrato";
import FinanceiroCobranca from "./pages/FinanceiroCobranca";
import ConsultaTribunais from "./pages/ConsultaTribunais";
import GestaoUsuarios from "./pages/GestaoUsuarios";
import Documentos from "./pages/Documentos";

function PrivateRoute({ children }) {
  const { token, loading } = useAuth();
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-gray-400">Carregando sessão...</div>;
  }
  return token ? children : <Navigate to="/login" replace />;
}

function AppFallbackRoute() {
  const { token, loading } = useAuth();
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-gray-400">Carregando sessão...</div>;
  }
  return <Navigate to={token ? "/dashboard" : "/login"} replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/login/*" element={<Login />} />
        <Route path="/accounts/login" element={<Login />} />
        <Route path="/accounts/login/*" element={<Login />} />
        <Route path="/accounts/logout" element={<AppFallbackRoute />} />
        <Route path="/accounts/logout/*" element={<AppFallbackRoute />} />
        <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="processos" element={<Processos />} />
          <Route path="processos/:id" element={<ProcessoDetail />} />
          <Route path="clientes" element={<Clientes />} />
          <Route path="clientes/:id" element={<ClienteDetail />} />
          <Route path="documentos" element={<Documentos />} />
          <Route path="agenda" element={<Agenda />} />
          <Route path="jurisprudencia" element={<Jurisprudencia />} />
          <Route path="ia" element={<IAPreditiva />} />
          <Route path="consulta-tribunais" element={<ConsultaTribunais />} />
          <Route path="financeiro" element={<DashboardFinanceiro />} />
          <Route path="financeiro/lancamentos" element={<Lancamentos />} />
          <Route path="financeiro/contas" element={<ContasExtrato />} />
          <Route path="financeiro/cobranca" element={<FinanceiroCobranca />} />
          <Route path="gestao-usuarios" element={<GestaoUsuarios />} />
        </Route>
        <Route path="*" element={<AppFallbackRoute />} />
      </Routes>
    </BrowserRouter>
  );
}
