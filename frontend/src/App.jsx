import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Processos from "./pages/Processos";
import ProcessoDetail from "./pages/ProcessoDetail";
import Clientes from "./pages/Clientes";
import Agenda from "./pages/Agenda";
import Jurisprudencia from "./pages/Jurisprudencia";
import IAPreditiva from "./pages/IAPreditiva";
import DashboardFinanceiro from "./pages/DashboardFinanceiro";
import Lancamentos from "./pages/Lancamentos";
import ContasExtrato from "./pages/ContasExtrato";

function PrivateRoute({ children }) {
  const { token } = useAuth();
  return token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="processos" element={<Processos />} />
          <Route path="processos/:id" element={<ProcessoDetail />} />
          <Route path="clientes" element={<Clientes />} />
          <Route path="agenda" element={<Agenda />} />
          <Route path="jurisprudencia" element={<Jurisprudencia />} />
          <Route path="ia" element={<IAPreditiva />} />
          <Route path="financeiro" element={<DashboardFinanceiro />} />
          <Route path="financeiro/lancamentos" element={<Lancamentos />} />
          <Route path="financeiro/contas" element={<ContasExtrato />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
