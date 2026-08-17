import { type FormEvent, type ReactNode, useEffect, useState } from "react";
import {
  apiClient,
  hasOperatorApiKey,
  setOperatorApiKey,
  type AuthIdentity,
} from "../api/client";
import { colors } from "../design-system/tokens";
import { AuthSessionProvider } from "./AuthContext";

interface AuthGateProps {
  children: ReactNode;
  language?: string;
}

export function getAuthText(language: string) {
  return language.toLowerCase().startsWith("pt")
    ? {
      title: "Autenticação necessária",
      description: "Informe a chave configurada no arquivo .env local.",
      label: "Chave da API",
      button: "Entrar com segurança",
      checking: "Validando credencial…",
      invalid: "Credencial inválida ou autenticação ainda não configurada.",
      }
    : {
      title: "Authentication required",
      description: "Enter the key configured in the local .env file.",
      label: "API key",
      button: "Sign in securely",
      checking: "Validating credential…",
      invalid: "Invalid credential or operator authentication is not configured.",
      };
}

export function AuthGate({ children, language = navigator.language }: AuthGateProps) {
  const text = getAuthText(language);
  const [identity, setIdentity] = useState<AuthIdentity | null>(null);
  const [key, setKey] = useState("");
  const [checking, setChecking] = useState(hasOperatorApiKey());
  const [error, setError] = useState("");

  async function authenticate(): Promise<boolean> {
    const response = await apiClient.authenticate();
    if (response.success && response.data) {
      setIdentity(response.data);
      setError("");
      return true;
    }
    setOperatorApiKey("");
    setError(text.invalid);
    return false;
  }

  useEffect(() => {
    if (!hasOperatorApiKey()) {
      setChecking(false);
      return;
    }
    void authenticate().finally(() => setChecking(false));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setChecking(true);
    setOperatorApiKey(key);
    await authenticate();
    setChecking(false);
    setKey("");
  }

  function signOut(): void {
    setOperatorApiKey("");
    setIdentity(null);
    setError("");
  }

  if (identity) {
    return (
      <AuthSessionProvider identity={identity} signOut={signOut}>
        {children}
      </AuthSessionProvider>
    );
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: 24,
        background: colors.background,
        color: colors.textPrimary,
      }}
    >
      <form
        onSubmit={(event) => void submit(event)}
        style={{
          width: "min(440px, 100%)",
          padding: 28,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
          background: colors.surface,
          display: "grid",
          gap: 16,
        }}
      >
        <div>
          <h1 style={{ margin: "0 0 8px", fontSize: 24 }}>{text.title}</h1>
          <p style={{ margin: 0, color: colors.textSecondary }}>{text.description}</p>
        </div>
        <label style={{ display: "grid", gap: 8 }}>
          <span>{text.label}</span>
          <input
            type="password"
            autoComplete="current-password"
            value={key}
            onChange={(event) => setKey(event.target.value)}
            minLength={32}
            required
            disabled={checking}
            style={{
              padding: "12px 14px",
              borderRadius: 8,
              border: `1px solid ${colors.border}`,
              background: colors.background,
              color: colors.textPrimary,
            }}
          />
        </label>
        {error ? <p role="alert" style={{ margin: 0, color: colors.danger }}>{error}</p> : null}
        <button
          type="submit"
          disabled={checking || key.trim().length < 32}
          style={{
            padding: "12px 16px",
            border: 0,
            borderRadius: 8,
            background: colors.accent,
            color: colors.textOnAccent,
            fontWeight: 700,
            cursor: checking ? "wait" : "pointer",
          }}
        >
          {checking ? text.checking : text.button}
        </button>
      </form>
    </main>
  );
}
