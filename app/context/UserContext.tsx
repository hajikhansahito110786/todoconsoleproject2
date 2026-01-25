// app/context/UserContext.tsx
"use client";

import { createContext, useContext, useState, ReactNode, useEffect } from 'react';

interface UserContextType {
  userEmail: string;
  setUserEmail: (email: string) => void;
  logout: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [userEmail, setUserEmail] = useState('');
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize from localStorage on client side only
  useEffect(() => {
    const storedEmail = localStorage.getItem('userEmail') || '';
    setUserEmail(storedEmail);
    setIsInitialized(true);
  }, []);

  const handleSetUserEmail = (email: string) => {
    setUserEmail(email);
    localStorage.setItem('userEmail', email);
  };

  const logout = () => {
    setUserEmail('');
    localStorage.removeItem('userEmail');
  };

  // Don't render children until initialized to avoid hydration mismatch
  if (!isInitialized) {
    return null; // or a loading spinner
  }

  return (
    <UserContext.Provider value={{ 
      userEmail, 
      setUserEmail: handleSetUserEmail, 
      logout 
    }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}