import { createContext, useContext, useState, ReactNode } from "react";

export interface Account {
  id: string;
  name: string;
  broker: string;
  balance?: number;
  equity?: number;
  isActive: boolean;
}

interface AccountsContextType {
  accounts: Account[];
  selectedAccountId: string;
  setSelectedAccountId: (id: string) => void;
  addAccount: (account: Account) => void;
  updateAccount: (id: string, account: Partial<Account>) => void;
  deleteAccount: (id: string) => void;
}

const AccountsContext = createContext<AccountsContextType | undefined>(undefined);

const mockAccounts: Account[] = [
  { id: "1", name: "Main Trading", broker: "IC Markets", balance: 10500.50, equity: 10750.25, isActive: true },
  { id: "2", name: "Scalping Account", broker: "Pepperstone", balance: 5200.00, equity: 5180.75, isActive: true },
  { id: "3", name: "Swing Trading", broker: "OANDA", balance: 25000.00, equity: 25500.00, isActive: false },
];

export function AccountsProvider({ children }: { children: ReactNode }) {
  const [accounts, setAccounts] = useState<Account[]>(mockAccounts);
  const [selectedAccountId, setSelectedAccountId] = useState("all");

  const addAccount = (account: Account) => {
    setAccounts((prev) => [...prev, account]);
  };

  const updateAccount = (id: string, updates: Partial<Account>) => {
    setAccounts((prev) =>
      prev.map((acc) => (acc.id === id ? { ...acc, ...updates } : acc))
    );
  };

  const deleteAccount = (id: string) => {
    setAccounts((prev) => prev.filter((acc) => acc.id !== id));
  };

  return (
    <AccountsContext.Provider
      value={{
        accounts,
        selectedAccountId,
        setSelectedAccountId,
        addAccount,
        updateAccount,
        deleteAccount,
      }}
    >
      {children}
    </AccountsContext.Provider>
  );
}

export function useAccounts() {
  const context = useContext(AccountsContext);
  if (context === undefined) {
    throw new Error("useAccounts must be used within an AccountsProvider");
  }
  return context;
}
