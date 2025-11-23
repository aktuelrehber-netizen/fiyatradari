'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Search, Menu, X, ChevronDown, Send, ChevronRight } from 'lucide-react'
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
  const [expandedCategories, setExpandedCategories] = useState<Set<number>>(new Set())

  const categoryTree = buildCategoryTree(categories)

  // Prevent body scroll when drawer is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [mobileMenuOpen])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: Implement search functionality
  }

  const toggleCategory = (categoryId: number) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev)
      if (newSet.has(categoryId)) {
        newSet.delete(categoryId)
      } else {
        newSet.add(categoryId)
      }
      return newSet
    })
  }

  return (
    <>
      <header className="bg-[#242F3E] border-b border-gray-700 sticky top-0 z-50 shadow-lg">
        {/* Main Header */}
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between py-4">
            {/* Mobile: Hamburger (left) */}
            <button
              className="md:hidden p-2 text-white hover:text-[#FF9900] -ml-2"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Menüyü aç"
            >
              <Menu className="h-6 w-6" />
            </button>

            {/* Logo - Desktop: left, Mobile: center */}
            <Link href="/" className="group md:mr-0 absolute left-1/2 -translate-x-1/2 md:static md:translate-x-0">
              <Logo className="group-hover:scale-105 transition-transform" />
            </Link>

            {/* Search Bar - Desktop Only */}
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
              {/* Desktop: Full button */}
              <a
                href="https://t.me/firsatradaricom"
                target="_blank"
                className="hidden lg:inline-flex items-center gap-2 bg-[#FF9900] hover:bg-[#FF9900]/90 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                <Send className="h-4 w-4" />
                Katıl
              </a>
              
              {/* Mobile: Icon only */}
              <a
                href="https://t.me/firsatradaricom"
                target="_blank"
                className="lg:hidden p-2 text-[#FF9900] hover:text-[#FF9900]/80 transition-colors"
                aria-label="Telegram kanalına katıl"
              >
                <Send className="h-6 w-6" />
              </a>
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

        {/* Desktop Navigation */}
        <nav className="hidden md:block border-t border-gray-700">
          <div className="container mx-auto px-4">
            <ul className="flex items-center justify-center">
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

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <>
          {/* Overlay */}
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
            onClick={() => setMobileMenuOpen(false)}
          />
          
          {/* Drawer */}
          <div className="fixed top-0 left-0 bottom-0 w-[280px] bg-[#242F3E] z-50 md:hidden shadow-2xl animate-slide-in">
            {/* Drawer Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <Logo />
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="p-2 text-white hover:text-[#FF9900] transition-colors"
                aria-label="Menüyü kapat"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Drawer Content */}
            <div className="overflow-y-auto h-[calc(100vh-73px)]">
              <nav className="py-4">
                {/* Ana Sayfa */}
                <Link
                  href="/"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center px-6 py-3 text-white hover:bg-[#FF9900]/10 hover:text-[#FF9900] transition-colors"
                >
                  Ana Sayfa
                </Link>

                {/* Categories */}
                <div className="mt-2">
                  {categoryTree.map((parentCategory) => (
                    <div key={parentCategory.id}>
                      {/* Parent Category */}
                      <button
                        onClick={() => {
                          if (parentCategory.children && parentCategory.children.length > 0) {
                            toggleCategory(parentCategory.id)
                          } else {
                            setMobileMenuOpen(false)
                            window.location.href = `/kategori/${parentCategory.slug}`
                          }
                        }}
                        className="w-full flex items-center justify-between px-6 py-3 text-white hover:bg-[#FF9900]/10 hover:text-[#FF9900] transition-colors"
                      >
                        <span>{parentCategory.name}</span>
                        {parentCategory.children && parentCategory.children.length > 0 && (
                          <ChevronRight
                            className={`h-4 w-4 transition-transform ${
                              expandedCategories.has(parentCategory.id) ? 'rotate-90' : ''
                            }`}
                          />
                        )}
                      </button>

                      {/* Child Categories */}
                      {expandedCategories.has(parentCategory.id) &&
                        parentCategory.children &&
                        parentCategory.children.length > 0 && (
                          <div className="bg-[#1a2332] py-1">
                            {parentCategory.children.map((child) => (
                              <div key={child.id}>
                                {/* Child Category */}
                                <button
                                  onClick={() => {
                                    if (child.children && child.children.length > 0) {
                                      toggleCategory(child.id)
                                    } else {
                                      setMobileMenuOpen(false)
                                      window.location.href = `/kategori/${child.slug}`
                                    }
                                  }}
                                  className="w-full flex items-center justify-between px-10 py-2.5 text-sm text-gray-300 hover:bg-[#FF9900]/10 hover:text-[#FF9900] transition-colors"
                                >
                                  <span>{child.name}</span>
                                  {child.children && child.children.length > 0 && (
                                    <ChevronRight
                                      className={`h-3 w-3 transition-transform ${
                                        expandedCategories.has(child.id) ? 'rotate-90' : ''
                                      }`}
                                    />
                                  )}
                                </button>

                                {/* Grandchild Categories */}
                                {expandedCategories.has(child.id) &&
                                  child.children &&
                                  child.children.length > 0 && (
                                    <div className="bg-[#0f1621] py-1">
                                      {child.children.map((grandchild) => (
                                        <Link
                                          key={grandchild.id}
                                          href={`/kategori/${grandchild.slug}`}
                                          onClick={() => setMobileMenuOpen(false)}
                                          className="block px-14 py-2 text-xs text-gray-400 hover:bg-[#FF9900]/10 hover:text-[#FF9900] transition-colors"
                                        >
                                          {grandchild.name}
                                        </Link>
                                      ))}
                                    </div>
                                  )}
                              </div>
                            ))}
                          </div>
                        )}
                    </div>
                  ))}
                </div>

                {/* Tüm Kategoriler */}
                {categoryTree.length > 0 && (
                  <Link
                    href="/kategoriler"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center px-6 py-3 mt-2 text-[#FF9900] hover:bg-[#FF9900]/10 transition-colors font-medium"
                  >
                    Tüm Kategoriler
                  </Link>
                )}
              </nav>

              {/* Telegram CTA */}
              <div className="p-6 border-t border-gray-700">
                <a
                  href="https://t.me/firsatradaricom"
                  target="_blank"
                  className="flex items-center justify-center gap-2 bg-[#FF9900] hover:bg-[#FF9900]/90 text-white px-4 py-3 rounded-lg font-medium transition-colors w-full"
                >
                  <Send className="h-5 w-5" />
                  Telegram Kanalına Katıl
                </a>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  )
}
