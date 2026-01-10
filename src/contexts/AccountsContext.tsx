import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { apiClient } from "@/lib/api";

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
    try {
      // Use v2 accounts list endpoint
      const response = await apiClient.get("/v2/accounts");
      if (response.data) {
        const data = response.data as any;
        const accounts = data.accounts || [];
        const formattedAccounts = accounts.map((acc: any) => ({
          id: acc.id.toString(),
          name: acc.account_name || `Account ${acc.account_number}`,
          broker: acc.broker || "Unknown",
          balance: acc.initial_balance ? parseFloat(acc.initial_balance) : undefined,
          equity: undefined, // Not available in list endpoint
          isActive: acc.is_active,
        }));
        setAccounts(formattedAccounts);
      }
    } catch (error) {
      console.error("Failed to fetch accounts:", error);
      setAccounts([]);
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
