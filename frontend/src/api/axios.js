import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "/api/v1";

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
});
let isReportingFrontendError = false;

function isAuthBootstrapRequest(url = "") {
  const normalized = String(url || "");
  return (
    normalized.includes("/auth/login/") ||
    normalized.includes("/auth/refresh/") ||
    normalized.includes("/auth/logout/") ||
    normalized.includes("/usuarios/me/")
  );
}

function isLoginPath(pathname = "") {
  return pathname === "/login" || pathname.startsWith("/login/") || pathname === "/accounts/login" || pathname.startsWith("/accounts/login/");
}

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config || {};
    const requestUrl = original?.url || "";
    const status = error.response?.status;
    const authBootstrap = isAuthBootstrapRequest(requestUrl);
    const onLoginScreen = isLoginPath(window.location.pathname);

    if (status === 401 && !original._retry && !authBootstrap) {
      original._retry = true;
      try {
        await axios.post(
          `${API_BASE}/auth/refresh/`,
          {},
          {
            withCredentials: true,
            headers: {
              "X-Skip-Error-Log": "1",
            },
          }
        );
        return api(original);
      } catch {
        if (!onLoginScreen) {
          window.location.replace("/login");
        }
      }
    }

    const skipLog = original?.headers?.["X-Skip-Error-Log"];
    const shouldReport =
      !skipLog &&
      !isReportingFrontendError &&
      !requestUrl.includes("/ia/analises/registrar-erro/") &&
      (status >= 500 || !status);

    if (shouldReport) {
      try {
        isReportingFrontendError = true;
        await axios.post(
          `${API_BASE}/ia/analises/registrar-erro/`,
          {
            tipo: "frontend",
            severidade: "alerta",
            mensagem: `Erro HTTP ${status || "network"} no frontend`,
            rota: requestUrl || window.location.pathname,
            detalhes: {
              method: original?.method,
              status: status || null,
              response_data: error.response?.data || null,
            },
          },
          {
            withCredentials: true,
            headers: {
              "X-Skip-Error-Log": "1",
            },
          }
        );
      } catch {
        // Silencioso: não quebrar o fluxo principal por falha no monitoramento.
      } finally {
        isReportingFrontendError = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
