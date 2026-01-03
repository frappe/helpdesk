import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, TrendingDown, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getDashboard } from '@/lib/api';
import { DashboardMetrics } from '@/types';

interface MetricCardProps {
  title: string;
  value: number | string;
  change?: number;
  icon: React.ReactNode;
}

function MetricCard({ title, value, change, icon }: MetricCardProps) {
  const hasPositiveChange = change && change > 0;
  const hasNegativeChange = change && change < 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
          {icon}
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change !== undefined && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
            {hasPositiveChange && <TrendingUp className="h-3 w-3 text-green-500" />}
            {hasNegativeChange && <TrendingDown className="h-3 w-3 text-red-500" />}
            <span className={hasPositiveChange ? 'text-green-500' : hasNegativeChange ? 'text-red-500' : ''}>
              {Math.abs(change)}%
            </span>
            <span>from last week</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function Dashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchDashboard() {
      try {
        const data = await getDashboard();
        setMetrics(data);
      } catch (error) {
        console.error('Failed to fetch dashboard:', error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchDashboard();
  }, []);

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse mb-8" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-200 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-muted-foreground mt-1">Overview of your helpdesk performance</p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Total Tickets"
          value={metrics?.total_tickets || 0}
          icon={<AlertCircle className="h-4 w-4" />}
        />
        <MetricCard
          title="Open Tickets"
          value={metrics?.open_tickets || 0}
          icon={<Clock className="h-4 w-4" />}
        />
        <MetricCard
          title="Resolved Tickets"
          value={metrics?.resolved_tickets || 0}
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
        <MetricCard
          title="Avg Response Time"
          value={`${metrics?.avg_response_time || 0}h`}
          icon={<TrendingUp className="h-4 w-4" />}
        />
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground">
              <p>No recent activity to display</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Link
              to="/tickets"
              className="block p-3 rounded-md hover:bg-gray-50 transition-colors border border-gray-200"
            >
              <p className="font-medium text-sm">View All Tickets</p>
              <p className="text-xs text-muted-foreground">Manage and respond to tickets</p>
            </Link>
            <Link
              to="/kb"
              className="block p-3 rounded-md hover:bg-gray-50 transition-colors border border-gray-200"
            >
              <p className="font-medium text-sm">Browse Knowledge Base</p>
              <p className="text-xs text-muted-foreground">Find answers and articles</p>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
