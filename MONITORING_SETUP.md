# 📊 Monitoring & Analytics Setup Guide

Complete guide for Fiyatradari monitoring, error tracking, and analytics.

---

## 🎯 Overview

### Monitoring Stack
- **Sentry**: Error tracking and performance monitoring
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization dashboards
- **Google Analytics**: User behavior and conversion tracking

### Key Features
✅ Real-time error tracking
✅ Performance monitoring
✅ System metrics (CPU, Memory, Disk)
✅ API metrics (requests, latency, errors)
✅ Worker task monitoring
✅ User behavior analytics
✅ Custom alerts and notifications

---

## 1️⃣ SENTRY SETUP

### Step 1: Create Sentry Project
1. Go to [sentry.io](https://sentry.io)
2. Create account / Login
3. Create new project → Select **FastAPI**
4. Copy your DSN

### Step 2: Configure Sentry
```bash
# In .env or .env.production
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
```

### Step 3: Verify Installation
```bash
# Restart backend
docker-compose restart backend

# Check logs
docker-compose logs backend | grep Sentry
# Should see: ✅ Sentry initialized successfully
```

### Features Enabled
- ✅ Automatic error capturing
- ✅ Performance transaction tracking (10% sample rate)
- ✅ FastAPI integration
- ✅ SQLAlchemy query tracking
- ✅ Redis operation tracking
- ✅ Release tracking
- ✅ Custom event filtering

### Testing Sentry
```bash
# Trigger test error
curl http://localhost:8000/api/v1/test-error

# Check Sentry dashboard for the error
```

---

## 2️⃣ PROMETHEUS SETUP

### What's Configured
- **Backend API metrics** (port 8000/metrics)
- **Node Exporter** (system metrics)
- **30-day retention**
- **15s scrape interval**

### Start Prometheus
```bash
docker-compose up -d prometheus
```

### Access Prometheus
- URL: http://localhost:9090
- Targets: http://localhost:9090/targets
- Alerts: http://localhost:9090/alerts

### Available Metrics
```promql
# Request rate
rate(fiyatradari_requests_total[5m])

# Response time (P95)
histogram_quantile(0.95, rate(fiyatradari_request_duration_seconds_bucket[5m]))

# Error rate
rate(fiyatradari_requests_total{status=~"5.."}[5m])

# Products count
fiyatradari_products_total

# Deals count
fiyatradari_deals_total

# Cache hit rate
rate(fiyatradari_cache_hits_total[5m]) / 
  (rate(fiyatradari_cache_hits_total[5m]) + rate(fiyatradari_cache_misses_total[5m]))

# Worker task rate
rate(fiyatradari_worker_tasks_total[5m])
```

### Custom Metrics in Code
```python
from app.core.monitoring import request_counter, products_total

# Increment counter
request_counter.labels(method="GET", endpoint="/products", status=200).inc()

# Set gauge
products_total.set(1000000)
```

---

## 3️⃣ GRAFANA SETUP

### Step 1: Start Grafana
```bash
docker-compose up -d grafana
```

### Step 2: Access Grafana
- URL: http://localhost:3002
- Username: `admin`
- Password: `admin123` (or from GRAFANA_PASSWORD env)

### Step 3: Verify Datasource
1. Go to Configuration → Data Sources
2. Prometheus should be auto-configured
3. Click "Test" → Should see "Data source is working"

### Step 4: Import Dashboard
1. Go to Dashboards → Import
2. Dashboard is auto-provisioned: "Fiyatradari - System Overview"
3. Or manually import: `grafana/dashboards/fiyatradari-overview.json`

### Available Dashboards

#### Fiyatradari System Overview
- Request Rate graph
- Response Time (P95) graph
- Error Rate graph
- Active Products counter
- Active Deals counter
- CPU Usage graph
- Memory Usage graph
- Cache Hit Rate graph
- Worker Task Rate graph

### Creating Custom Dashboards
1. Click "+" → New Dashboard
2. Add Panel
3. Select Prometheus datasource
4. Enter PromQL query
5. Configure visualization
6. Save

---

## 4️⃣ GOOGLE ANALYTICS SETUP

### Step 1: Create GA4 Property
1. Go to [analytics.google.com](https://analytics.google.com)
2. Create Account / Property
3. Select "Web" platform
4. Copy Measurement ID (format: G-XXXXXXXXXX)

### Step 2: Configure Environment
```bash
# In web/.env.local
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX

# Optional: Google Tag Manager
NEXT_PUBLIC_GTM_ID=GTM-XXXXXXX
```

### Step 3: Add Analytics Component
The Analytics component is already created at `web/components/Analytics.tsx`.

Add it to your root layout:
```tsx
// web/app/layout.tsx
import { Analytics } from '@/components/Analytics';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <Analytics />
        {children}
      </body>
    </html>
  );
}
```

### Tracked Events

#### Automatic Tracking
- ✅ Page views
- ✅ Time on page
- ✅ Performance metrics (page load, TTFB)

#### Product Events
```typescript
import { trackProductView, trackDealClick, trackAmazonClick } from '@/lib/analytics';

// Product view
trackProductView({
  id: product.asin,
  name: product.title,
  category: product.category.name,
  price: product.current_price,
  brand: product.brand
});

// Deal click
trackDealClick({
  id: deal.id,
  productName: deal.product.title,
  discount: deal.discount_percentage,
  price: deal.price_after_discount
});

// Amazon link click (conversion)
trackAmazonClick(product.asin, product.title);
```

#### User Behavior
```typescript
import { trackSearch, trackCategoryView, trackFilterChange } from '@/lib/analytics';

// Search
trackSearch(searchQuery, resultsCount);

// Category view
trackCategoryView(category.name);

// Filter application
trackFilterChange('price_range', '0-100');
```

#### Social Sharing
```typescript
import { trackShare } from '@/lib/analytics';

trackShare('twitter', 'deal');
trackShare('whatsapp', 'product');
```

---

## 5️⃣ ADMIN PANEL MONITORING

### Access Monitoring Dashboard
- URL: http://localhost:3001/dashboard/monitoring
- Features:
  - Real-time API metrics
  - System resource usage
  - Worker performance
  - Links to Grafana and Prometheus
  - Active alerts display

### Integration
The monitoring page automatically fetches from:
- Backend `/metrics` endpoint
- Prometheus HTTP API
- Updates every 10 seconds

---

## 6️⃣ ALERTS CONFIGURATION

### Prometheus Alert Rules
Located in `prometheus/alerts.yml`:

#### Critical Alerts
- **APIDown**: Backend API is down for > 1 minute
- **RedisDown**: Redis is down for > 1 minute
- **HighMemoryUsage**: Memory > 90% for 5 minutes
- **DiskSpaceLow**: Disk < 10% free

#### Warning Alerts
- **HighErrorRate**: API errors > 5% for 5 minutes
- **SlowResponseTime**: P95 latency > 1s for 10 minutes
- **HighTaskFailureRate**: Worker failures > 10%
- **HighCPUUsage**: CPU > 80% for 10 minutes

### Alert Notification Setup

#### Slack Integration
```yaml
# Add to prometheus/alertmanager.yml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts'
        title: 'Fiyatradari Alert'
```

#### Email Notifications
```yaml
receivers:
  - name: 'email'
    email_configs:
      - to: 'alerts@fiyatradari.com'
        from: 'monitoring@fiyatradari.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
```

---

## 7️⃣ MONITORING URLS

### Development
- **Backend API**: http://localhost:8000
- **API Metrics**: http://localhost:8000/metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3002
- **Admin Monitoring**: http://localhost:3001/dashboard/monitoring
- **Flower (Celery)**: http://localhost:5555

### Production
- **API**: https://api.fiyatradari.com
- **Metrics**: https://api.fiyatradari.com/metrics (protect with auth!)
- **Grafana**: https://grafana.fiyatradari.com
- **Prometheus**: Internal only (not exposed)

---

## 8️⃣ BEST PRACTICES

### Security
- ✅ Protect `/metrics` endpoint in production with HTTP auth
- ✅ Use strong Grafana password
- ✅ Don't expose Prometheus publicly
- ✅ Firewall monitoring services
- ✅ Enable HTTPS for all monitoring tools

### Performance
- ✅ Sample Sentry transactions (10% default)
- ✅ Set appropriate metric retention (30 days)
- ✅ Use Prometheus recording rules for complex queries
- ✅ Implement metric cardinality limits

### Maintenance
- ✅ Regularly review and update alert thresholds
- ✅ Archive old Grafana dashboards
- ✅ Clean up unused Sentry issues
- ✅ Monitor monitoring tool resource usage

---

## 9️⃣ TROUBLESHOOTING

### Sentry not receiving errors
```bash
# Check initialization
docker-compose logs backend | grep Sentry

# Verify DSN is set
docker-compose exec backend printenv | grep SENTRY_DSN

# Test error
curl http://localhost:8000/api/v1/non-existent-endpoint
```

### Prometheus not scraping
```bash
# Check targets
curl http://localhost:9090/api/v1/targets | jq

# Verify metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus logs
docker-compose logs prometheus
```

### Grafana dashboard empty
```bash
# Verify datasource connection
curl http://localhost:3002/api/datasources

# Check Prometheus is reachable from Grafana
docker-compose exec grafana wget -O- http://prometheus:9090/api/v1/query?query=up
```

### Analytics not tracking
```bash
# Check browser console for errors
# Verify GA_ID is set
echo $NEXT_PUBLIC_GA_ID

# Check gtag is loaded
# In browser console: typeof window.gtag
```

---

## 🎯 METRICS TO MONITOR

### Application Health
- ✅ Request rate (target: stable)
- ✅ Error rate (target: < 1%)
- ✅ Response time P95 (target: < 500ms)
- ✅ Uptime (target: 99.9%)

### Business Metrics
- ✅ Total products
- ✅ Active deals
- ✅ Conversion rate (Amazon clicks)
- ✅ User engagement (time on site, pages per session)

### Infrastructure
- ✅ CPU usage (target: < 70%)
- ✅ Memory usage (target: < 80%)
- ✅ Disk usage (target: < 75%)
- ✅ Database connections

### Workers
- ✅ Task success rate (target: > 95%)
- ✅ Queue length (target: < 100)
- ✅ Task execution time
- ✅ Worker health

---

## ✅ POST-DEPLOYMENT CHECKLIST

- [ ] Sentry DSN configured and tested
- [ ] Google Analytics ID set and verified
- [ ] Grafana password changed from default
- [ ] Prometheus retention configured
- [ ] Alert rules tested
- [ ] Notification channels configured (Slack/Email)
- [ ] Monitoring dashboards reviewed
- [ ] Performance baselines established
- [ ] On-call rotation defined
- [ ] Runbooks created for common issues

---

**Congratulations! Your monitoring stack is complete** 🎉
