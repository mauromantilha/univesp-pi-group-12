import { useEffect, useMemo, useState } from "react";
import api from "../api/axios";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";

function fmtDateTime(v) {
  if (!v) return "-";
  try {
    return new Date(v).toLocaleString("pt-BR");
  } catch {
    return v;
  }
}

function StatCard({ label, value, color }) {
  const colors = {
    green: "bg-green-50 border-green-200 text-green-700",
    blue: "bg-blue-50 border-blue-200 text-blue-700",
    gray: "bg-gray-50 border-gray-200 text-gray-700",
  };
  return (
    <div className={`card border ${colors[color] || colors.gray}`}>
      <div className="text-3xl font-bold">{value}</div>
      <div className="text-sm font-medium mt-1">{label}</div>
    </div>
  );
}

export default function GestaoUsuarios() {
  const { user } = useAuth();
  const isAdmin = user?.papel === "administrador";

  const [usuarios, setUsuarios] = useState([]);
  const [atividades, setAtividades] = useState([]);
  const [auditoria, setAuditoria] = useState([]);
  const [loading, setLoading] = useState(true);

  async function fetchAll() {
    setLoading(true);
    try {
      const [u, a, l] = await Promise.all([
        api.get("/usuarios/?limit=300"),
        api.get("/usuarios/atividades/?limit=60"),
        api.get("/usuarios/auditoria/?limit=200"),
      ]);
      setUsuarios(u.data?.results || u.data || []);
      setAtividades(a.data || []);
      setAuditoria(l.data || []);
    } catch {
      toast.error("Erro ao carregar gestão de usuários");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchAll();
  }, []);

  const resumo = useMemo(() => {
    const ativos = usuarios.filter((u) => u.is_active).length;
    const inativos = usuarios.filter((u) => !u.is_active).length;
    const advogadosAtivos = usuarios.filter((u) => u.is_active && u.papel === "advogado").length;
    return { ativos, inativos, advogadosAtivos };
  }, [usuarios]);

  if (!isAdmin) {
    return (
      <div className="card">
        <h1 className="text-xl font-semibold text-gray-900">Gestão Usuários</h1>
        <p className="text-sm text-gray-500 mt-2">Acesso restrito ao administrador.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🛡️ Gestão Usuários</h1>
          <p className="text-sm text-gray-500 mt-1">
            Usuários ativos, gerenciamento, atividades e auditoria.
          </p>
        </div>
        <button onClick={fetchAll} className="btn-secondary text-sm">Atualizar</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="Usuários Ativos" value={resumo.ativos} color="green" />
        <StatCard label="Usuários Inativos" value={resumo.inativos} color="gray" />
        <StatCard label="Advogados Ativos" value={resumo.advogadosAtivos} color="blue" />
      </div>

      <div className="card p-0 overflow-x-auto">
        <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-800">Gerenciar Usuários</h2>
          <span className="text-xs text-gray-500">{usuarios.length} usuário(s)</span>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-100">
              <th className="text-left px-4 py-2 text-xs text-gray-500 uppercase">Nome</th>
              <th className="text-left px-4 py-2 text-xs text-gray-500 uppercase">Usuário</th>
              <th className="text-left px-4 py-2 text-xs text-gray-500 uppercase">Papel</th>
              <th className="text-left px-4 py-2 text-xs text-gray-500 uppercase">Email</th>
              <th className="text-left px-4 py-2 text-xs text-gray-500 uppercase">Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="px-4 py-6 text-center text-gray-400">Carregando...</td></tr>
            ) : usuarios.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-6 text-center text-gray-400">Nenhum usuário</td></tr>
            ) : (
              usuarios.map((u) => (
                <tr key={u.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-4 py-2">{`${u.first_name || ""} ${u.last_name || ""}`.trim() || "-"}</td>
                  <td className="px-4 py-2 font-mono text-xs">{u.username}</td>
                  <td className="px-4 py-2">{u.papel_display || u.papel}</td>
                  <td className="px-4 py-2">{u.email || "-"}</td>
                  <td className="px-4 py-2">
                    <span className={u.is_active ? "badge-green" : "badge-gray"}>{u.is_active ? "Ativo" : "Inativo"}</span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="card p-0 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100">
            <h2 className="font-semibold text-gray-800">Mostrar Atividades</h2>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {atividades.length === 0 ? (
              <p className="px-4 py-6 text-sm text-gray-400">Sem atividades recentes.</p>
            ) : (
              atividades.map((a) => (
                <div key={a.id} className="px-4 py-3 border-b border-gray-50 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <span className="badge-blue text-xs">{a.acao_display || a.acao}</span>
                    <span className="text-xs text-gray-400">{fmtDateTime(a.criado_em)}</span>
                  </div>
                  <div className="mt-1 text-gray-700">
                    <strong>Autor:</strong> {a.autor_nome || "Sistema"}
                  </div>
                  <div className="text-gray-700">
                    <strong>Usuário:</strong> {a.usuario_nome || "-"}
                  </div>
                  {a.detalhes && <div className="text-xs text-gray-500 mt-1">{a.detalhes}</div>}
                </div>
              ))
            )}
          </div>
        </div>

        <div className="card p-0 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100">
            <h2 className="font-semibold text-gray-800">Auditoria e Logs dos Usuários</h2>
          </div>
          <div className="max-h-96 overflow-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100">
                  <th className="text-left px-3 py-2 text-xs text-gray-500 uppercase">Data/Hora</th>
                  <th className="text-left px-3 py-2 text-xs text-gray-500 uppercase">Ação</th>
                  <th className="text-left px-3 py-2 text-xs text-gray-500 uppercase">Autor</th>
                  <th className="text-left px-3 py-2 text-xs text-gray-500 uppercase">Usuário</th>
                  <th className="text-left px-3 py-2 text-xs text-gray-500 uppercase">IP</th>
                </tr>
              </thead>
              <tbody>
                {auditoria.length === 0 ? (
                  <tr><td colSpan={5} className="px-3 py-6 text-center text-gray-400">Sem logs de auditoria.</td></tr>
                ) : (
                  auditoria.map((log) => (
                    <tr key={log.id} className="border-b border-gray-50">
                      <td className="px-3 py-2 whitespace-nowrap text-xs">{fmtDateTime(log.criado_em)}</td>
                      <td className="px-3 py-2">{log.acao_display || log.acao}</td>
                      <td className="px-3 py-2">{log.autor_nome || "Sistema"}</td>
                      <td className="px-3 py-2">{log.usuario_nome || "-"}</td>
                      <td className="px-3 py-2 font-mono text-xs">{log.ip_endereco || "-"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
