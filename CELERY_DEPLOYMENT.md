# Celery Distributed Worker System - Deployment Guide

## 📋 Genel Bakış

Bu mimari, **1M+ ürün** için optimize edilmiş production-ready distributed task queue sistemidir.

### Celery Distributed Task Queue System

**Production-ready sistem özellikleri:**
- ✅ Distributed task queue (Redis)
- ✅ 10-100+ worker desteği
- ✅ 1M+ ürün kapasitesi
- ✅ Paralel işlem (80-400+ concurrent tasks)
- ✅ Priority-based scheduling
- ✅ Auto-retry mechanism
- ✅ Flower monitoring dashboard
- ✅ Horizontal scaling

## 🚀 Hızlı Başlangıç

### 1. Database Migration

Önce yeni alanları ekleyin:

```bash
# PostgreSQL'e bağlan
psql -U fiyatradari -d fiyatradari

# Migration'ı çalıştır
\i backend/migrations/add_celery_fields.sql
```

### 2. Dependencies Kurulumu

```bash
cd worker
pip install -r requirements.txt
```

### 3. Environment Variables

`.env` dosyanıza ekleyin:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### 4. Sistemi Başlatma

#### Option A: Docker Compose (Önerilen)

```bash
# Tüm servisleri başlat
docker-compose up -d

# Flower monitoring: http://localhost:5555
```

#### Option B: Manuel Başlatma

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery Worker Pool (3 worker, her biri 4 concurrent task)
cd worker
celery -A celery_app worker --loglevel=info --concurrency=4

# Terminal 3: Celery Beat (Scheduler)
cd worker
celery -A celery_app beat --loglevel=info

# Terminal 4: Flower (Monitoring) - Opsiyonel
cd worker
celery -A celery_app flower --port=5555

```

## 📊 Monitoring

### Flower Dashboard

Web arayüzü: http://localhost:5555

**Özellikler:**
- Active tasks görüntüleme
- Worker durumları
- Task başarı/hata oranları
- Task execution time grafikleri
- Real-time monitoring

### Celery CLI Commands

```bash
# Worker'ları görüntüle
celery -A celery_app inspect active

# Stats
celery -A celery_app inspect stats

# Registered tasks
celery -A celery_app inspect registered

# Queue'ları görüntüle
celery -A celery_app inspect active_queues

# Task'ı iptal et
celery -A celery_app control revoke <task_id>

# Worker'ı durdur
celery -A celery_app control shutdown
```

## 🎯 Task Çeşitleri ve Zamanlama

### Otomatik Zamanlanmış Task'lar (Celery Beat)

| Task | Sıklık | Açıklama |
|------|--------|----------|
| `schedule_high_priority_checks` | Her saat | Active deal'leri olan ürünler |
| `schedule_medium_priority_checks` | Her 6 saat | Orta öncelik ürünler |
| `schedule_low_priority_checks` | Günlük (03:00) | Düşük öncelik ürünler |
| `schedule_product_fetch` | Günlük (04:00) | Yeni ürün çekme |
| `schedule_notifications` | Her 30 dakika | Telegram bildirimleri |
| `update_product_priorities` | Her 4 saat | Priority score güncelleme |
| `cleanup_old_data` | Günlük (02:00) | Eski veri temizleme |

### Manuel Task Tetikleme

Python'dan:

```python
from celery_tasks import check_product_price, batch_price_check

# Single product
result = check_product_price.delay(product_id=123, priority=10)
print(result.id)  # Task ID

# Batch
result = batch_price_check.delay([1, 2, 3, 4, 5], priority=8)
```

Celery CLI'dan:

```bash
# Task tetikle
celery -A celery_app call celery_tasks.check_product_price --args='[123]' --kwargs='{"priority": 10}'
```

## 🔧 Konfigürasyon

### Worker Scaling

#### Docker Compose ile:

```yaml
# docker-compose.yml'de replicas değiştir
celery_worker:
  deploy:
    replicas: 10  # 10 worker instance
```

#### Manuel:

```bash
# Concurrency artır (her worker'da daha fazla task)
celery -A celery_app worker --concurrency=20

# Birden fazla worker başlat
celery -A celery_app worker -n worker1@%h --concurrency=4
celery -A celery_app worker -n worker2@%h --concurrency=4
celery -A celery_app worker -n worker3@%h --concurrency=4
```

### Queue Priorities

`celery_app.py`'de queue tanımları:

```python
task_queues=(
    Queue('price_check', ..., queue_arguments={'x-max-priority': 10}),
    Queue('product_fetch', ..., queue_arguments={'x-max-priority': 5}),
    Queue('notifications', ..., queue_arguments={'x-max-priority': 8}),
    Queue('batch_processing', ..., queue_arguments={'x-max-priority': 3}),
)
```

### Rate Limiting

Her task için rate limit:

```python
@app.task(rate_limit='100/m')  # 100 tasks per minute
def check_product_price(product_id):
    pass
