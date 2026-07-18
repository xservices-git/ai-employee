# Deployment

## Yêu cầu hệ thống

### Minimum (1 user, dev)
- CPU: 4 cores
- RAM: 16GB
- Disk: 50GB SSD
- GPU: optional (chạy CPU được, chậm hơn)
- OS: Linux, macOS, hoặc Windows + WSL2

### Recommended (5-10 users, prod)
- CPU: 8 cores
- RAM: 32GB
- Disk: 200GB SSD
- GPU: NVIDIA 8GB VRAM (cho 4B/8B model)
- OS: Ubuntu 22.04 LTS

### Scale (50+ users)
- CPU: 16 cores
- RAM: 64GB
- Disk: 500GB NVMe
- GPU: NVIDIA 24GB VRAM (cho 13B+ model)
- Multi-node với Docker Swarm

## Docker Compose (dev + small prod)

```yaml
# infra/docker-compose.yaml
version: '3.8'

services:
  api:
    build: ./docker/api
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=sqlite:///data/ai-employee.db
      - CHROMA_PATH=/data/chroma
      - OLLAMA_URL=http://ollama:11434
    volumes:
      - ./data:/data
    depends_on: [ollama]

  web:
    build: ./docker/web
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on: [api]

  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes:
      - ./data/ollama:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  chroma:
    image: chromadb/chroma:latest
    ports: ["8001:8000"]
    volumes:
      - ./data/chroma:/chroma/chroma

  mcp-data:
    build: ./docker/mcp-data
    environment:
      - DATABASE_URL=sqlite:///data/ai-employee.db
    volumes:
      - ./data:/data

  mcp-communication:
    build: ./docker/mcp-comm
    environment:
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASS=${SMTP_PASS}
    secrets: [smtp_pass]

  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports: ["3001:3000"]
    volumes:
      - grafana-data:/var/lib/grafana

volumes:
  grafana-data:
```

## Setup lần đầu

```bash
# 1. Clone
git clone https://github.com/xservices-git/ai-employee.git
cd ai-employee

# 2. Copy env
cp .env.example .env
# Edit .env, điền SMTP, secrets

# 3. Pull models
docker compose run --rm ollama ollama pull qwen2.5:4b
docker compose run --rm ollama ollama pull llama3.1:8b
docker compose run --rm ollama ollama pull nomic-embed-text:v1.5

# 4. Migrate DB
docker compose run --rm api alembic upgrade head

# 5. Start
docker compose up -d

# 6. Verify
curl http://localhost:8000/health
open http://localhost:3000
```

## Backup

### SQLite (mỗi 6h)
```bash
# infra/scripts/backup_db.sh
#!/bin/bash
BACKUP_DIR=/backups/ai-employee/$(date +%Y-%m-%d_%H-%M)
mkdir -p $BACKUP_DIR
sqlite3 /data/ai-employee.db ".backup '$BACKUP_DIR/db.sqlite'"
tar czf $BACKUP_DIR/chroma.tar.gz -C /data chroma
# Upload to S3
aws s3 cp $BACKUP_DIR s3://my-backups/ai-employee/$BACKUP_DIR --recursive
```

Cài đặt cron:
```bash
0 */6 * * * /opt/ai-employee/infra/scripts/backup_db.sh
```

### ChromaDB
- Snapshot thư mục khi không active (stop API briefly)
- Hoặc dùng `chroma` CLI export

### Models
- Ollama tự cache models trong `/root/.ollama`
- Backup thư mục này nếu muốn (nặng ~5-10GB)

## Restore

```bash
# Stop services
docker compose down

# Restore DB
cp /backups/ai-employee/2026-07-19_12-00/db.sqlite /data/ai-employee.db

# Restore vector store
rm -rf /data/chroma
tar xzf /backups/ai-employee/2026-07-19_12-00/chroma.tar.gz -C /data

# Start lại
docker compose up -d
```

## Update

```bash
# 1. Pull code mới
git pull origin master

# 2. Rebuild images
docker compose build

# 3. Migrate DB
docker compose run --rm api alembic upgrade head

# 4. Restart với zero downtime (Swarm mode)
docker service update --image ai-employee_api:latest ai-employee_api
```

## Monitoring

### Prometheus metrics
- Scrape từ `http://api:8000/metrics`
- Xem tại `http://localhost:9090`

### Grafana dashboards
- Task throughput
- Latency P50/P95/P99
- Error rate per tool
- Confidence distribution
- Approval queue size

### Alerting
Alert gửi qua Telegram/Slack khi:
- API down > 1 phút
- Error rate > 5%
- P95 latency > 10s
- Disk usage > 80%
- Backup fail

## Security checklist

- [ ] TLS cho mọi external endpoint
- [ ] Secret trong Docker secrets hoặc vault, không trong env
- [ ] Rate limiting enabled
- [ ] Firewall: chỉ mở 80/443 cho web, 22 cho admin
- [ ] SSH key-only, disable password
- [ ] Auto security update
- [ ] Audit log ship ra external storage
- [ ] Backup mã hóa (at-rest)
- [ ] Penetration test mỗi năm

## Disaster Recovery

- **RPO (Recovery Point Objective):** 6h (mất tối đa 6h data)
- **RTO (Recovery Time Objective):** 30 phút

Kịch bản:
- **DB corrupt:** restore từ backup gần nhất
- **Vector store corrupt:** restore từ backup hoặc rebuild từ source docs
- **Server chết:** deploy lại từ compose, restore backup
- **Mất models:** pull lại từ Ollama registry (~10-30 phút)
- **Mất toàn bộ data center:** backup offsite (S3), deploy ở region khác

## Single-node vs multi-node

### Single-node (khuyến nghị cho < 50 users)
- Docker Compose đơn giản
- 1 instance mọi service
- Dễ backup, dễ debug
- Phù hợp SME

### Multi-node (50+ users)
- Docker Swarm hoặc K3s
- Tách Ollama ra node riêng (GPU)
- Tách vector DB ra node riêng (RAM)
- API có thể scale horizontal
- Web có thể scale horizontal

## Migration sang K8s (sau M5)

Nếu cần scale lớn hơn, có Helm chart:
```bash
helm install ai-employee ./helm/
```

Nhưng default là Swarm/K3s cho đơn giản.
