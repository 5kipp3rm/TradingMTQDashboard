import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AccountsProvider } from "@/contexts/AccountsContext";
import Dashboard from "./pages/Dashboard";
import Accounts from "./pages/Accounts";
import Currencies from "./pages/Currencies";
import Config from "./pages/Config";
import Charts from "./pages/Charts";
import Alerts from "./pages/Alerts";
import Reports from "./pages/Reports";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AccountsProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/accounts" element={<Accounts />} />
            <Route path="/currencies" element={<Currencies />} />
            <Route path="/config" element={<Config />} />
            <Route path="/charts" element={<Charts />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AccountsProvider>
  </QueryClientProvider>
);

export default App;
