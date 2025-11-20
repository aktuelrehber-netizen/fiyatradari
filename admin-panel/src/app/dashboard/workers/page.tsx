'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ExternalLink, Flower as FlowerIcon, Play, Pause, Power, Loader2 } from 'lucide-react';
import { workersAPI } from '@/utils/api-client';
import { useToast } from '@/hooks/use-toast';

export default function WorkersPage() {
  const flowerUrl = 'http://localhost:5555';
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [controlStatus, setControlStatus] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadControlStatus();
  }, []);

  const loadControlStatus = async () => {
    try {
      setRefreshing(true);
      const status = await workersAPI.getControlStatus();
      setControlStatus(status);
    } catch (error) {
      console.error('Failed to load control status:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handlePause = async () => {
    try {
      setLoading(true);
      await workersAPI.pauseScheduler();
      toast({
        title: '✅ Scheduler Durduruldu',
        description: 'Otomatik görevler artık çalışmayacak.',
      });
      await loadControlStatus();
    } catch (error) {
      toast({
        title: '❌ Hata',
        description: 'Scheduler durdurulamadı.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleResume = async () => {
    try {
      setLoading(true);
      await workersAPI.resumeScheduler();
      toast({
        title: '✅ Scheduler Başlatıldı',
        description: 'Otomatik görevler tekrar çalışacak.',
      });
      await loadControlStatus();
    } catch (error) {
      toast({
        title: '❌ Hata',
        description: 'Scheduler başlatılamadı.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleToggleJob = async (jobType: string, currentStatus: boolean) => {
    try {
      setLoading(true);
      if (currentStatus) {
        await workersAPI.disableJob(jobType);
        toast({
          title: '⏸️ Job Kapatıldı',
          description: `${getJobDisplayName(jobType)} artık çalışmayacak.`,
        });
      } else {
        await workersAPI.enableJob(jobType);
        toast({
          title: '▶️ Job Açıldı',
          description: `${getJobDisplayName(jobType)} tekrar çalışacak.`,
        });
      }
      await loadControlStatus();
    } catch (error) {
      toast({
        title: '❌ Hata',
        description: 'Job durumu değiştirilemedi.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const getJobDisplayName = (jobType: string) => {
    const names: Record<string, string> = {
      fetch_products: 'Ürün Çekme',
      check_prices: 'Fiyat Kontrol',
      send_telegram: 'Telegram'
    };
    return names[jobType] || jobType;
  };

  const isRunning = controlStatus?.scheduler_enabled;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <FlowerIcon className="w-8 h-8 text-pink-500" />
            Worker Yönetimi
          </h1>
          <p className="text-muted-foreground mt-1">
            Worker'ları kontrol et ve izle
          </p>
        </div>
        
        <Button
          onClick={() => window.open(flowerUrl, '_blank')}
          variant="outline"
          size="sm"
        >
          <ExternalLink className="w-4 h-4 mr-2" />
          Flower'ı Aç
        </Button>
      </div>

      {/* Worker Control Panel */}
      <Card>
        <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b">
          <CardTitle className="text-lg flex items-center gap-2">
            <Power className="w-5 h-5" />
            Worker Kontrolü
          </CardTitle>
          <CardDescription>
            Otomatik görevleri durdur veya başlat
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
                isRunning 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-yellow-100 text-yellow-700'
              }`}>
                {isRunning ? (
                  <><Play className="w-4 h-4" /> Çalışıyor</>
                ) : (
                  <><Pause className="w-4 h-4" /> Durduruldu</>
                )}
              </div>
              <Button
                onClick={loadControlStatus}
                variant="ghost"
                size="sm"
                disabled={refreshing}
              >
                {refreshing ? <Loader2 className="w-4 h-4 animate-spin" /> : '🔄 Yenile'}
              </Button>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handlePause}
                variant="destructive"
                disabled={loading || !isRunning}
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Pause className="w-4 h-4 mr-2" />}
                Durdur
              </Button>
              <Button
                onClick={handleResume}
                variant="default"
                disabled={loading || isRunning}
                className="bg-green-600 hover:bg-green-700"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                Başlat
              </Button>
            </div>
          </div>

          {controlStatus?.jobs && (
            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              <JobControlCard
                title="Ürün Çekme"
                jobType="fetch_products"
                enabled={controlStatus.jobs.fetch_products?.enabled}
                onToggle={handleToggleJob}
                loading={loading}
              />
              <JobControlCard
                title="Fiyat Kontrol"
                jobType="check_prices"
                enabled={controlStatus.jobs.check_prices?.enabled}
                onToggle={handleToggleJob}
                loading={loading}
              />
              <JobControlCard
                title="Telegram"
                jobType="send_telegram"
                enabled={controlStatus.jobs.send_telegram?.enabled}
                onToggle={handleToggleJob}
                loading={loading}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Flower iFrame */}
      <Card className="overflow-hidden">
        <CardHeader className="bg-gradient-to-r from-pink-50 to-purple-50 border-b">
          <CardTitle className="text-lg">Celery Flower Monitor</CardTitle>
          <CardDescription>
            Workers, Tasks, Task History, ve Broker bilgilerini görüntüleyin
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="relative w-full" style={{ height: 'calc(100vh - 280px)', minHeight: '600px' }}>
            <iframe
              src={flowerUrl}
              className="w-full h-full border-0"
              title="Flower Dashboard"
              sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
            />
          </div>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">💡 Flower Özellikleri</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <h4 className="font-semibold mb-2">🔍 Monitoring</h4>
              <ul className="text-muted-foreground space-y-1">
                <li>• Real-time worker durumu</li>
                <li>• Aktif task'ları izle</li>
                <li>• Task geçmişi</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">⚙️ Yönetim</h4>
              <ul className="text-muted-foreground space-y-1">
                <li>• Worker'ları restart et</li>
                <li>• Task'ları iptal et</li>
                <li>• Pool boyutu ayarla</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">📊 İstatistikler</h4>
              <ul className="text-muted-foreground space-y-1">
                <li>• Task başarı/hata oranı</li>
                <li>• İşlem süreleri</li>
                <li>• Queue durumu</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Job Control Card Component
interface JobControlCardProps {
  title: string;
  jobType: string;
  enabled: boolean;
  onToggle: (jobType: string, currentStatus: boolean) => void;
  loading: boolean;
}

function JobControlCard({ title, jobType, enabled, onToggle, loading }: JobControlCardProps) {
  return (
    <div className={`p-4 rounded-lg border-2 transition-all ${
      enabled 
        ? 'bg-green-50 border-green-200' 
        : 'bg-gray-50 border-gray-200'
    }`}>
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold">{title}</div>
        <div className={`text-xs px-2 py-1 rounded ${
          enabled 
            ? 'bg-green-100 text-green-700' 
            : 'bg-gray-200 text-gray-600'
        }`}>
          {enabled ? '✓ Aktif' : '✗ Kapalı'}
        </div>
      </div>
      <Button
        onClick={() => onToggle(jobType, enabled)}
        disabled={loading}
        variant={enabled ? 'destructive' : 'default'}
        size="sm"
        className={`w-full ${!enabled && 'bg-green-600 hover:bg-green-700'}`}
      >
        {loading ? (
          <Loader2 className="w-3 h-3 animate-spin mr-2" />
        ) : enabled ? (
          <Pause className="w-3 h-3 mr-2" />
        ) : (
          <Play className="w-3 h-3 mr-2" />
        )}
        {enabled ? 'Kapat' : 'Aç'}
      </Button>
    </div>
  );
}
