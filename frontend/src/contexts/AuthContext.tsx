import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

interface AuthContextType {
  isAuthenticated: boolean;
  tenantId: string | null;
  tenantName: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
}

interface AuthProviderProps {
  children: ReactNode;
}

interface JwtPayload {
  sub: string;
  tenant_id: string;
  tenant_name: string;
  exp: number;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  tenantId: null,
  tenantName: null,
  login: async () => false,
  logout: async () => {},
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [tenantName, setTenantName] = useState<string | null>(null);

  useEffect(() => {
    // Check token validity on component mount
    checkTokenValidity();
  }, []);

  const checkTokenValidity = () => {
    const token = localStorage.getItem('authToken');
    if (!token) {
      setIsAuthenticated(false);
      return;
    }

    try {
      const decoded = jwtDecode<JwtPayload>(token);
      const currentTime = Date.now() / 1000;
      
      if (decoded.exp < currentTime) {
        // Token expired
        localStorage.removeItem('authToken');
        setIsAuthenticated(false);
        setTenantId(null);
        setTenantName(null);
      } else {
        // Token valid
        setIsAuthenticated(true);
        setTenantId(decoded.tenant_id);
        setTenantName(decoded.tenant_name);
        
        // Configure axios with the token
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Invalid token:', error);
      localStorage.removeItem('authToken');
      setIsAuthenticated(false);
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await axios.post('/api/auth/login', { email, password });
      const { token } = response.data;
      
      localStorage.setItem('authToken', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      const decoded = jwtDecode<JwtPayload>(token);
      setTenantId(decoded.tenant_id);
      setTenantName(decoded.tenant_name);
      setIsAuthenticated(true);
      
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      setIsAuthenticated(false);
      return false;
    }
  };

  const logout = async (): Promise<void> => {
    localStorage.removeItem('authToken');
    delete axios.defaults.headers.common['Authorization'];
    setIsAuthenticated(false);
    setTenantId(null);
    setTenantName(null);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, tenantId, tenantName, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
