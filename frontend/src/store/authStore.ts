import { create } from 'zustand';

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  setToken: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('quantx_token'),
  isAuthenticated: !!localStorage.getItem('quantx_token'),
  setToken: (token: string) => {
    localStorage.setItem('quantx_token', token);
    set({ token, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem('quantx_token');
    set({ token: null, isAuthenticated: false });
  },
}));
