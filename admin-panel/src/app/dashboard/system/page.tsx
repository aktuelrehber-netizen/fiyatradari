'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { useToast } from '@/hooks/use-toast'
import { 
  Activity, Server, Zap, Database, Clock, Play, Pause, 
  RefreshCw, Loader2, X, TrendingUp, AlertCircle, CheckCircle2
} from 'lucide-react'

interface SystemHealth {
  status: string
  score: number
  database: boolean
  redis: boolean
  workers: number
  queue_size: number
}

interface Schedule {
  enabled: boolean
  cron: string
  description?: string
}

interface ActiveTask {
  task_id: string
  task_name: string
  worker: string
  started: string
  duration_seconds: number
}

export default function SystemManagementPage() {
  const { toast } = useToast()
  
  // State
  const [loading, setLoading] = useState(true)
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [stats, setStats] = useState<any>(null)
  const [schedules, setSchedules] = useState<Record<string, Schedule>>({})
  const [activeTasks, setActiveTasks] = useState<ActiveTask[]>([])
  const [poolSize, setPoolSize] = useState(4)
  const [isRunning, setIsRunning] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  // Load dashboard data
  const loadDashboard = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/system/dashboard')
      const data = await response.json()
      
      setHealth(data.health)
      setStats(data.stats)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load dashboard:', error)
      setLoading(false)
    }
  }

  // Load schedules
  const loadSchedules = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/system/schedules')
      const data = await response.json()
      setSchedules(data.schedules || {})
    } catch (error) {
      console.error('Failed to load schedules:', error)
    }
  }

  // Load active tasks
  const loadActiveTasks = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/system/tasks/active')
      const data = await response.json()
      setActiveTasks(data.tasks || [])
    } catch (error) {
      console.error('Failed to load tasks:', error)
    }
  }

  // Load worker pool status
  const loadPoolStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/system/workers/pool')
      const data = await response.json()
      setPoolSize(data.current_size || 4)
    } catch (error) {
      console.error('Failed to load pool status:', error)
    }
  }

  // Load control status
  const loadControlStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/system/control/status')
      const data = await response.json()
      setIsRunning(data.scheduler_enabled !== false)
    } catch (error) {
      console.error('Failed to load control status:', error)
    }
  }

  // Initial load
  useEffect(() => {
    loadDashboard()
    loadSchedules()
    loadActiveTasks()
    loadPoolStatus()
    loadControlStatus()

    // Auto-refresh every 5 seconds
    const interval = setInterval(() => {
      loadDashboard()
      loadActiveTasks()
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  // Scale worker pool
  const handleScalePool = async (newSize: number) => {
    try {
      setActionLoading(true)
      const token = localStorage.getItem('token')
      
      const response = await fetch(`http://localhost:8000/api/v1/system/workers/pool/scale?size=${newSize}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!response.ok) throw new Error('Failed to scale pool')
      
      toast({
        title: '✅ Pool Scaled',
        description: `Worker pool size set to ${newSize}`
      })
      
      setPoolSize(newSize)
    } catch (error) {
      toast({
        title: '❌ Error',
        description: 'Failed to scale worker pool',
        variant: 'destructive'
      })
    } finally {
      setActionLoading(false)
    }
  }

  // Toggle scheduler
  const handleToggleScheduler = async () => {
    try {
      setActionLoading(true)
      const token = localStorage.getItem('token')
      const endpoint = isRunning ? 'pause' : 'resume'
      
      const response = await fetch(`http://localhost:8000/api/v1/system/control/${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!response.ok) throw new Error('Failed to toggle scheduler')
      
      toast({
        title: isRunning ? '⏸️ Paused' : '▶️ Resumed',
        description: isRunning ? 'All jobs paused' : 'All jobs resumed'
      })
      
      setIsRunning(!isRunning)
    } catch (error) {
      toast({
        title: '❌ Error',
        description: 'Failed to toggle scheduler',
        variant: 'destructive'
      })
    } finally {
      setActionLoading(false)
    }
  }

  // Update schedule
  const handleUpdateSchedule = async (jobType: string, enabled: boolean, cron: string) => {
    try {
      const token = localStorage.getItem('token')
      
      const response = await fetch(`http://localhost:8000/api/v1/system/schedules/${jobType}?enabled=${enabled}&cron=${encodeURIComponent(cron)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!response.ok) throw new Error('Failed to update schedule')
      
      toast({
        title: '✅ Schedule Updated',
        description: `${jobType} schedule updated`
      })
      
      loadSchedules()
    } catch (error) {
      toast({
        title: '❌ Error',
        description: 'Failed to update schedule',
        variant: 'destructive'
      })
    }
  }

  // Cancel task
  const handleCancelTask = async (taskId: string) => {
    try {
      const token = localStorage.getItem('token')
      
      const response = await fetch(`http://localhost:8000/api/v1/system/tasks/${taskId}/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!response.ok) throw new Error('Failed to cancel task')
      
      toast({
        title: '✅ Task Cancelled',
        description: `Task ${taskId.substring(0, 8)} cancelled`
      })
      
      loadActiveTasks()
    } catch (error) {
      toast({
        title: '❌ Error',
        description: 'Failed to cancel task',
        variant: 'destructive'
      })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-12 h-12 animate-spin text-primary" />
      </div>
    )
  }

  const healthStatus = health?.status || 'unknown'
  const healthColor = healthStatus === 'healthy' ? 'text-green-600' : 
                      healthStatus === 'degraded' ? 'text-yellow-600' : 'text-red-600'

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Server className="w-8 h-8 text-blue-600" />
            Sistem Yönetimi
          </h1>
          <p className="text-muted-foreground mt-1">
            Worker kontrolü, zamanlama ve performans yönetimi
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={isRunning ? "default" : "secondary"} className="px-4 py-2">
            {isRunning ? <><Play className="w-4 h-4 mr-2" /> Çalışıyor</> : <><Pause className="w-4 h-4 mr-2" /> Durduruldu</>}
          </Badge>
          <Button onClick={() => { loadDashboard(); loadActiveTasks(); loadSchedules() }} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Yenile
          </Button>
        </div>
      </div>

      {/* Health & Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className={healthStatus === 'healthy' ? 'border-green-200' : healthStatus === 'degraded' ? 'border-yellow-200' : 'border-red-200'}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center justify-between">
              Sistem Sağlığı
              {healthStatus === 'healthy' ? <CheckCircle2 className="w-5 h-5 text-green-600" /> : <AlertCircle className="w-5 h-5 text-yellow-600" />}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${healthColor}`}>
              {health?.score || 0}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {healthStatus === 'healthy' ? 'Mükemmel' : healthStatus === 'degraded' ? 'Dikkat' : 'Kritik'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center justify-between">
              Toplam Ürün
              <Database className="w-5 h-5 text-muted-foreground" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_products?.toLocaleString('tr-TR') || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">Veritabanında</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center justify-between">
              Aktif Fırsatlar
              <Zap className="w-5 h-5 text-orange-500" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{stats?.active_deals?.toLocaleString('tr-TR') || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">Şu anda</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center justify-between">
              Bugün İşlenen
              <TrendingUp className="w-5 h-5 text-muted-foreground" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.tasks_today?.toLocaleString('tr-TR') || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">Task</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Worker Pool Control */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Worker Pool Yönetimi
            </CardTitle>
            <CardDescription>
              Eşzamanlı çalışan task sayısını ayarlayın
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-base font-semibold">Pool Size</Label>
                <Badge variant="outline" className="text-lg px-3">
                  {poolSize} worker
                </Badge>
              </div>
              <Slider
                value={[poolSize]}
                onValueChange={(value: number[]) => setPoolSize(value[0])}
                min={1}
                max={20}
                step={1}
                className="w-full"
                disabled={actionLoading}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Min: 1</span>
                <span>Max: 20</span>
              </div>
            </div>

            <Button
              onClick={() => handleScalePool(poolSize)}
              disabled={actionLoading}
              className="w-full"
              size="lg"
            >
              {actionLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Zap className="w-4 h-4 mr-2" />}
              Pool Size Güncelle
            </Button>

            <div className="pt-4 border-t space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Aktif Worker:</span>
                <span className="font-medium">{health?.workers || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Kuyruk:</span>
                <span className="font-medium">{health?.queue_size || 0} task</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Scheduler Control */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Zamanlayıcı Kontrolü
            </CardTitle>
            <CardDescription>
              Tüm otomatik görevleri durdur/başlat
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className={`p-6 rounded-lg border-2 ${isRunning ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-lg">Durum</h3>
                  <p className="text-sm text-muted-foreground">
                    {isRunning ? 'Tüm görevler zamanında çalışıyor' : 'Otomatik görevler durduruldu'}
                  </p>
                </div>
                {isRunning ? (
                  <Play className="w-8 h-8 text-green-600" />
                ) : (
                  <Pause className="w-8 h-8 text-gray-600" />
                )}
              </div>
              <Button
                onClick={handleToggleScheduler}
                disabled={actionLoading}
                variant={isRunning ? "destructive" : "default"}
                className={`w-full ${!isRunning && 'bg-green-600 hover:bg-green-700'}`}
                size="lg"
              >
                {actionLoading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : isRunning ? (
                  <Pause className="w-4 h-4 mr-2" />
                ) : (
                  <Play className="w-4 h-4 mr-2" />
                )}
                {isRunning ? 'Tüm Görevleri Durdur' : 'Görevleri Başlat'}
              </Button>
            </div>

            <div className="space-y-2 pt-4 border-t">
              <h4 className="font-semibold text-sm">Sistem Durumu</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Database:</span>
                  <Badge variant={health?.database ? "default" : "destructive"}>
                    {health?.database ? '✓ Online' : '✗ Offline'}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Redis:</span>
                  <Badge variant={health?.redis ? "default" : "destructive"}>
                    {health?.redis ? '✓ Online' : '✗ Offline'}
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Job Schedules */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Görev Zamanlamaları
          </CardTitle>
          <CardDescription>
            Her görevin çalışma zamanını ve durumunu yönetin (Cron format)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(schedules).map(([jobType, schedule]) => (
              <div key={jobType} className="flex items-center gap-4 p-4 border rounded-lg">
                <Switch
                  checked={schedule.enabled}
                  onCheckedChange={(checked) => handleUpdateSchedule(jobType, checked, schedule.cron)}
                />
                <div className="flex-1">
                  <h4 className="font-semibold">{schedule.description || jobType}</h4>
                  <p className="text-sm text-muted-foreground font-mono">{schedule.cron}</p>
                </div>
                <Badge variant={schedule.enabled ? "default" : "secondary"}>
                  {schedule.enabled ? 'Aktif' : 'Kapalı'}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Active Tasks */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Aktif Task'lar
            <Badge variant="outline">{activeTasks.length}</Badge>
          </CardTitle>
          <CardDescription>
            Şu anda çalışan görevler
          </CardDescription>
        </CardHeader>
        <CardContent>
          {activeTasks.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              Şu anda aktif task yok
            </div>
          ) : (
            <div className="space-y-3">
              {activeTasks.map((task) => (
                <div key={task.task_id} className="flex items-center gap-4 p-4 border rounded-lg bg-blue-50">
                  <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                  <div className="flex-1">
                    <h4 className="font-semibold">{task.task_name}</h4>
                    <p className="text-sm text-muted-foreground">
                      Worker: {task.worker} • {task.duration_seconds}s
                    </p>
                  </div>
                  <Button
                    onClick={() => handleCancelTask(task.task_id)}
                    variant="ghost"
                    size="sm"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
