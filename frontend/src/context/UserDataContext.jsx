import { createContext, useContext, useState } from 'react';

const UserDataContext = createContext(null);

export function UserDataProvider({ children }) {
  const [sleepData, setSleepData] = useState(null);

  return (
    <UserDataContext.Provider value={{ sleepData, setSleepData }}>
      {children}
    </UserDataContext.Provider>
  );
}

export function useUserData() {
  const ctx = useContext(UserDataContext);
  if (!ctx) throw new Error('useUserData must be used within UserDataProvider');
  return ctx;
}
