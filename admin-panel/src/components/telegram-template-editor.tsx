'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { settingsAPI } from '@/utils/api-client'
import { Eye, Save, Loader2, Info } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

interface TelegramTemplateEditorProps {
  onSave?: () => void
}

export function TelegramTemplateEditor({ onSave }: TelegramTemplateEditorProps) {
  const { toast } = useToast()
  const [template, setTemplate] = useState('')
  const [preview, setPreview] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [previewing, setPreviewing] = useState(false)

  // Available variables
  const variables = [
    { name: '{title}', desc: 'Ürün başlığı' },
    { name: '{brand_line}', desc: 'Marka satırı (otomatik)' },
    { name: '{cheapest_badge}', desc: '🏆 En ucuz badge (otomatik)' },
    { name: '{discount_percentage}', desc: 'İndirim %' },
    { name: '{original_price}', desc: 'Orijinal fiyat' },
    { name: '{deal_price}', desc: 'İndirimli fiyat' },
    { name: '{previous_price}', desc: 'Önceki fiyat (price history)' },
    { name: '{discount_amount}', desc: 'İndirim miktarı (TL)' },
    { name: '{rating}', desc: 'Yıldız puanı (4.5)' },
    { name: '{review_count}', desc: 'Değerlendirme sayısı (150)' },
    { name: '{rating_line}', desc: 'Yıldız satırı (otomatik, ⭐⭐⭐⭐ 4.5/5)' },
    { name: '{product_url}', desc: 'Affiliate link' },
    { name: '{is_cheapest_14days}', desc: '14 günün en ucuzu mu? (true/false)' },
    { name: '{is_cheapest_1month}', desc: '1 ayın en ucuzu mu? (true/false)' },
    { name: '{is_cheapest_3months}', desc: '3 ayın en ucuzu mu? (true/false)' },
    { name: '{is_cheapest_6months}', desc: '6 ayın en ucuzu mu? (true/false)' },
  ]

  useEffect(() => {
    loadTemplate()
  }, [])

  const loadTemplate = async () => {
    try {
      const settings = await settingsAPI.list('telegram')
      const templateSetting = settings.find((s: any) => s.key === 'telegram_message_template')
      
      if (templateSetting) {
        setTemplate(templateSetting.value)
      }
    } catch (error) {
      console.error('Template yüklenemedi:', error)
      toast({
        title: 'Hata',
        description: 'Şablon yüklenirken hata oluştu',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await settingsAPI.update('telegram_message_template', { value: template })
      
      toast({
        title: 'Başarılı',
        description: 'Telegram şablonu kaydedildi',
      })
      
      if (onSave) {
        onSave()
      }
    } catch (error: any) {
      toast({
        title: 'Hata',
        description: error.response?.data?.detail || 'Kaydetme başarısız oldu',
        variant: 'destructive',
      })
    } finally {
      setSaving(false)
    }
  }

  const handlePreview = async () => {
    setPreviewing(true)
    try {
      const response = await fetch('/api/v1/settings/telegram/preview-template', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ template }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Önizleme başarısız')
      }

      const data = await response.json()
      setPreview(data)
    } catch (error: any) {
      toast({
        title: 'Hata',
        description: error.message || 'Önizleme oluşturulamadı',
        variant: 'destructive',
      })
    } finally {
      setPreviewing(false)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto" />
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Telegram Mesaj Şablonu</CardTitle>
          <CardDescription>
            Telegram'a gönderilecek fırsat mesajlarının formatını özelleştirin
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium">Şablon</label>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePreview}
                  disabled={previewing || !template}
                >
                  {previewing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Hazırlanıyor...
                    </>
                  ) : (
                    <>
                      <Eye className="h-4 w-4 mr-2" />
                      Önizleme
                    </>
                  )}
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={saving || !template}
                  size="sm"
                >
                  {saving ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Kaydediliyor...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Kaydet
                    </>
                  )}
                </Button>
              </div>
            </div>
            <Textarea
              value={template}
              onChange={(e) => setTemplate(e.target.value)}
              rows={12}
              className="font-mono text-sm"
              placeholder="Telegram mesaj şablonunu buraya yazın..."
            />
            <p className="text-xs text-gray-500 mt-2">
              HTML formatı desteklenir: &lt;b&gt;kalın&lt;/b&gt;, &lt;i&gt;italik&lt;/i&gt;, &lt;s&gt;üstü çizili&lt;/s&gt;, &lt;a href=""&gt;link&lt;/a&gt;
            </p>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-2">
              <Info className="h-4 w-4 text-blue-500" />
              <label className="text-sm font-medium">Kullanılabilir Değişkenler</label>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {variables.map((variable) => (
                <div
                  key={variable.name}
                  className="flex items-center justify-between p-2 border rounded-lg cursor-pointer hover:bg-gray-50"
                  onClick={() => {
                    setTemplate((prev) => prev + variable.name)
                  }}
                >
                  <Badge variant="outline" className="font-mono text-xs">
                    {variable.name}
                  </Badge>
                  <span className="text-xs text-gray-600">{variable.desc}</span>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Değişkenlere tıklayarak şablona ekleyebilirsiniz
            </p>
          </div>
        </CardContent>
      </Card>

      {preview && (
        <Card>
          <CardHeader>
            <CardTitle>Önizleme</CardTitle>
            <CardDescription>
              {preview.preview}
              {!preview.is_sample && preview.deal_title && (
                <span className="block mt-1 text-sm">
                  Ürün: {preview.deal_title}
                </span>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-50 border rounded-lg p-4">
              <div 
                className="whitespace-pre-wrap text-sm"
                dangerouslySetInnerHTML={{ 
                  __html: preview.rendered
                    .replace(/<b>/g, '<strong>')
                    .replace(/<\/b>/g, '</strong>')
                    .replace(/<s>/g, '<del>')
                    .replace(/<\/s>/g, '</del>')
                    .replace(/<i>/g, '<em>')
                    .replace(/<\/i>/g, '</em>')
                }}
              />
            </div>
            {preview.is_sample && (
              <p className="text-xs text-amber-600 mt-2">
                ⚠️ Bu bir örnek önizleme. Gerçek ürün verisi eklendiğinde daha doğru görünüm elde edeceksiniz.
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
