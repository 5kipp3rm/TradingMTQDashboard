/**
 * Admin: Registration Settings
 *
 * Toggle self-registration on/off and set the default role for new users.
 */

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/dashboard/Header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { QuickTradeModal } from "@/components/dashboard/QuickTradeModal";
import { getAccessToken } from "@/lib/auth";
import { UserPlus, ArrowLeft, Save, CheckCircle } from "lucide-react";
import { Link } from "react-router-dom";

const API = import.meta.env.VITE_API_URL || "/api";

export default function AdminRegistration() {
  const { toast } = useToast();
  const [enabled, setEnabled] = useState(true);
  const [defaultRole, setDefaultRole] = useState("viewer");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [quickTradeOpen, setQuickTradeOpen] = useState(false);

  const headers = () => ({
    Authorization: `Bearer ${getAccessToken()}`,
    "Content-Type": "application/json",
  });

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/auth/registration-settings`, { headers: headers() });
      if (res.ok) {
        const data = await res.json();
        setEnabled(data.enabled ?? true);
        setDefaultRole(data.default_role ?? "viewer");
      }
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { fetchSettings(); }, [fetchSettings]);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      const res = await fetch(`${API}/auth/registration-settings`, {
        method: "PUT",
        headers: headers(),
        body: JSON.stringify({ enabled, default_role: defaultRole }),
      });
      if (!res.ok) throw new Error("Failed to update");
      setSaved(true);
      toast({ title: "Saved", description: "Registration settings updated" });
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    }
    setSaving(false);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full py-5 px-4 lg:px-8">
        <Header period={30} onPeriodChange={() => {}} onRefresh={fetchSettings} onQuickTrade={() => setQuickTradeOpen(true)} />

        <div className="flex items-center gap-3 mb-6">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/admin"><ArrowLeft className="h-4 w-4 mr-1" />Admin</Link>
          </Button>
          <UserPlus className="h-6 w-6 text-indigo-500" />
          <h2 className="text-2xl font-bold">Registration Settings</h2>
        </div>

        <div className="max-w-xl">
          <Card>
            <CardHeader>
              <CardTitle>Self-Registration</CardTitle>
              <CardDescription>
                Control whether new users can create their own accounts.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {loading ? (
                <p className="text-sm text-muted-foreground">Loading...</p>
              ) : (
                <>
                  {/* Enable/Disable Toggle */}
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <Label className="text-base font-medium">Allow Registration</Label>
                      <p className="text-sm text-muted-foreground">
                        When enabled, a &quot;Sign Up&quot; link appears on the login page.
                      </p>
                    </div>
                    <Switch checked={enabled} onCheckedChange={setEnabled} />
                  </div>

                  {/* Default Role */}
                  <div className="space-y-2">
                    <Label>Default Role for New Users</Label>
                    <Select value={defaultRole} onValueChange={setDefaultRole}>
                      <SelectTrigger className="w-[200px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="viewer">Viewer (read-only)</SelectItem>
                        <SelectItem value="trader">Trader (can trade)</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      Admin role can only be assigned manually through User Management.
                    </p>
                  </div>

                  {saved && (
                    <Alert className="border-green-500/50 bg-green-500/10">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <AlertDescription className="text-green-700 dark:text-green-400">
                        Settings saved successfully.
                      </AlertDescription>
                    </Alert>
                  )}

                  <Button onClick={handleSave} disabled={saving} className="w-full">
                    <Save className="h-4 w-4 mr-2" />
                    {saving ? "Saving..." : "Save Settings"}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        <QuickTradeModal open={quickTradeOpen} onClose={() => setQuickTradeOpen(false)} currencies={[]} onTrade={() => {}} />
      </div>
    </div>
  );
}
