import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Outlet } from "react-router-dom";
import { AccountsProvider } from "@/contexts/AccountsContext";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Accounts from "./pages/Accounts";
import AccountDetail from "./pages/AccountDetail";
import Currencies from "./pages/Currencies";
import Strategies from "./pages/Strategies";
import Config from "./pages/Config";
import Charts from "./pages/Charts";
import Alerts from "./pages/Alerts";
import Reports from "./pages/Reports";
import Logs from "./pages/Logs";
import Admin from "./pages/Admin";
import AdminMetrics from "./pages/AdminMetrics";
import AdminAccounts from "./pages/AdminAccounts";
import AdminConfig from "./pages/AdminConfig";
import AdminWorkers from "./pages/AdminWorkers";
import AdminLogs from "./pages/AdminLogs";
import AdminRegistration from "./pages/AdminRegistration";
import AdminSessions from "./pages/AdminSessions";
import UserManagement from "./pages/UserManagement";
import UserSettings from "./pages/UserSettings";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

/**
 * Layout that wraps authenticated routes with AccountsProvider.
 * AccountsProvider fetches accounts on mount, so it must be inside auth.
 */
function AuthenticatedLayout() {
  return (
    <AccountsProvider>
      <Outlet />
    </AccountsProvider>
  );
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected routes — require authentication */}
            <Route element={<ProtectedRoute />}>
              <Route element={<AuthenticatedLayout />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/accounts" element={<Accounts />} />
                <Route path="/accounts/:id" element={<AccountDetail />} />
                <Route path="/currencies" element={<Currencies />} />
                <Route path="/strategies" element={<Strategies />} />
                <Route path="/config" element={<Config />} />
                <Route path="/charts" element={<Charts />} />
                <Route path="/alerts" element={<Alerts />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/logs" element={<Logs />} />
                <Route path="/settings" element={<UserSettings />} />
                <Route path="/admin" element={<Admin />} />
                <Route path="/admin/users" element={<UserManagement />} />
                <Route path="/admin/metrics" element={<AdminMetrics />} />
                <Route path="/admin/accounts" element={<AdminAccounts />} />
                <Route path="/admin/config" element={<AdminConfig />} />
                <Route path="/admin/workers" element={<AdminWorkers />} />
                <Route path="/admin/logs" element={<AdminLogs />} />
                <Route path="/admin/registration" element={<AdminRegistration />} />
                <Route path="/admin/sessions" element={<AdminSessions />} />
              </Route>
            </Route>

            {/* Catch-all */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
