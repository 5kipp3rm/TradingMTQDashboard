import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Header } from "@/components/dashboard/Header";
import { Download, FileText, Calendar } from "lucide-react";

const Reports = () => {
  const reportTypes = [
    { id: "daily", name: "Daily Report", description: "Summary of today's trading activity" },
    { id: "weekly", name: "Weekly Report", description: "Week-over-week performance analysis" },
    { id: "monthly", name: "Monthly Report", description: "Comprehensive monthly statistics" },
    { id: "custom", name: "Custom Report", description: "Generate report for custom date range" },
  ];

  const recentReports = [
    { id: "1", name: "December 2024 Monthly", date: "2024-12-01", size: "245 KB" },
    { id: "2", name: "Week 50 Summary", date: "2024-12-09", size: "128 KB" },
    { id: "3", name: "Week 49 Summary", date: "2024-12-02", size: "135 KB" },
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="container py-5 max-w-[1400px]">
        <Header
          period={30}
          onPeriodChange={() => {}}
          onRefresh={() => {}}
          onQuickTrade={() => {}}
        />

        <h2 className="text-2xl font-bold mb-6">Reports</h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-6">
          <Card className="card-glow">
            <CardHeader>
              <CardTitle>Generate Report</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {reportTypes.map((report) => (
                  <div
                    key={report.id}
                    className="p-4 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors cursor-pointer"
                  >
                    <div className="flex items-start gap-3">
                      <FileText className="h-5 w-5 text-primary mt-0.5" />
                      <div>
                        <p className="font-semibold">{report.name}</p>
                        <p className="text-sm text-muted-foreground">{report.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="card-glow">
            <CardHeader>
              <CardTitle>Recent Reports</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentReports.map((report) => (
                  <div
                    key={report.id}
                    className="flex items-center justify-between p-4 rounded-lg bg-muted/30"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-semibold">{report.name}</p>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Calendar className="h-3 w-3" />
                          {new Date(report.date).toLocaleDateString()}
                          <span>•</span>
                          {report.size}
                        </div>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="card-glow">
          <CardHeader>
            <CardTitle>Performance Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center">
                <p className="text-3xl font-bold font-mono text-profit">$6,240</p>
                <p className="text-sm text-muted-foreground">Total Profit (MTD)</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold font-mono">234</p>
                <p className="text-sm text-muted-foreground">Total Trades</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold font-mono">68.5%</p>
                <p className="text-sm text-muted-foreground">Win Rate</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold font-mono">1.85</p>
                <p className="text-sm text-muted-foreground">Profit Factor</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Reports;
