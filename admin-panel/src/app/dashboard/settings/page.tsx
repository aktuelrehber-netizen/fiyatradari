'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { settingsAPI } from '@/utils/api-client'
import { Save, Eye, EyeOff } from 'lucide-react'
import { TelegramTemplateEditor } from '@/components/telegram-template-editor'

interface Setting {
  key: string
  value: string
  data_type: string
  description: string
  group: string
  is_secret?: boolean
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Setting[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showSecrets, setShowSecrets] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const data = await settingsAPI.list()
      setSettings(data)
    } catch (error) {
      // Silent fail - will show empty state
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (key: string, value: string) => {
    setSaving(true)
    try {
      await settingsAPI.update(key, { value })
      alert('Ayar kaydedildi')
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Kaydetme başarısız oldu')
    } finally {
      setSaving(false)
    }
  }

  const groupSettings = (group: string) => {
    return settings.filter(s => s.group === group)
  }

  const isSecretField = (key: string) => {
    return key.includes('secret') || key.includes('password') || key.includes('token')
  }

  if (loading) {
    return <div className="text-center py-12">Yükleniyor...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Ayarlar</h1>
          <p className="text-gray-500 mt-1">
            Sistem ayarlarını ve entegrasyonları yönetin
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => setShowSecrets(!showSecrets)}
        >
          {showSecrets ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
          {showSecrets ? 'Gizli Alanları Gizle' : 'Gizli Alanları Göster'}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Amazon Product Advertising API</CardTitle>
          <CardDescription>
            Amazon PA API bağlantı ayarları
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {groupSettings('amazon').map((setting) => (
            <div key={setting.key} className="space-y-2">
              <Label>{setting.description || setting.key}</Label>
              <div className="flex gap-2">
                <Input
                  type={isSecretField(setting.key) && !showSecrets ? 'password' : 'text'}
                  defaultValue={setting.value}
                  id={setting.key}
                  placeholder={setting.description}
                />
                <Button
                  onClick={() => {
                    const input = document.getElementById(setting.key) as HTMLInputElement
                    handleSave(setting.key, input.value)
                  }}
                  disabled={saving}
                >
                  <Save className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Telegram Bot</CardTitle>
          <CardDescription>
            Telegram bot token ve kanal ayarları
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {groupSettings('telegram')
            .filter((s) => !s.key.includes('template'))
            .map((setting) => (
              <div key={setting.key} className="space-y-2">
                <Label>{setting.description || setting.key}</Label>
                <div className="flex gap-2">
                  <Input
                    type={isSecretField(setting.key) && !showSecrets ? 'password' : 'text'}
                    defaultValue={setting.value}
                    id={setting.key}
                    placeholder={setting.description}
                  />
                  <Button
                    onClick={() => {
                      const input = document.getElementById(setting.key) as HTMLInputElement
                      handleSave(setting.key, input.value)
                    }}
                    disabled={saving}
                  >
                    <Save className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>🌐 Proxy Settings</CardTitle>
          <CardDescription>
            Web crawler için proxy ayarları (bot detection bypass)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {groupSettings('proxy').length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-gray-500 mb-4">
                Proxy ayarları henüz eklenmemiş. Veritabanına seed edilmesi gerekiyor.
              </p>
              <code className="text-xs bg-gray-100 p-2 rounded block">
                python backend/scripts/seed_proxy_settings.py
              </code>
            </div>
          ) : (
            <>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-900 mb-2">
                  <strong>💡 Not:</strong> Proxy ayarları worker container'ında environment variable olarak kullanılır.
                </p>
                <p className="text-xs text-blue-700 mt-2">
                  Değişiklikler için worker'ı restart etmelisiniz: <code className="bg-blue-100 px-1 rounded">docker compose restart celery_worker</code>
                </p>
              </div>
              
              {groupSettings('proxy').map((setting) => (
                <div key={setting.key} className="space-y-2">
                  <Label>{setting.description || setting.key}</Label>
                  <div className="flex gap-2">
                    <Input
                      type={(setting.is_secret || isSecretField(setting.key)) && !showSecrets ? 'password' : 'text'}
                      defaultValue={setting.value}
                      id={setting.key}
                      placeholder={setting.description}
                    />
                    <Button
                      onClick={() => {
                        const input = document.getElementById(setting.key) as HTMLInputElement
                        handleSave(setting.key, input.value)
                      }}
                      disabled={saving}
                    >
                      <Save className="h-4 w-4" />
                    </Button>
                  </div>
                  {setting.key === 'proxy_enabled' && (
                    <p className="text-xs text-gray-500">
                      Proxy kullanımını aktif/pasif etmek için: true veya false
                    </p>
                  )}
                  {setting.key === 'http_proxy' && (
                    <p className="text-xs text-gray-500">
                      Format: http://user:pass@proxy.com:8080
                    </p>
                  )}
                  {setting.key === 'proxy_list' && (
                    <p className="text-xs text-gray-500">
                      Virgülle ayrılmış: proxy1.com:8080,proxy2.com:8080
                    </p>
                  )}
                </div>
              ))}
              
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mt-4">
                <p className="text-sm text-amber-900 font-semibold mb-2">
                  ⚠️ Üç Proxy Yöntemi:
                </p>
                <ol className="text-xs text-amber-800 space-y-1 ml-4 list-decimal">
                  <li><strong>Tek Proxy:</strong> http_proxy field'ını doldur (diğerlerini boş bırak)</li>
                  <li><strong>Proxy Listesi:</strong> proxy_list field'ını doldur (rotation için)</li>
                  <li><strong>Premium Proxy:</strong> host, port, user, pass field'larını doldur</li>
                </ol>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <TelegramTemplateEditor onSave={() => {
        loadSettings()
      }} />
    </div>
  )
}
