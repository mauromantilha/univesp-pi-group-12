import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "/api/v1";

const api = axios.create({ baseURL: API_BASE });
let isReportingFrontendError = false;

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config || {};
    const requestUrl = original?.url || "";
    const status = error.response?.status;

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const res = await axios.post(`${API_BASE}/auth/refresh/`, { refresh });
          localStorage.setItem("access_token", res.data.access);
          original.headers.Authorization = `Bearer ${res.data.access}`;
          return api(original);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
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
      const token = localStorage.getItem("access_token");
      if (token) {
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
              headers: {
                Authorization: `Bearer ${token}`,
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
    }

    return Promise.reject(error);
  }
);

export default api;
