/**
 * Google Analytics & User Behavior Tracking
 * Fiyatradari Web Analytics
 */

// Google Analytics Measurement ID
export const GA_MEASUREMENT_ID = process.env.NEXT_PUBLIC_GA_ID || '';

// Check if GA is enabled
export const isGAEnabled = (): boolean => {
  return !!GA_MEASUREMENT_ID && process.env.NODE_ENV === 'production';
};

// Initialize Google Analytics
export const initGA = (): void => {
  if (!isGAEnabled()) {
    console.log('Google Analytics disabled in development');
    return;
  }

  // Load gtag script
  const script = document.createElement('script');
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
  script.async = true;
  document.head.appendChild(script);

  // Initialize gtag
  window.dataLayer = window.dataLayer || [];
  function gtag(...args: any[]) {
    window.dataLayer.push(args);
  }
  gtag('js', new Date());
  gtag('config', GA_MEASUREMENT_ID, {
    page_path: window.location.pathname,
    send_page_view: false, // We'll handle this manually
  });
};

// Page view tracking
export const trackPageView = (url: string): void => {
  if (!isGAEnabled()) return;

  if (typeof window.gtag !== 'undefined') {
    window.gtag('config', GA_MEASUREMENT_ID, {
      page_path: url,
    });
  }
};

export interface GAEvent {
  action: string;
  category: string;
  label?: string;
  value?: number;
}

export const trackEvent = ({ action, category, label, value }: GAEvent): void => {
  if (!isGAEnabled()) {
    console.log('Event:', { action, category, label, value });
    return;
  }

  if (typeof window.gtag !== 'undefined') {
    window.gtag('event', action, {
      event_category: category,
      event_label: label,
      value: value,
    });
  }
};

// E-commerce tracking
export const trackProductView = (product: {
  id: string;
  name: string;
  category: string;
  price: number;
  brand?: string;
}): void => {
  trackEvent({
    action: 'view_item',
    category: 'Ecommerce',
    label: product.name,
    value: product.price,
  });

  if (typeof window.gtag !== 'undefined') {
    window.gtag('event', 'view_item', {
      currency: 'TRY',
      value: product.price,
      items: [
        {
          item_id: product.id,
          item_name: product.name,
          item_category: product.category,
          item_brand: product.brand,
          price: product.price,
        },
      ],
    });
  }
};

export const trackDealClick = (deal: {
  id: string;
  productName: string;
  discount: number;
  price: number;
}): void => {
  trackEvent({
    action: 'select_promotion',
    category: 'Deals',
    label: deal.productName,
    value: deal.discount,
  });
};

export const trackAmazonClick = (productId: string, productName: string): void => {
  trackEvent({
    action: 'click_to_amazon',
    category: 'Conversion',
    label: productName,
  });
};

// User behavior tracking
export const trackSearch = (searchTerm: string, resultsCount: number): void => {
  trackEvent({
    action: 'search',
    category: 'Engagement',
    label: searchTerm,
    value: resultsCount,
  });
};

export const trackCategoryView = (categoryName: string): void => {
  trackEvent({
    action: 'view_category',
    category: 'Navigation',
    label: categoryName,
  });
};

export const trackFilterChange = (filterType: string, filterValue: string): void => {
  trackEvent({
    action: 'apply_filter',
    category: 'Engagement',
    label: `${filterType}: ${filterValue}`,
  });
};

export const trackTimeOnPage = (pageName: string, seconds: number): void => {
  trackEvent({
    action: 'time_on_page',
    category: 'Engagement',
    label: pageName,
    value: seconds,
  });
};

// Error tracking
export const trackError = (errorMessage: string, errorLocation: string): void => {
  trackEvent({
    action: 'error',
    category: 'Error',
    label: `${errorLocation}: ${errorMessage}`,
  });
};

// Social sharing
export const trackShare = (platform: string, contentType: string): void => {
  trackEvent({
    action: 'share',
    category: 'Social',
    label: `${platform} - ${contentType}`,
  });
};

// Performance tracking
export const trackPerformance = (): void => {
  if (!isGAEnabled() || typeof window.performance === 'undefined') return;

  const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
  if (!navigation) return;

  const pageLoadTime = navigation.loadEventEnd - navigation.fetchStart;
  const dnsTime = navigation.domainLookupEnd - navigation.domainLookupStart;
  const tcpTime = navigation.connectEnd - navigation.connectStart;
  const ttfb = navigation.responseStart - navigation.requestStart;

  trackEvent({
    action: 'page_load_time',
    category: 'Performance',
    label: window.location.pathname,
    value: Math.round(pageLoadTime),
  });

  trackEvent({
    action: 'time_to_first_byte',
    category: 'Performance',
    label: window.location.pathname,
    value: Math.round(ttfb),
  });
};

// Declare gtag for TypeScript
declare global {
  interface Window {
    dataLayer: any[];
    gtag: (...args: any[]) => void;
  }
}
