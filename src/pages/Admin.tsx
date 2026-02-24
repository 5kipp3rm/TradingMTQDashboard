/**
 * Admin Dashboard Hub
 *
 * Central navigation page for all admin management sections.
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { Header } from "@/components/dashboard/Header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { QuickTradeModal } from "@/components/dashboard/QuickTradeModal";
import {
  Users,
  Activity,
  Wallet,
  Settings,
  Cpu,
  ScrollText,
  UserPlus,
  Shield,
  ArrowRight,
} from "lucide-react";

const adminSections = [
  {
    title: "User Management",
    description: "Create, edit, delete users. Assign roles and reset passwords.",
    icon: Users,
    href: "/admin/users",
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
  },
  {
    title: "API Metrics",
    description: "Monitor request stats, response times, error rates, and uptime.",
    icon: Activity,
    href: "/admin/metrics",
    color: "text-emerald-500",
    bgColor: "bg-emerald-500/10",
  },
  {
    title: "Account Ownership",
    description: "View all trading accounts and reassign ownership between users.",
    icon: Wallet,
    href: "/admin/accounts",
    color: "text-amber-500",
    bgColor: "bg-amber-500/10",
  },
  {
    title: "System Configuration",
    description: "View and manage runtime configuration, import/export settings.",
    icon: Settings,
    href: "/admin/config",
    color: "text-purple-500",
    bgColor: "bg-purple-500/10",
  },
  {
    title: "Workers Management",
    description: "View, start, and stop background workers and trading bots.",
    icon: Cpu,
    href: "/admin/workers",
    color: "text-orange-500",
    bgColor: "bg-orange-500/10",
  },
  {
    title: "System Logs",
    description: "View, filter, and download application logs.",
    icon: ScrollText,
    href: "/admin/logs",
    color: "text-cyan-500",
    bgColor: "bg-cyan-500/10",
  },
  {
    title: "Registration Settings",
    description: "Enable/disable self-registration and set the default role for new users.",
    icon: UserPlus,
    href: "/admin/registration",
    color: "text-pink-500",
    bgColor: "bg-pink-500/10",
  },
  {
    title: "Active Sessions",
    description: "View logged-in users and revoke sessions.",
    icon: Shield,
    href: "/admin/sessions",
    color: "text-red-500",
    bgColor: "bg-red-500/10",
  },
];

export default function Admin() {
  const [quickTradeOpen, setQuickTradeOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full py-5 px-4 lg:px-8">
        <Header
          period={30}
          onPeriodChange={() => {}}
          onRefresh={() => {}}
          onQuickTrade={() => setQuickTradeOpen(true)}
        />

        <div className="mb-6">
          <h2 className="text-3xl font-bold">Admin Panel</h2>
          <p className="text-muted-foreground mt-1">System management and monitoring</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {adminSections.map((section) => {
            const Icon = section.icon;
            return (
              <Link key={section.href} to={section.href}>
                <Card className="h-full hover:shadow-lg hover:border-primary/50 transition-all group cursor-pointer">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className={`p-2.5 rounded-lg ${section.bgColor}`}>
                        <Icon className={`h-6 w-6 ${section.color}`} />
                      </div>
                      <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                    </div>
                    <CardTitle className="text-lg mt-3">{section.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-sm">
                      {section.description}
                    </CardDescription>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>

        <QuickTradeModal
          open={quickTradeOpen}
          onClose={() => setQuickTradeOpen(false)}
          currencies={[]}
          onTrade={() => {}}
        />
      </div>
    </div>
  );
}
