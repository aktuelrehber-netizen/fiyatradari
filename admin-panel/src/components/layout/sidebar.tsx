'use client'

import Link from 'next/link'
import Image from 'next/image'
import { usePathname } from 'next/navigation'
import { 
  LayoutDashboard, 
  FolderTree, 
  Package, 
  Zap, 
  Settings, 
  Users,
  LogOut,
  Search,
  Server
} from 'lucide-react'
import { cn } from '@/utils/cn'

const menuItems = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'Kategoriler',
    href: '/dashboard/categories',
    icon: FolderTree,
  },
  {
    title: 'Ürünler',
    href: '/dashboard/products',
    icon: Package,
  },
  {
    title: 'Fırsatlar',
    href: '/dashboard/deals',
    icon: Zap,
  },
  {
    title: 'ASIN Sorgulama',
    href: '/dashboard/asin-lookup',
    icon: Search,
  },
  {
    title: 'Kullanıcılar',
    href: '/dashboard/users',
    icon: Users,
  },
  {
    title: 'Monitoring',
    href: '/dashboard/monitoring',
    icon: Server,
  },
  {
    title: 'Ayarlar',
    href: '/dashboard/settings',
    icon: Settings,
  },
]

export function Sidebar() {
  const pathname = usePathname()

  const handleLogout = () => {
    localStorage.removeItem('token')
    window.location.href = '/login'
  }

  return (
    <div className="flex h-full w-64 flex-col bg-gray-900 text-white">
      <div className="flex h-16 items-center justify-center border-b border-gray-800 px-4">
        <div className="relative w-full h-8">
          <Image
            src="/logo.webp"
            alt="FiyatRadarı"
            fill
            sizes="240px"
            className="object-contain"
            priority
          />
        </div>
      </div>
      
      <nav className="flex-1 space-y-1 p-4">
        {menuItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              )}
            >
              <Icon className="h-5 w-5" />
              {item.title}
            </Link>
          )
        })}
      </nav>

      <div className="border-t border-gray-800 p-4">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-gray-300 transition-colors hover:bg-gray-800 hover:text-white"
        >
          <LogOut className="h-5 w-5" />
          Çıkış Yap
        </button>
      </div>
    </div>
  )
}
