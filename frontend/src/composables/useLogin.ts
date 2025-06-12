import { useAuth } from '@/composables/useAuth';
import type { UserLogin } from '@/types/api';

export function useLogin() {
  const { login } = useAuth();

  const loginUser = async (email: string, password: string) => {
    const loginData: UserLogin = { email, password };
    return await login(loginData);
  };

  const loginDemo = async () => {
    const demoCredentials: UserLogin = { email: "demo@example.com", password: "demo123" };
    return await login(demoCredentials);
  };

  return { loginUser, loginDemo };
}
