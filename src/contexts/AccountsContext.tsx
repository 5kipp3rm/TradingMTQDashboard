import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { accountsApi } from "@/lib/api";

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
  refreshAccounts: () => Promise<void>;
  isLoading: boolean;
}

const AccountsContext = createContext<AccountsContextType | undefined>(undefined);

export function AccountsProvider({ children }: { children: ReactNode }) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState("all");
  const [isLoading, setIsLoading] = useState(true);

  const refreshAccounts = async () => {
    setIsLoading(true);
    const response = await accountsApi.getAll();
    if (response.data) {
      const formattedAccounts = (response.data as any).accounts?.map((acc: any) => ({
        id: acc.id.toString(),
        name: acc.account_name || `Account ${acc.account_number}`,
        broker: acc.broker || "Unknown",
        balance: acc.balance,
        equity: acc.equity,
        isActive: acc.is_active,
      })) || [];
      setAccounts(formattedAccounts);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    refreshAccounts();
  }, []);

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
        refreshAccounts,
        isLoading,
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
