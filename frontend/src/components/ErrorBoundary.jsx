import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error("ErrorBoundary capturou erro:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-6">
          <div className="max-w-lg w-full rounded-xl border border-red-200 bg-white p-6">
            <h1 className="text-lg font-semibold text-red-700">Erro inesperado na interface</h1>
            <p className="text-sm text-gray-600 mt-2">
              A tela encontrou um erro e foi interrompida para evitar comportamento inconsistente.
            </p>
            <button
              className="btn-primary mt-4"
              onClick={() => window.location.reload()}
            >
              Recarregar aplicação
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
