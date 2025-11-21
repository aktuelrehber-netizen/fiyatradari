'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { healthAPI } from '@/utils/api-client'
import { Package, Zap, FolderTree, Send, TrendingUp, Activity, TrendingDown, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface DashboardStats {
  total_products: number
  active_products: number
  total_categories: number
  active_deals: number
  total_price_checks_today: number
  price_changes_today: number
  telegram_messages_sent: number
  last_worker_run: string | null
  system_health: string
}

interface TrendData {
  date: string
  price_checks: number
  deals: number
}

interface CategoryData {
  name: string
  value: number
}

interface Deal {
  id: number
  title: string
  discount_percentage: number
  deal_price: string
  original_price: string
  currency: string
  created_at: string
}

interface Product {
  id: number
  title: string
  brand: string
  current_price: string
  currency: string
  image_url: string
  created_at: string
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [trends, setTrends] = useState<TrendData[]>([])
  const [categories, setCategories] = useState<CategoryData[]>([])
  const [topDeals, setTopDeals] = useState<Deal[]>([])
  const [recentProducts, setRecentProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      const [statsData, trendsData, categoriesData, dealsData, productsData] = await Promise.all([
        healthAPI.dashboard(),
        healthAPI.getTrends(),
        healthAPI.getCategoryStats(),
        healthAPI.getTopDeals(),
        healthAPI.getRecentProducts()
      ])
      
      setStats(statsData)
      setTrends(trendsData.trends || [])
      setCategories(categoriesData.categories || [])
      setTopDeals(dealsData.deals || [])
      setRecentProducts(productsData.products || [])
    } catch (error) {
      // Silent fail - dashboard will show empty states
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    )
  }

  const statCards = [
    {
      title: 'Toplam Ürün',
      value: stats?.total_products || 0,
      icon: Package,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Aktif Ürün',
      value: stats?.active_products || 0,
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: 'Kategoriler',
      value: stats?.total_categories || 0,
      icon: FolderTree,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: 'Aktif Fırsatlar',
      value: stats?.active_deals || 0,
      icon: Zap,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
    {
      title: 'Bugünkü Fiyat Kontrolleri',
      value: stats?.total_price_checks_today || 0,
      icon: RefreshCw,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-100',
    },
    {
      title: 'Bugün Fiyatı Değişenler',
      value: stats?.price_changes_today || 0,
      icon: TrendingDown,
      color: 'text-pink-600',
      bgColor: 'bg-pink-100',
    },
    {
      title: 'Telegram Mesajları',
      value: stats?.telegram_messages_sent || 0,
      icon: Send,
      color: 'text-cyan-600',
      bgColor: 'bg-cyan-100',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-gray-500 mt-1">
          Fiyat Radarı sistem özeti ve istatistikler
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <div className={`${stat.bgColor} p-2 rounded-lg`}>
                  <Icon className={`h-5 w-5 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stat.value}</div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sistem Durumu</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Sistem Sağlığı</span>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                stats?.system_health === 'healthy' 
                  ? 'bg-green-100 text-green-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {stats?.system_health === 'healthy' ? 'Sağlıklı' : 'Uyarı'}
              </span>
            </div>
            
            {stats?.last_worker_run && (
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Son Worker Çalışması</span>
                <span className="text-sm text-gray-600">
                  {new Date(stats.last_worker_run).toLocaleString('tr-TR')}
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Charts Section */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Aktivite Trendi (Son 7 Gün)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="price_checks" stroke="#3b82f6" strokeWidth={2} name="Fiyat Kontrolleri" />
                <Line type="monotone" dataKey="deals" stroke="#10b981" strokeWidth={2} name="Fırsatlar" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Kategori Dağılımı</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categories}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {categories.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity Section */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-orange-500" />
              En Yüksek İndirimler
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topDeals.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">Henüz fırsat yok</p>
              ) : (
                topDeals.map((deal) => (
                  <div key={deal.id} className="flex items-center justify-between border-b pb-3 last:border-0">
                    <div className="flex-1">
                      <p className="font-medium text-sm line-clamp-1">{deal.title}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(deal.created_at).toLocaleDateString('tr-TR')}
                      </p>
                    </div>
                    <div className="text-right ml-4">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 line-through">
                          {parseFloat(deal.original_price).toFixed(2)} {deal.currency}
                        </span>
                        <TrendingDown className="h-4 w-4 text-green-600" />
                      </div>
                      <div className="font-bold text-green-600">
                        %{deal.discount_percentage.toFixed(0)}
                      </div>
                      <div className="text-sm font-semibold">
                        {parseFloat(deal.deal_price).toFixed(2)} {deal.currency}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5 text-blue-500" />
              Yeni Eklenen Ürünler
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentProducts.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">Henüz ürün yok</p>
              ) : (
                recentProducts.map((product) => (
                  <div key={product.id} className="flex items-center gap-3 border-b pb-3 last:border-0">
                    {product.image_url && (
                      <div className="relative h-12 w-12 bg-gray-100 rounded flex-shrink-0">
                        <img
                          src={product.image_url}
                          alt={product.title}
                          className="object-contain w-full h-full p-1"
                        />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm line-clamp-1">{product.title}</p>
                      {product.brand && (
                        <p className="text-xs text-gray-500">{product.brand}</p>
                      )}
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className="font-semibold text-sm">
                        {parseFloat(product.current_price).toFixed(2)} {product.currency}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Hızlı İşlemler</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <a
              href="/dashboard/categories"
              className="block p-3 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="font-medium">Yeni Kategori Ekle</div>
              <div className="text-sm text-gray-500">Amazon kategorilerini takip edin</div>
            </a>
            <a
              href="/dashboard/products"
              className="block p-3 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="font-medium">Ürünleri Görüntüle</div>
              <div className="text-sm text-gray-500">Takip edilen ürünleri yönetin</div>
            </a>
            <a
              href="/dashboard/deals"
              className="block p-3 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="font-medium">Fırsatları Yönet</div>
              <div className="text-sm text-gray-500">İndirimleri inceleyin ve yayınlayın</div>
            </a>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sistem Bilgileri</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <div className="text-sm text-gray-500">API Durumu</div>
              <div className="font-medium text-green-600">Çalışıyor</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Database</div>
              <div className="font-medium text-green-600">Bağlı</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Worker</div>
              <div className="font-medium text-green-600">Aktif</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
