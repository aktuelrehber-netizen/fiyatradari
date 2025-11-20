'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Search, Menu, X, ChevronDown, Send } from 'lucide-react'
import { Logo } from './logo'

interface Category {
  id: number
  name: string
  slug: string
  parent_id?: number | null
  children?: Category[]
}

interface HeaderProps {
  categories?: Category[]
}

// Build tree structure
function buildCategoryTree(categories: Category[]): Category[] {
  const categoryMap = new Map<number, Category>()
  const roots: Category[] = []

  categories.forEach(cat => {
    categoryMap.set(cat.id, { ...cat, children: [] })
  })

  categories.forEach(cat => {
    const node = categoryMap.get(cat.id)!
    if (!cat.parent_id) {
      roots.push(node)
    } else {
      const parent = categoryMap.get(cat.parent_id)
      if (parent) {
        parent.children!.push(node)
      } else {
        roots.push(node)
      }
    }
  })

  return roots
}

export function Header({ categories = [] }: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const categoryTree = buildCategoryTree(categories)

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: Implement search functionality
  }

  return (
    <header className="bg-[#242F3E] border-b border-gray-700 sticky top-0 z-50 shadow-lg">
      {/* Main Header */}
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between py-4">
          {/* Logo */}
          <Link href="/" className="group">
            <Logo className="group-hover:scale-105 transition-transform" />
          </Link>

          {/* Search Bar - Desktop */}
          <form onSubmit={handleSearch} className="hidden md:block flex-1 max-w-xl mx-8">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Ürün veya kategori ara..."
                className="w-full pl-10 pr-4 py-2 text-sm bg-white border border-gray-300 text-gray-900 placeholder:text-gray-400 rounded-lg focus:ring-2 focus:ring-[#FF9900] focus:border-transparent outline-none transition-all"
              />
            </div>
          </form>

          {/* Right Side */}
          <div className="flex items-center gap-3">
            <a
              href="https://t.me/firsatradaricom"
              target="_blank"
              className="hidden lg:inline-flex items-center gap-2 bg-[#FF9900] hover:bg-[#FF9900]/90 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              <Send className="h-4 w-4" />
              Katıl
            </a>
            
            <button
              className="md:hidden p-2 text-white hover:text-[#FF9900]"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Search */}
        <div className="md:hidden pb-4">
          <form onSubmit={handleSearch}>
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Ara..."
                className="w-full pl-9 pr-4 py-1.5 text-sm bg-white border border-gray-300 text-gray-900 placeholder:text-gray-400 rounded-lg focus:ring-2 focus:ring-[#FF9900] focus:border-transparent outline-none"
              />
            </div>
          </form>
        </div>
      </div>

      {/* Navigation */}
      <nav className={`border-t border-gray-700 ${mobileMenuOpen ? 'block' : 'hidden md:block'}`}>
        <div className="container mx-auto px-4">
          <ul className="flex flex-col md:flex-row md:items-center md:justify-center">
            {/* Ana Sayfa */}
            <li>
              <Link 
                href="/" 
                className="block px-5 py-3 text-white hover:text-[#FF9900] text-sm transition-colors"
              >
                Ana Sayfa
              </Link>
            </li>

            {/* Separator */}
            <li className="hidden md:block text-gray-500">|</li>

            {/* Categories */}
            {categoryTree.slice(0, 6).map((parentCategory, index) => (
              <li key={parentCategory.id} className="relative group">
                <Link
                  href={`/kategori/${parentCategory.slug}`}
                  className="flex items-center gap-1 px-5 py-3 text-white hover:text-[#FF9900] text-sm transition-colors"
                >
                  {parentCategory.name}
                  {parentCategory.children && parentCategory.children.length > 0 && (
                    <ChevronDown className="h-3 w-3" />
                  )}
                </Link>

                {/* Mega Dropdown - 3 Level Support */}
                {parentCategory.children && parentCategory.children.length > 0 && (
                  <div className="md:absolute left-0 top-full min-w-max bg-[#242F3E] md:shadow-xl md:border border-gray-700 z-50 hidden group-hover:block">
                    <div className="py-2 px-2">
                      <div className="flex flex-wrap gap-4 max-w-4xl">
                        {parentCategory.children.map((child) => (
                          <div key={child.id} className="min-w-[200px]">
                            {/* Child Category */}
                            <Link
                              href={`/kategori/${child.slug}`}
                              className="block px-3 py-2 text-sm font-semibold text-[#FF9900] hover:text-[#FF9900]/80 transition-colors"
                            >
                              {child.name}
                            </Link>
                            
                            {/* Grandchildren (3rd level) */}
                            {child.children && child.children.length > 0 && (
                              <div className="ml-2 mt-1 space-y-1">
                                {child.children.map((grandchild) => (
                                  <Link
                                    key={grandchild.id}
                                    href={`/kategori/${grandchild.slug}`}
                                    className="block px-3 py-1.5 text-xs text-gray-300 hover:text-white hover:bg-[#FF9900]/20 rounded transition-colors"
                                  >
                                    {grandchild.name}
                                  </Link>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {index < Math.min(categoryTree.length - 1, 5) && (
                  <span className="hidden md:block absolute right-0 top-1/2 -translate-y-1/2 text-gray-500">|</span>
                )}
              </li>
            ))}

            {categoryTree.length > 6 && (
              <>
                <li className="hidden md:block text-gray-500">|</li>
                <li>
                  <Link
                    href="/kategoriler"
                    className="block px-5 py-3 text-[#FF9900] hover:text-[#FF9900]/80 text-sm transition-colors"
                  >
                    Tümü
                  </Link>
                </li>
              </>
            )}
          </ul>
        </div>
      </nav>
    </header>
  )
}
