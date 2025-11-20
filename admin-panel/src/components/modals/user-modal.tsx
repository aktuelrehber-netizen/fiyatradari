'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { usersAPI } from '@/utils/api-client'
import { useToast } from '@/hooks/use-toast'

interface User {
  id?: number
  username: string
  email: string
  full_name: string
  password?: string
  is_active: boolean
  is_admin: boolean
}

interface UserModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  user?: User | null
  onSuccess?: () => void
}

export function UserModal({ open, onOpenChange, user, onSuccess }: UserModalProps) {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState<User>({
    username: '',
    email: '',
    full_name: '',
    password: '',
    is_active: true,
    is_admin: false,
  })

  useEffect(() => {
    if (user) {
      setFormData({
        ...user,
        password: '',
      })
    } else {
      setFormData({
        username: '',
        email: '',
        full_name: '',
        password: '',
        is_active: true,
        is_admin: false,
      })
    }
  }, [user, open])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const payload = { ...formData }
      if (user?.id && !payload.password) {
        delete payload.password
      }

      if (user?.id) {
        await usersAPI.update(user.id, payload)
        toast({
          title: 'Başarılı',
          description: 'Kullanıcı güncellendi',
          variant: 'success',
        })
      } else {
        await usersAPI.create(payload)
        toast({
          title: 'Başarılı',
          description: 'Kullanıcı oluşturuldu',
          variant: 'success',
        })
      }
      onOpenChange(false)
      onSuccess?.()
    } catch (error: any) {
      toast({
        title: 'Hata',
        description: error.response?.data?.detail || 'İşlem başarısız oldu',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {user ? 'Kullanıcı Düzenle' : 'Yeni Kullanıcı Ekle'}
            </DialogTitle>
            <DialogDescription>
              Admin panel erişimi için kullanıcı bilgilerini girin.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="username">Kullanıcı Adı *</Label>
              <Input
                id="username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                placeholder="johndoe"
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="email">Email *</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="john@example.com"
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="full_name">Tam Ad</Label>
              <Input
                id="full_name"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                placeholder="John Doe"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="password">
                Şifre {user ? '(Değiştirmek için girin)' : '*'}
              </Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="••••••••"
                required={!user}
              />
              {user && (
                <p className="text-xs text-gray-500">
                  Boş bırakırsanız şifre değişmez
                </p>
              )}
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border p-3">
                <div className="space-y-0.5">
                  <Label htmlFor="is_active">Aktif</Label>
                  <p className="text-xs text-gray-500">
                    Kullanıcı giriş yapabilsin mi?
                  </p>
                </div>
                <Switch
                  id="is_active"
                  checked={formData.is_active}
                  onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                />
              </div>

              <div className="flex items-center justify-between rounded-lg border p-3">
                <div className="space-y-0.5">
                  <Label htmlFor="is_admin">Admin Yetkisi</Label>
                  <p className="text-xs text-gray-500">
                    Tüm yönetim yetkilerine erişim
                  </p>
                </div>
                <Switch
                  id="is_admin"
                  checked={formData.is_admin}
                  onCheckedChange={(checked) => setFormData({ ...formData, is_admin: checked })}
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              İptal
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Kaydediliyor...' : user ? 'Güncelle' : 'Oluştur'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
