'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { usersAPI } from '@/utils/api-client'
import { Plus, Edit, Trash2, Shield, User, RefreshCw } from 'lucide-react'
import { UserModal } from '@/components/modals/user-modal'
import { useToast } from '@/hooks/use-toast'

interface UserData {
  id: number
  email: string
  username: string
  full_name: string
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export default function UsersPage() {
  const { toast } = useToast()
  const [users, setUsers] = useState<UserData[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<UserData | null>(null)

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      const data = await usersAPI.list()
      setUsers(data)
    } catch (error) {
      // Silent fail - will show empty state
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Bu kullanıcıyı silmek istediğinizden emin misiniz?')) {
      return
    }

    try {
      await usersAPI.delete(id)
      toast({
        title: 'Başarılı',
        description: 'Kullanıcı silindi',
        variant: 'success',
      })
      loadUsers()
    } catch (error: any) {
      toast({
        title: 'Hata',
        description: error.response?.data?.detail || 'Silme işlemi başarısız oldu',
        variant: 'destructive',
      })
    }
  }

  const handleEdit = (user: UserData) => {
    setSelectedUser(user)
    setModalOpen(true)
  }

  const handleCreate = () => {
    setSelectedUser(null)
    setModalOpen(true)
  }

  const handleModalClose = () => {
    setModalOpen(false)
    setSelectedUser(null)
  }

  if (loading) {
    return <div className="text-center py-12">Yükleniyor...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Kullanıcılar</h1>
          <p className="text-gray-500 mt-1">
            Admin panel kullanıcılarını yönetin
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={loadUsers}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Yenile
          </Button>
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Yeni Kullanıcı
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Tüm Kullanıcılar ({users.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Kullanıcı Adı</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Tam Ad</TableHead>
                <TableHead className="text-center">Rol</TableHead>
                <TableHead className="text-center">Durum</TableHead>
                <TableHead>Oluşturulma</TableHead>
                <TableHead className="text-right">İşlemler</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-medium">{user.username}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>{user.full_name || '-'}</TableCell>
                  <TableCell className="text-center">
                    <div className="flex items-center justify-center gap-1">
                      {user.is_admin ? (
                        <>
                          <Shield className="h-4 w-4 text-purple-600" />
                          <span className="text-xs font-medium text-purple-600">Admin</span>
                        </>
                      ) : (
                        <>
                          <User className="h-4 w-4 text-gray-600" />
                          <span className="text-xs font-medium text-gray-600">Kullanıcı</span>
                        </>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-center">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      user.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {user.is_active ? 'Aktif' : 'Pasif'}
                    </span>
                  </TableCell>
                  <TableCell className="text-sm text-gray-600">
                    {new Date(user.created_at).toLocaleDateString('tr-TR')}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => handleEdit(user)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => handleDelete(user.id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <UserModal
        open={modalOpen}
        onOpenChange={handleModalClose}
        user={selectedUser}
        onSuccess={loadUsers}
      />
    </div>
  )
}
