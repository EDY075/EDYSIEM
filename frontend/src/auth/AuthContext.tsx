import { createContext, type ReactNode, useContext } from "react";
import type { AuthIdentity } from "../api/client";

interface AuthSession {
  identity: AuthIdentity;
  signOut: () => void;
}

const AuthContext = createContext<AuthSession | null>(null);

export function getAuthIdentityPresentation(identity: AuthIdentity) {
  return {
    identityLabel: identity.identity,
    roleLabel: identity.role,
    avatarLabel: identity.identity.trim().charAt(0).toUpperCase() || "?",
  };
}

export function AuthSessionProvider({
  children,
  identity,
  signOut,
}: AuthSession & { children: ReactNode }) {
  return <AuthContext.Provider value={{ identity, signOut }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthSession {
  const session = useContext(AuthContext);
  if (!session) throw new Error("useAuth must be used inside AuthGate");
  return session;
}
