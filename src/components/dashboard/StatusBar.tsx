import { cn } from "@/lib/utils";

type ConnectionStatus = "connected" | "disconnected" | "connecting";

interface StatusBarProps {
  status: ConnectionStatus;
  lastUpdate: Date | null;
}

export function StatusBar({ status, lastUpdate }: StatusBarProps) {
  const statusText = {
    connected: "Connected",
    disconnected: "Disconnected",
    connecting: "Connecting...",
  };

  const statusClass = {
    connected: "status-dot-connected",
    disconnected: "status-dot-disconnected",
    connecting: "status-dot-connecting",
  };

  return (
    <div className="bg-card rounded-lg px-5 py-3 mb-5 flex justify-between items-center shadow-lg">
      <span className="flex items-center gap-2">
        <span className={cn("status-dot", statusClass[status])} />
        <span className="text-sm text-muted-foreground">{statusText[status]}</span>
      </span>
      <span className="text-sm text-muted-foreground">
        Last updated: {lastUpdate ? lastUpdate.toLocaleTimeString() : "Never"}
      </span>
    </div>
  );
}
