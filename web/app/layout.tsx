import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Suspense } from "react";
import "./globals.css";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";
import { Analytics } from "@/components/Analytics";
import { OrganizationStructuredData, WebSiteStructuredData } from "@/components/StructuredData";
import { api } from "@/utils/api";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL('https://fiyatradari.com'),
  title: {
    default: "Fiyat Radarı - Amazon Fırsat ve İndirim Takibi",
    template: "%s | Fiyat Radarı"
  },
  description: "Amazon'dan tespit edilen en iyi fırsatları keşfedin. Günlük binlerce ürün taranır, büyük indirimler anında size bildirilir. Telegram kanalımıza katılın!",
  authors: [{ name: "Fiyat Radarı" }],
  creator: "Fiyat Radarı",
  publisher: "Fiyat Radarı",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: 'website',
    locale: 'tr_TR',
    url: 'https://fiyatradari.com',
    siteName: 'Fiyat Radarı',
    title: 'Fiyat Radarı - Amazon Fırsat ve İndirim Takibi',
    description: 'Amazon\'dan tespit edilen en iyi fırsatları keşfedin. Günlük binlerce ürün taranır!',
    images: [
      {
        url: '/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'Fiyat Radarı',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Fiyat Radarı - Amazon Fırsat Takibi',
    description: 'Amazon\'dan tespit edilen en iyi fırsatları keşfedin!',
    images: ['/og-image.jpg'],
  },
  alternates: {
    canonical: 'https://fiyatradari.com',
  },
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Fetch categories for header menu
  let categories = []
  
  try {
    categories = await api.getCategories()
  } catch (error) {
    // Silent fail - header will show without categories
    categories = []
  }

  return (
    <html lang="tr">
      <head>
        <OrganizationStructuredData />
        <WebSiteStructuredData />
      </head>
      <body className={inter.className}>
        <Suspense fallback={null}>
          <Analytics />
        </Suspense>
        <Header categories={categories} />
        {children}
        <Footer />
      </body>
    </html>
  );
}
