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

      <TelegramTemplateEditor onSave={() => {
        loadSettings()
      }} />

      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-900">
          <strong>💡 Not:</strong> Worker ayarları ve Cache yönetimi artık{' '}
          <a href="/dashboard/system" className="underline font-semibold">
            Sistem Yönetimi
          </a>{' '}
          sayfasında bulunmaktadır.
        </p>
      </div>
    </div>
  )
}
