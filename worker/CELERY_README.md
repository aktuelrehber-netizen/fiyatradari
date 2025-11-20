# Celery Distributed Worker System

## 🎯 Hızlı Başlangıç

### 1. Kurulum
```bash
# Dependencies
pip install -r requirements.txt

# Database migration
psql -U fiyatradari -d fiyatradari -f ../backend/migrations/add_celery_fields.sql
```

### 2. Başlatma

#### Docker ile (Önerilen)
```bash
cd ..
docker-compose up -d
```

#### Manuel
```bash
# Start
chmod +x start_celery.sh
./start_celery.sh 5  # 5 worker

# Stop
chmod +x stop_celery.sh
./stop_celery.sh
```

### 3. Monitoring
- Flower Dashboard: http://localhost:5555
- Loglar: `tail -f logs/*.log`

## 📊 Sistem Durumu

```bash
# Active tasks
celery -A celery_app inspect active

# Statistics
python3 -c "
from services.smart_batch_processor import SmartBatchProcessor
print(SmartBatchProcessor().get_statistics())
"
```

## 🔧 Konfigürasyon

### Worker Scaling

```bash
# 10 worker başlat
./start_celery.sh 10

# Docker ile
docker-compose up -d --scale celery_worker=10
```

### Environment Variables

`.env` dosyasında:
```bash
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
DEAL_THRESHOLD_PERCENTAGE=15
```

## 📋 Task Listesi

| Task | Zamanlama | Açıklama |
|------|-----------|----------|
| High Priority Check | Her saat | Active deals |
| Medium Priority Check | 6 saat | Popüler ürünler |
| Low Priority Check | 24 saat | Stabil ürünler |
| Product Fetch | Günlük 04:00 | Yeni ürünler |
| Notifications | 30 dakika | Telegram |
| Priority Update | 4 saat | Priority recalc |
| Cleanup | Günlük 02:00 | Old data |

## 🐛 Troubleshooting

### Redis bağlantı hatası
```bash
redis-cli ping  # PONG dönmeli
redis-server  # Çalışmıyorsa başlat
```

### Task çalışmıyor
```bash
# Worker'ları kontrol et
celery -A celery_app inspect active_queues

# Logları kontrol et
tail -f logs/celery_worker_*.log
```

### Yavaş performans
```bash
# Worker sayısını artır
./start_celery.sh 20

# Concurrency artır (her worker'da)
celery -A celery_app worker --concurrency=10
```

## 📚 Detaylı Dokümantasyon

Tüm detaylar için: [CELERY_DEPLOYMENT.md](../CELERY_DEPLOYMENT.md)


## 📈 Performance

1M ürün için beklenen:
- Worker: 10-20
- Concurrent tasks: 80-400
- Full check: 3-7 saat
- Throughput: 150K-300K ürün/saat
