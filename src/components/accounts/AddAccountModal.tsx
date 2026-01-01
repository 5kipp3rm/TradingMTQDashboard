import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Plus, Eye, EyeOff } from "lucide-react";

interface AddAccountModalProps {
  open: boolean;
  onClose: () => void;
  onAdd: (account: {
    name: string;
    loginNumber: string;
    platform: string;
    server: string;
    serverCustom?: string;
    password: string;
    broker: string;
    isDemo: boolean;
    isDefault: boolean;
  }) => void;
}

interface ServerOption {
  value: string;
  label: string;
}

const platforms = ["MT4", "MT5"];

export function AddAccountModal({ open, onClose, onAdd }: AddAccountModalProps) {
  const [name, setName] = useState("");
  const [loginNumber, setLoginNumber] = useState("");
  const [platform, setPlatform] = useState("");
  const [server, setServer] = useState("");
  const [serverCustom, setServerCustom] = useState("");
  const [password, setPassword] = useState("");
  const [broker, setBroker] = useState("");
  const [isDemo, setIsDemo] = useState(false);
  const [isDefault, setIsDefault] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [serverOptions, setServerOptions] = useState<ServerOption[]>([]);
  const [loadingServers, setLoadingServers] = useState(false);

  // Fetch server options when modal opens
  useEffect(() => {
    if (open) {
      fetchServerOptions();
    }
  }, [open]);

  const fetchServerOptions = async () => {
    setLoadingServers(true);
    try {
      const response = await fetch("/api/servers/options");
      if (response.ok) {
        const data = await response.json();
        setServerOptions(data.servers || []);
      }
    } catch (error) {
      console.error("Failed to fetch server options:", error);
      // Fallback to basic options
      setServerOptions([
        { value: "Demo", label: "Demo Server" },
        { value: "Live-01", label: "Live Server 01" },
        { value: "Custom", label: "Custom Server (enter manually)" }
      ]);
    } finally {
      setLoadingServers(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAdd({
      name,
      loginNumber,
      platform,
      server,
      serverCustom: server === "Custom" ? serverCustom : undefined,
      password,
      broker,
      isDemo,
      isDefault
    });
    resetForm();
    onClose();
  };

  const resetForm = () => {
    setName("");
    setLoginNumber("");
    setPlatform("");
    setServer("");
    setServerCustom("");
    setPassword("");
    setBroker("");
    setIsDemo(false);
    setIsDefault(false);
    setShowPassword(false);
  };

  const isValid = name && loginNumber && platform && server && password &&
    (server !== "Custom" || serverCustom.trim() !== "");

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Add Trading Account
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Account Name - Full Row */}
          <div>
            <Label htmlFor="name">Account Name</Label>
            <Input
              id="name"
              placeholder="e.g., My Main Account"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          {/* Account Number & Platform - Side by Side */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="loginNumber">Account Number / Login</Label>
              <Input
                id="loginNumber"
                placeholder="e.g., 123456789"
                value={loginNumber}
                onChange={(e) => setLoginNumber(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="platform">Platform</Label>
              <Select value={platform} onValueChange={setPlatform}>
                <SelectTrigger>
                  <SelectValue placeholder="Select platform" />
                </SelectTrigger>
                <SelectContent>
                  {platforms.map((p) => (
                    <SelectItem key={p} value={p}>
                      {p}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Server & Password - Side by Side */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="server">Server</Label>
              <Select value={server} onValueChange={setServer} disabled={loadingServers}>
                <SelectTrigger>
                  <SelectValue placeholder={loadingServers ? "Loading..." : "Select server"} />
                </SelectTrigger>
                <SelectContent>
                  {serverOptions.map((s) => (
                    <SelectItem key={s.value} value={s.value}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Account password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pr-10"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <Eye className="h-4 w-4 text-muted-foreground" />
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* Custom Server Input - Shows only when "Custom" is selected */}
          {server === "Custom" && (
            <div>
              <Label htmlFor="serverCustom">Custom Server Name</Label>
              <Input
                id="serverCustom"
                placeholder="e.g., MyBroker-Real-01"
                value={serverCustom}
                onChange={(e) => setServerCustom(e.target.value)}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Find in MT5: Tools → Options → Server
              </p>
            </div>
          )}

          {/* Broker - Full Row */}
          <div>
            <Label htmlFor="broker">Broker (Optional)</Label>
            <Input
              id="broker"
              placeholder="e.g., ICMarkets"
              value={broker}
              onChange={(e) => setBroker(e.target.value)}
            />
          </div>

          {/* Checkboxes */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="isDemo"
                checked={isDemo}
                onCheckedChange={(checked) => setIsDemo(checked as boolean)}
              />
              <Label htmlFor="isDemo" className="text-sm font-normal cursor-pointer">
                Demo account
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="isDefault"
                checked={isDefault}
                onCheckedChange={(checked) => setIsDefault(checked as boolean)}
              />
              <Label htmlFor="isDefault" className="text-sm font-normal cursor-pointer">
                Set as default account
              </Label>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={!isValid}>
              Add Account
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}