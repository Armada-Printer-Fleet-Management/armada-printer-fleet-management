import type { User } from 'oidc-client-ts';
import {
  createContext,
  ReactNode,
  useState,
  useEffect,
  useMemo,
  useContext,
} from 'react';
import { userManager } from './auth';

interface AuthState {
  user: User | null;
  loading: boolean;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
}
const AuthContext = createContext<AuthState | undefined>(undefined);

async function signIn(): Promise<void> {
  await userManager.signinRedirect({
    state: window.location.pathname + window.location.search,
  });
}

async function signOut(): Promise<void> {
  await userManager.signoutRedirect();
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let cancelled = false;
    const onLoaded = (loaded: User) => setUser(loaded);
    const onUnloaded = () => setUser(null);
    userManager.events.addUserLoaded(onLoaded);
    userManager.events.addUserUnloaded(onUnloaded);

    void userManager
      .getUser()
      .then((stored) => {
        if (!cancelled) setUser(stored);
      })
      .catch(() => {
        // A stored session that cannot be read counts as signed out.
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      userManager.events.removeUserLoaded(onLoaded);
      userManager.events.removeUserUnloaded(onUnloaded);
    };
  }, []);

  const value = useMemo(
    () => ({ user, loading, signIn, signOut }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
