'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Search, Package, Barcode, Star, ShoppingCart, ExternalLink, CheckCircle, XCircle } from 'lucide-react'
import Image from 'next/image'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ProductData {
  asin: string
  title: string
  brand?: string
  current_price?: number
  currency: string
  image_url?: string
  detail_page_url?: string
  rating?: number
  review_count?: number
  is_available: boolean
  availability?: string
  is_prime: boolean
  ean?: string
  upc?: string
  isbn?: string
}

interface BulkResult {
  asin: string
  title?: string
  ean?: string
  upc?: string
  isbn?: string
  error?: string
}

interface BulkResponse {
  results: BulkResult[]
  total: number
  successful: number
  failed: number
}

interface SearchResult {
  asin: string
  title: string
  brand?: string
  current_price?: number
  currency: string
  image_url?: string
  detail_page_url?: string
  ean?: string
  upc?: string
  isbn?: string
}

interface SearchResponse {
  results: SearchResult[]
  total: number
  keyword: string
}

export default function ASINLookupPage() {
  const [asin, setAsin] = useState('')
  const [loading, setLoading] = useState(false)
  const [product, setProduct] = useState<ProductData | null>(null)
  const [error, setError] = useState('')
  
  // Bulk lookup state
  const [bulkAsins, setBulkAsins] = useState('')
  const [bulkLoading, setBulkLoading] = useState(false)
  const [bulkResults, setBulkResults] = useState<BulkResponse | null>(null)
  const [bulkError, setBulkError] = useState('')
  
  // Product search state
  const [searchKeyword, setSearchKeyword] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null)
  const [searchError, setSearchError] = useState('')
  
  const [activeTab, setActiveTab] = useState<'single' | 'bulk' | 'search'>('single')

  const handleLookup = async () => {
    if (!asin.trim()) {
      setError('Lütfen bir ASIN girin')
      return
    }

    setLoading(true)
    setError('')
    setProduct(null)

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_URL}/api/v1/amazon/lookup-asin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ asin: asin.trim() })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Ürün bulunamadı')
      }

      const data = await response.json()
      setProduct(data)
    } catch (err: any) {
      setError(err.message || 'Bir hata oluştu')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleLookup()
    }
  }

  const handleBulkLookup = async () => {
    if (!bulkAsins.trim()) {
      setBulkError('Lütfen en az bir ASIN girin')
      return
    }

    // Parse ASINs from textarea (newline or comma separated)
    const asinList = bulkAsins
      .split(/[\n,]/)
      .map(a => a.trim().toUpperCase())
      .filter(a => a.length > 0)

    if (asinList.length === 0) {
      setBulkError('Geçerli ASIN bulunamadı')
      return
    }

    if (asinList.length > 100) {
      setBulkError('Maksimum 100 ASIN sorgulanabilir')
      return
    }

    setBulkLoading(true)
    setBulkError('')
    setBulkResults(null)

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_URL}/api/v1/amazon/bulk-lookup-asin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ asins: asinList })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Toplu sorgulama başarısız')
      }

      const data = await response.json()
      setBulkResults(data)
    } catch (err: any) {
      setBulkError(err.message || 'Bir hata oluştu')
    } finally {
      setBulkLoading(false)
    }
  }

  const copyResultsToClipboard = () => {
    if (!bulkResults) return

    const text = bulkResults.results.map(r => {
      const barcode = r.ean || r.upc || r.isbn || 'Yok'
      return `${r.asin}\t${barcode}\t${r.title || r.error || 'N/A'}`
    }).join('\n')

    navigator.clipboard.writeText(text)
    alert('Sonuçlar panoya kopyalandı!')
  }

  const handleProductSearch = async () => {
    if (!searchKeyword.trim()) {
      setSearchError('Lütfen bir ürün adı girin')
      return
    }

    setSearchLoading(true)
    setSearchError('')
    setSearchResults(null)

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_URL}/api/v1/amazon/search-products`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          keyword: searchKeyword.trim(),
          max_results: 10
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Arama başarısız')
      }

      const data = await response.json()
      setSearchResults(data)
    } catch (err: any) {
      setSearchError(err.message || 'Bir hata oluştu')
    } finally {
      setSearchLoading(false)
    }
  }

  const handleSearchKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleProductSearch()
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">ASIN Sorgulama</h1>
        <p className="text-sm text-gray-500 mt-1">
          Amazon ASIN ile ürün bilgilerini ve barkod bilgisini sorgulayın
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('single')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'single'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Tekli Sorgulama
        </button>
        <button
          onClick={() => setActiveTab('bulk')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'bulk'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Toplu Sorgulama
        </button>
        <button
          onClick={() => setActiveTab('search')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'search'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Ürün Ara
        </button>
      </div>

      {/* Single Search Card */}
      {activeTab === 'single' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              ASIN Girişi
            </CardTitle>
            <CardDescription>
              Amazon Product ASIN kodunu girin (örn: B07684M7WV)
            </CardDescription>
          </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="ASIN kodunu girin..."
              value={asin}
              onChange={(e) => setAsin(e.target.value.toUpperCase())}
              onKeyPress={handleKeyPress}
              className="font-mono"
              maxLength={10}
            />
            <Button onClick={handleLookup} disabled={loading}>
              {loading ? 'Sorgulanıyor...' : 'Sorgula'}
            </Button>
          </div>
          {error && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
              <XCircle className="h-4 w-4" />
              {error}
            </div>
          )}
        </CardContent>
      </Card>
      )}

      {/* Bulk Search Card */}
      {activeTab === 'bulk' && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Toplu ASIN Girişi
              </CardTitle>
              <CardDescription>
                Her satıra bir ASIN veya virgülle ayırarak girin (Max: 100 ASIN)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <textarea
                  className="w-full min-h-[200px] p-3 border rounded-lg font-mono text-sm"
                  placeholder="B07684M7WV&#10;B0FRYMF193, B0FFHHWWTB&#10;..."
                  value={bulkAsins}
                  onChange={(e) => setBulkAsins(e.target.value)}
                />
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">
                    {bulkAsins.split(/[\n,]/).filter(a => a.trim()).length} ASIN girildi
                  </span>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={() => setBulkAsins('')}
                      disabled={bulkLoading || !bulkAsins}
                    >
                      Temizle
                    </Button>
                    <Button onClick={handleBulkLookup} disabled={bulkLoading}>
                      {bulkLoading ? 'Sorgulanıyor...' : 'Toplu Sorgula'}
                    </Button>
                  </div>
                </div>
                {bulkError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
                    <XCircle className="h-4 w-4" />
                    {bulkError}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Bulk Results */}
          {bulkResults && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Barcode className="h-5 w-5" />
                      Sorgulama Sonuçları
                    </CardTitle>
                    <CardDescription className="mt-1">
                      <Badge variant="outline" className="mr-2">
                        Toplam: {bulkResults.total}
                      </Badge>
                      <Badge variant="outline" className="mr-2 bg-green-50 text-green-700 border-green-200">
                        Başarılı: {bulkResults.successful}
                      </Badge>
                      {bulkResults.failed > 0 && (
                        <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                          Başarısız: {bulkResults.failed}
                        </Badge>
                      )}
                    </CardDescription>
                  </div>
                  <Button onClick={copyResultsToClipboard} variant="outline" size="sm">
                    📋 Kopyala
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="text-left p-3 font-medium">ASIN</th>
                        <th className="text-left p-3 font-medium">Barkod (EAN/UPC/ISBN)</th>
                        <th className="text-left p-3 font-medium">Başlık</th>
                        <th className="text-left p-3 font-medium">Durum</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bulkResults.results.map((result, index) => (
                        <tr key={index} className="border-b last:border-0 hover:bg-gray-50">
                          <td className="p-3 font-mono font-semibold">{result.asin}</td>
                          <td className="p-3 font-mono">
                            {result.ean && (
                              <div className="flex items-center gap-1">
                                <Badge variant="outline" className="text-xs">EAN</Badge>
                                <span className="font-semibold">{result.ean}</span>
                              </div>
                            )}
                            {!result.ean && result.upc && (
                              <div className="flex items-center gap-1">
                                <Badge variant="outline" className="text-xs">UPC</Badge>
                                <span className="font-semibold">{result.upc}</span>
                              </div>
                            )}
                            {!result.ean && !result.upc && result.isbn && (
                              <div className="flex items-center gap-1">
                                <Badge variant="outline" className="text-xs">ISBN</Badge>
                                <span className="font-semibold">{result.isbn}</span>
                              </div>
                            )}
                            {!result.ean && !result.upc && !result.isbn && !result.error && (
                              <span className="text-gray-400 italic">Yok</span>
                            )}
                            {result.error && <span className="text-gray-400 italic">-</span>}
                          </td>
                          <td className="p-3 text-xs max-w-md truncate">
                            {result.title || '-'}
                          </td>
                          <td className="p-3">
                            {result.error ? (
                              <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200 text-xs">
                                {result.error}
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 text-xs">
                                ✓ Başarılı
                              </Badge>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Product Search */}
      {activeTab === 'search' && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Ürün Adı ile Ara
              </CardTitle>
              <CardDescription>
                Ürün adını girin ve Amazon'da arayın (Max: 10 sonuç)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Input
                  placeholder="Örn: Kahve makinesi, laptop..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  onKeyPress={handleSearchKeyPress}
                />
                <Button onClick={handleProductSearch} disabled={searchLoading}>
                  {searchLoading ? 'Aranıyor...' : 'Ara'}
                </Button>
              </div>
              {searchError && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
                  <XCircle className="h-4 w-4" />
                  {searchError}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Search Results */}
          {searchResults && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  Arama Sonuçları
                </CardTitle>
                <CardDescription>
                  &quot;{searchResults.keyword}&quot; için {searchResults.total} sonuç bulundu
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {searchResults.results.map((result, index) => (
                    <div key={index} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex gap-4">
                        {/* Image */}
                        <div className="flex-shrink-0">
                          {result.image_url ? (
                            <div className="relative w-20 h-20">
                              <Image
                                src={result.image_url}
                                alt={result.title}
                                fill
                                sizes="80px"
                                className="object-contain rounded"
                              />
                            </div>
                          ) : (
                            <div className="w-20 h-20 bg-gray-100 rounded flex items-center justify-center">
                              <Package className="h-8 w-8 text-gray-300" />
                            </div>
                          )}
                        </div>

                        {/* Details */}
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-sm mb-1 line-clamp-2">
                            {result.title}
                          </h3>
                          
                          {result.brand && (
                            <Badge variant="outline" className="text-xs mb-2">
                              {result.brand}
                            </Badge>
                          )}

                          <div className="space-y-1 text-xs">
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500">ASIN:</span>
                              <span className="font-mono font-semibold">{result.asin}</span>
                            </div>
                            
                            {result.current_price && (
                              <div className="flex items-center gap-2">
                                <span className="text-gray-500">Fiyat:</span>
                                <span className="font-semibold text-green-600">
                                  {result.current_price.toFixed(2)} {result.currency}
                                </span>
                              </div>
                            )}

                            {/* Barcodes */}
                            <div className="pt-2 border-t space-y-1">
                              {result.ean && (
                                <div className="flex items-center gap-1">
                                  <Badge variant="outline" className="text-xs">EAN</Badge>
                                  <span className="font-mono text-xs">{result.ean}</span>
                                </div>
                              )}
                              {result.upc && (
                                <div className="flex items-center gap-1">
                                  <Badge variant="outline" className="text-xs">UPC</Badge>
                                  <span className="font-mono text-xs">{result.upc}</span>
                                </div>
                              )}
                              {result.isbn && (
                                <div className="flex items-center gap-1">
                                  <Badge variant="outline" className="text-xs">ISBN</Badge>
                                  <span className="font-mono text-xs">{result.isbn}</span>
                                </div>
                              )}
                              {!result.ean && !result.upc && !result.isbn && (
                                <span className="text-gray-400 italic text-xs">Barkod yok</span>
                              )}
                            </div>
                          </div>

                          {result.detail_page_url && (
                            <a
                              href={result.detail_page_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 mt-2"
                            >
                              <ExternalLink className="h-3 w-3" />
                              Amazon&apos;da Gör
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Product Result */}
      {activeTab === 'single' && product && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Product Image and Basic Info */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Ürün Bilgileri
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Image */}
                <div className="flex justify-center items-start">
                  {product.image_url ? (
                    <div className="relative w-full aspect-square max-w-[200px]">
                      <Image
                        src={product.image_url}
                        alt={product.title}
                        fill
                        sizes="200px"
                        className="object-contain"
                      />
                    </div>
                  ) : (
                    <div className="w-full aspect-square max-w-[200px] bg-gray-100 rounded-lg flex items-center justify-center">
                      <Package className="h-16 w-16 text-gray-300" />
                    </div>
                  )}
                </div>

                {/* Details */}
                <div className="md:col-span-2 space-y-4">
                  <div>
                    <h3 className="font-semibold text-lg mb-2">{product.title}</h3>
                    {product.brand && (
                      <Badge variant="outline" className="mb-2">{product.brand}</Badge>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">ASIN:</span>
                      <p className="font-mono font-semibold">{product.asin}</p>
                    </div>
                    
                    {product.current_price && (
                      <div>
                        <span className="text-gray-500">Fiyat:</span>
                        <p className="font-semibold text-lg text-green-600">
                          {product.current_price.toFixed(2)} {product.currency}
                        </p>
                      </div>
                    )}

                    <div>
                      <span className="text-gray-500">Stok Durumu:</span>
                      <p className="flex items-center gap-1 mt-1">
                        {product.is_available ? (
                          <>
                            <CheckCircle className="h-4 w-4 text-green-500" />
                            <span className="text-green-600">Stokta</span>
                          </>
                        ) : (
                          <>
                            <XCircle className="h-4 w-4 text-red-500" />
                            <span className="text-red-600">Stok Dışı</span>
                          </>
                        )}
                      </p>
                    </div>

                    {/* Rating & Reviews - DEBUG SECTION */}
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <Star className="h-4 w-4 text-yellow-600" />
                        <span className="font-semibold text-yellow-900">Customer Reviews (DEBUG)</span>
                      </div>
                      
                      {product.rating ? (
                        <div className="space-y-1">
                          <p className="flex items-center gap-2">
                            <span className="text-sm text-gray-600">Rating:</span>
                            <span className="font-bold text-lg text-yellow-600">{product.rating.toFixed(1)}</span>
                            <span className="text-xs text-green-600 font-semibold">✓ API'den geldi</span>
                          </p>
                          <p className="flex items-center gap-2">
                            <span className="text-sm text-gray-600">Review Count:</span>
                            <span className="font-bold text-lg">{product.review_count?.toLocaleString('tr-TR') || 0}</span>
                            {product.review_count ? (
                              <span className="text-xs text-green-600 font-semibold">✓ API'den geldi</span>
                            ) : (
                              <span className="text-xs text-orange-600 font-semibold">⚠ API'den gelmedi</span>
                            )}
                          </p>
                        </div>
                      ) : (
                        <div className="bg-red-50 border border-red-200 rounded p-2">
                          <p className="text-red-700 font-semibold text-sm flex items-center gap-2">
                            <XCircle className="h-4 w-4" />
                            ❌ Rating API'den GELMEDİ!
                          </p>
                          <p className="text-xs text-red-600 mt-1">
                            Amazon PA-API customer_reviews döndürmüyor olabilir.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="pt-4 border-t flex gap-2">
                    {product.is_prime && (
                      <Badge className="bg-blue-500">Prime</Badge>
                    )}
                    {product.detail_page_url && (
                      <a
                        href={product.detail_page_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
                      >
                        <ExternalLink className="h-4 w-4" />
                        Amazon'da Görüntüle
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Barcode Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Barcode className="h-5 w-5" />
                Barkod Bilgileri
              </CardTitle>
              <CardDescription>
                Ürüne ait barkod numaraları
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* EAN */}
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-gray-500">EAN</span>
                  <Badge variant="outline" className="text-xs">European Article Number</Badge>
                </div>
                {product.ean ? (
                  <p className="font-mono text-lg font-semibold bg-gray-50 p-2 rounded border border-gray-200">
                    {product.ean}
                  </p>
                ) : (
                  <p className="text-sm text-gray-400 italic">Bilgi yok</p>
                )}
              </div>

              {/* UPC */}
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-gray-500">UPC</span>
                  <Badge variant="outline" className="text-xs">Universal Product Code</Badge>
                </div>
                {product.upc ? (
                  <p className="font-mono text-lg font-semibold bg-gray-50 p-2 rounded border border-gray-200">
                    {product.upc}
                  </p>
                ) : (
                  <p className="text-sm text-gray-400 italic">Bilgi yok</p>
                )}
              </div>

              {/* ISBN */}
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-gray-500">ISBN</span>
                  <Badge variant="outline" className="text-xs">Book Identifier</Badge>
                </div>
                {product.isbn ? (
                  <p className="font-mono text-lg font-semibold bg-gray-50 p-2 rounded border border-gray-200">
                    {product.isbn}
                  </p>
                ) : (
                  <p className="text-sm text-gray-400 italic">Bilgi yok</p>
                )}
              </div>

              {!product.ean && !product.upc && !product.isbn && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800 text-sm">
                  ⚠️ Bu ürün için Amazon'da barkod bilgisi bulunamadı
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
