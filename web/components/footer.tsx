import Link from 'next/link'
import { Send, Heart } from 'lucide-react'
import { Logo } from './logo'

export function Footer() {
  return (
    <footer className="bg-[#242F3E] text-gray-300">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div>
            <div className="mb-4">
              <Logo textColor="text-white" />
            </div>
            <p className="text-sm text-gray-400">
              Amazon'dan en iyi fırsatları keşfedin. Anlık bildirimler ile tasarruf edin.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="font-semibold text-white mb-4">Hızlı Linkler</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/" className="hover:text-[#FF9900] transition-colors">
                  Ana Sayfa
                </Link>
              </li>
              <li>
                <Link href="/kategoriler" className="hover:text-[#FF9900] transition-colors">
                  Tüm Kategoriler
                </Link>
              </li>
              <li>
                <Link href="/hakkimizda" className="hover:text-[#FF9900] transition-colors">
                  Hakkımızda
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="font-semibold text-white mb-4">Yasal</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/gizlilik" className="hover:text-[#FF9900] transition-colors">
                  Gizlilik Politikası
                </Link>
              </li>
              <li>
                <Link href="/kullanim-kosullari" className="hover:text-[#FF9900] transition-colors">
                  Kullanım Koşulları
                </Link>
              </li>
              <li>
                <Link href="/cerez-politikasi" className="hover:text-[#FF9900] transition-colors">
                  Çerez Politikası
                </Link>
              </li>
            </ul>
          </div>

          {/* Social */}
          <div>
            <h3 className="font-semibold text-white mb-4">Bizi Takip Edin</h3>
            <div className="space-y-3">
              <Link
                href="https://t.me/firsatradaricom"
                target="_blank"
                className="flex items-center gap-2 text-sm hover:text-[#FF9900] transition-colors"
              >
                <Send className="h-4 w-4" />
                Telegram Kanalı
              </Link>
              <p className="text-sm text-gray-400 mt-4">
                Anlık fırsatları kaçırma! Telegram'dan takip et.
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-gray-700 mt-8 pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-gray-400">
          <p>
            © {new Date().getFullYear()} Fiyat Radarı. Tüm hakları saklıdır.
          </p>
          <p className="flex items-center gap-1">
            Made with <Heart className="h-4 w-4 text-red-500 fill-red-500" /> in Turkey
          </p>
        </div>

        {/* Disclaimer */}
        <div className="mt-6 text-xs text-gray-500 text-center">
          <p>
            Bu site Amazon Associates Programı'nın bir parçasıdır. Amazon logosu ve markası Amazon.com, Inc. veya iştiraklerin ünvanıdır.
          </p>
        </div>
      </div>
    </footer>
  )
}
