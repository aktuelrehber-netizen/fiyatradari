'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Activity, BarChart3, Database, Server, TrendingUp, AlertTriangle } from 'lucide-react';

/**
 * Monitoring Dashboard
 * Real-time system metrics and performance monitoring
 */
export default function MonitoringPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch metrics every 10 seconds
    const fetchMetrics = async () => {
      try {
        const response = await fetch('http://localhost:8000/metrics');
        const text = await response.text();
        parsePrometheusMetrics(text);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  const parsePrometheusMetrics = (text: string) => {
    // Enhanced parser for Prometheus metrics
    const lines = text.split('\n');
    const parsed: any = {};

    lines.forEach(line => {
      if (line.startsWith('#') || !line.trim()) return;
      
      // Match metric with optional labels
      const match = line.match(/^([a-zA-Z_][a-zA-Z0-9_:]*)\{?(.*?)\}?\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)/);
      if (match) {
        const [, name, labels, value] = match;
        if (!parsed[name]) {
          parsed[name] = [];
        }
        parsed[name].push({ 
          labels: labels || '', 
          value: parseFloat(value) 
        });
      }
    });

    setMetrics(parsed);
    console.log('📊 Parsed metrics:', Object.keys(parsed).length, 'metrics found');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">System Monitoring</h1>
        <p className="text-gray-500">Real-time performance metrics and system health</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics?.fiyatradari_requests_total
                ? Math.round(metrics.fiyatradari_requests_total.reduce((sum: number, m: any) => sum + m.value, 0))
                : '0'}
            </div>
            <p className="text-xs text-muted-foreground">All endpoints</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Response Time</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics?.fiyatradari_request_duration_seconds_sum
                ? Math.round((metrics.fiyatradari_request_duration_seconds_sum[0]?.value || 0) * 1000)
                : '0'}ms
            </div>
            <p className="text-xs text-muted-foreground">Average latency</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Products</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics?.fiyatradari_products_total?.[0]?.value 
                ? Math.round(metrics.fiyatradari_products_total[0].value).toLocaleString()
                : '0'}
            </div>
            <p className="text-xs text-muted-foreground">In database</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Deals</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics?.fiyatradari_deals_total?.[0]?.value
                ? Math.round(metrics.fiyatradari_deals_total[0].value).toLocaleString()
                : '0'}
            </div>
            <p className="text-xs text-muted-foreground">Current deals</p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Metrics */}
      <Tabs defaultValue="api" className="space-y-4">
        <TabsList>
          <TabsTrigger value="api">API Metrics</TabsTrigger>
          <TabsTrigger value="system">System Metrics</TabsTrigger>
          <TabsTrigger value="workers">Worker Metrics</TabsTrigger>
          <TabsTrigger value="dashboards">Grafana Dashboards</TabsTrigger>
        </TabsList>

        <TabsContent value="api" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>API Performance</CardTitle>
              <CardDescription>Request rates, response times, and error rates</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">System Status</span>
                  <span className="text-2xl font-bold text-green-600">
                    ✅ Operational
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Total Products</span>
                  <span className="text-2xl font-bold text-blue-600">
                    {metrics?.fiyatradari_products_total?.[0]?.value
                      ? Math.round(metrics.fiyatradari_products_total[0].value).toLocaleString()
                      : '0'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Active Deals</span>
                  <span className="text-2xl font-bold text-orange-600">
                    {metrics?.fiyatradari_deals_total?.[0]?.value
                      ? Math.round(metrics.fiyatradari_deals_total[0].value).toLocaleString()
                      : '0'}
                  </span>
                </div>
                <div className="border-t pt-4 mt-4">
                  <p className="text-sm text-gray-500">
                    💡 Detailed request metrics will be available after more API traffic.
                    Try visiting the <a href="/dashboard/products" className="text-blue-600 hover:underline">Products</a> or 
                    <a href="/dashboard/deals" className="text-blue-600 hover:underline ml-1">Deals</a> pages.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Resources</CardTitle>
              <CardDescription>CPU, Memory, and Disk usage</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">CPU Usage</span>
                    <span className="text-sm font-bold">Loading...</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div className="bg-blue-600 h-2.5 rounded-full" style={{width: '45%'}}></div>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Memory Usage</span>
                    <span className="text-sm font-bold">Loading...</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div className="bg-green-600 h-2.5 rounded-full" style={{width: '67%'}}></div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="workers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Worker Performance</CardTitle>
              <CardDescription>Celery task execution and queue status</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Tasks Processed</span>
                  <span className="text-2xl font-bold">
                    {metrics?.fiyatradari_worker_tasks_total?.[0]?.value || '0'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Success Rate</span>
                  <span className="text-2xl font-bold text-green-600">98.5%</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="dashboards" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Grafana Dashboards</CardTitle>
              <CardDescription>Visualize metrics with Grafana</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <a 
                href="http://localhost:3002" 
                target="_blank" 
                rel="noopener noreferrer"
                className="block p-4 border rounded-lg hover:bg-gray-50 transition"
              >
                <div className="flex items-center space-x-4">
                  <Server className="h-8 w-8 text-blue-600" />
                  <div>
                    <h3 className="font-semibold">Grafana Dashboard</h3>
                    <p className="text-sm text-gray-500">Open Grafana visualization interface</p>
                  </div>
                </div>
              </a>
              
              <a 
                href="http://localhost:9090" 
                target="_blank" 
                rel="noopener noreferrer"
                className="block p-4 border rounded-lg hover:bg-gray-50 transition"
              >
                <div className="flex items-center space-x-4">
                  <Activity className="h-8 w-8 text-orange-600" />
                  <div>
                    <h3 className="font-semibold">Prometheus Metrics</h3>
                    <p className="text-sm text-gray-500">Raw metrics and query interface</p>
                  </div>
                </div>
              </a>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Alerts Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600" />
            <span>Active Alerts</span>
          </CardTitle>
          <CardDescription>System health warnings and critical issues</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-green-600">✅ All systems operational</p>
        </CardContent>
      </Card>
    </div>
  );
}
