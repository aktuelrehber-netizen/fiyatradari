'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function HealthPage() {
  const router = useRouter();
  
  useEffect(() => {
    router.replace('/dashboard/system');
  }, [router]);
  
  return null;
}
