'use client';

import { useEffect } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { initGA, trackPageView, trackPerformance } from '@/lib/analytics';

/**
 * Analytics Component
 * Automatically tracks page views and performance
 */
export function Analytics() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Initialize GA on mount
  useEffect(() => {
    initGA();
  }, []);

  // Track page views on route change
  useEffect(() => {
    if (pathname) {
      const url = pathname + (searchParams?.toString() ? `?${searchParams.toString()}` : '');
      trackPageView(url);
      
      // Track performance metrics
      setTimeout(() => {
        trackPerformance();
      }, 1000);
    }
  }, [pathname, searchParams]);

  // Track time on page
  useEffect(() => {
    const startTime = Date.now();

    return () => {
      const timeOnPage = Math.round((Date.now() - startTime) / 1000);
      if (timeOnPage > 5) { // Only track if spent more than 5 seconds
        const { trackTimeOnPage } = require('@/lib/analytics');
        trackTimeOnPage(pathname || 'unknown', timeOnPage);
      }
    };
  }, [pathname]);

  return null; // This component doesn't render anything
}

/**
 * Google Tag Manager Script (Alternative to GA)
 */
export function GTMScript({ gtmId }: { gtmId: string }) {
  if (!gtmId || process.env.NODE_ENV !== 'production') {
    return null;
  }

  return (
    <>
      <script
        dangerouslySetInnerHTML={{
          __html: `
            (function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
            new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
            j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
            'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
            })(window,document,'script','dataLayer','${gtmId}');
          `,
        }}
      />
      <noscript>
        <iframe
          src={`https://www.googletagmanager.com/ns.html?id=${gtmId}`}
          height="0"
          width="0"
          style={{ display: 'none', visibility: 'hidden' }}
        />
      </noscript>
    </>
  );
}