```

## 📈 Priority System

### Priority Hesaplama

Product priority (0-100) şu faktörlere göre hesaplanır:

```python
Priority = (
    has_active_deal * 50 +      # Active deal varsa 50 puan
    volatility_score * 0.30 +   # Fiyat volatility %30
    popularity_score * 0.15 +   # Popülerlik %15
    recency_score * 0.05        # Son kontrol zamanı %5
)
```

### Check Intervals (Priority'ye göre)

- **Priority >= 80:** Her saat kontrol
- **Priority 60-79:** Her 3 saat
- **Priority 40-59:** Her 6 saat
- **Priority 20-39:** Her 12 saat
- **Priority < 20:** Günde 1

### Priority Güncelleme

Otomatik (her 4 saatte):
```python
# Celery Beat tarafından otomatik çalıştırılır
update_product_priorities()
```

Manuel:
```python
from services.priority_calculator import PriorityCalculator
calculator = PriorityCalculator()

with get_db() as db:
    product = db.query(Product).first()
    priority = calculator.calculate_priority(product, db)
    product.check_priority = priority
    db.commit()
```

## 🔍 Smart Batching

### Batch Processor Kullanımı

```python
from services.smart_batch_processor import SmartBatchProcessor

processor = SmartBatchProcessor(batch_size=1000)

# High priority batch'ler al
batches = processor.get_high_priority_batches(limit=10000)
for batch in batches:
    batch_price_check.delay(batch['product_ids'], priority=10)

# Statistics
stats = processor.get_statistics()
print(stats)
```

### Batch Stratejisi

1. **High Priority (her saat)**
   - Active deal'leri olan ürünler
   - Priority score >= 80
   - Son 1 saatte kontrol edilmemiş

2. **Medium Priority (her 6 saat)**
   - Priority score 40-79
   - Son 6 saatte kontrol edilmemiş

3. **Low Priority (günlük)**
   - Priority score < 40
   - Son 24 saatte kontrol edilmemiş

## 🐛 Debugging

### Task Sonuçlarını Görme

```python
from celery.result import AsyncResult

result = AsyncResult('task-id-here')
print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE
print(result.result)  # Task sonucu
print(result.traceback)  # Hata varsa traceback
```

### Logları İzleme

```bash
# Worker logs
docker-compose logs -f celery_worker

# Beat logs
docker-compose logs -f celery_beat

# Tüm Celery logları
docker-compose logs -f celery_worker celery_beat flower
```

### Common Issues

#### 1. "Connection refused" hatası
```bash
# Redis çalışıyor mu?
redis-cli ping  # PONG dönmeli

# Docker'da
docker-compose ps redis
```

#### 2. Task'lar çalışmıyor
```bash
# Worker'lar aktif mi?
celery -A celery_app inspect active_queues

# Beat çalışıyor mu?
docker-compose logs celery_beat | grep "Scheduler:"
```

#### 3. Yavaş performans
```bash
# Worker sayısını artır
docker-compose up -d --scale celery_worker=10

# Veya concurrency artır
celery -A celery_app worker --concurrency=20
```

## ✅ Deployment Checklist

- [ ] Database migration çalıştırıldı
- [ ] Redis yüklendi ve çalışıyor
- [ ] Dependencies kuruldu (`pip install -r requirements.txt`)
- [ ] Environment variables eklendi
- [ ] Celery worker başlatıldı ve çalışıyor
- [ ] Celery beat başlatıldı
- [ ] Flower monitoring erişilebilir
- [ ] İlk batch test edildi
- [ ] Priority'ler güncellendi
- [ ] 24 saat monitoring yapıldı

## 📊 Performance Metrics

### 1M Ürün için Beklenen Performans

| Metrik | Değer |
|--------|-------|
| **Worker sayısı** | 10-20 |
| **Concurrent tasks** | 80-400 |
| **Ürün/saat** | 150K-300K |
| **Full check süresi** | 3-7 saat |
| **Memory usage** | ~2-4 GB total |
| **Redis memory** | ~500 MB |

### Monitoring Metrikleri

Flower'da takip edilmesi gerekenler:
- Task success rate (>95% olmalı)
- Average task duration (<30 saniye olmalı)
- Worker utilization (70-90% ideal)
- Queue length (sürekli artmamalı)

## 🚨 Production Deployment

### Kubernetes (Opsiyonel)

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
spec:
  replicas: 20  # 20 worker pod
  template:
    spec:
      containers:
      - name: worker
        image: fiyatradari-worker:latest
        command: ["celery", "-A", "celery_app", "worker"]
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Auto-scaling Setup

```python
# autoscaler.py
from celery.app.control import Control

def scale_workers(queue_length):
    """Auto-scale based on queue length"""
    if queue_length > 10000:
        # Scale up
        os.system("docker-compose up -d --scale celery_worker=20")
    elif queue_length < 1000:
        # Scale down
        os.system("docker-compose up -d --scale celery_worker=5")
```

## 📚 Ek Kaynaklar

- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Best Practices](https://redis.io/topics/optimization)
- [Flower Monitoring](https://flower.readthedocs.io/)

## 🤝 Destek

Sorun yaşarsanız:
1. Flower dashboard'u kontrol edin: http://localhost:5555
2. Worker loglarını inceleyin: `docker-compose logs celery_worker`
3. Redis bağlantısını test edin: `redis-cli ping`
4. Statistics'leri kontrol edin:
   ```python
   from services.smart_batch_processor import SmartBatchProcessor
   print(SmartBatchProcessor().get_statistics())
   ```
