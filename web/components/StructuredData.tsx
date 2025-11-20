/**
 * Structured Data (JSON-LD) for SEO
 * Helps search engines understand the content
 */

interface OrganizationSchema {
  '@context': string;
  '@type': string;
  name: string;
  url: string;
  logo?: string;
  sameAs?: string[];
  contactPoint?: {
    '@type': string;
    email?: string;
    contactType: string;
  };
}

interface WebSiteSchema {
  '@context': string;
  '@type': string;
  name: string;
  url: string;
  description: string;
  potentialAction?: {
    '@type': string;
    target: string;
    'query-input': string;
  };
}

interface ProductSchema {
  '@context': string;
  '@type': string;
  name: string;
  description?: string;
  image?: string;
  offers: {
    '@type': string;
    price: number;
    priceCurrency: string;
    availability: string;
    url: string;
  };
  brand?: {
    '@type': string;
    name: string;
  };
}

export function OrganizationStructuredData() {
  const schema: OrganizationSchema = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'Fiyat Radarı',
    url: 'https://fiyatradari.com',
    logo: 'https://fiyatradari.com/logo.png',
    sameAs: [
      // Add your social media URLs here
      // 'https://twitter.com/fiyatradari',
      // 'https://www.facebook.com/fiyatradari',
      // 'https://www.instagram.com/fiyatradari',
    ],
    contactPoint: {
      '@type': 'ContactPoint',
      email: 'info@fiyatradari.com',
      contactType: 'Customer Service',
    },
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

export function WebSiteStructuredData() {
  const schema: WebSiteSchema = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'Fiyat Radarı',
    url: 'https://fiyatradari.com',
    description: 'Amazon\'dan tespit edilen en iyi fırsatları keşfedin. Günlük binlerce ürün taranır!',
    potentialAction: {
      '@type': 'SearchAction',
      target: 'https://fiyatradari.com/ara?q={search_term_string}',
      'query-input': 'required name=search_term_string',
    },
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

export function ProductStructuredData({ 
  product 
}: { 
  product: {
    title: string;
    description?: string;
    image_url?: string;
    current_price: number;
    brand?: string;
    asin: string;
  }
}) {
  const schema: ProductSchema = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: product.title,
    description: product.description,
    image: product.image_url,
    offers: {
      '@type': 'Offer',
      price: product.current_price,
      priceCurrency: 'TRY',
      availability: 'https://schema.org/InStock',
      url: `https://www.amazon.com.tr/dp/${product.asin}`,
    },
  };

  if (product.brand) {
    schema.brand = {
      '@type': 'Brand',
      name: product.brand,
    };
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

export function BreadcrumbStructuredData({ 
  items 
}: { 
  items: Array<{ name: string; url: string }> 
}) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url,
    })),
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}
