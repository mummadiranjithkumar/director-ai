# Director AI Video App - Deployment Guide

## Architecture Overview

Director is a scalable FastAPI backend for AI video generation with:
- **FastAPI**: REST API endpoints
- **Redis**: Job queue and storage
- **Celery**: Background task processing
- **Replicate**: Image and video generation
- **Local Face Swap**: OpenCV-based face swapping

## System Requirements

### Dependencies
- Python 3.8+
- Redis server
- Replicate API token

### Environment Variables
```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://localhost:6379/0

# Replicate API
REPLICATE_API_TOKEN=your_replicate_token_here

# Test Mode (optional)
TEST_MODE=false
```

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Redis Setup
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server

# macOS
brew install redis

# Windows
# Download and install Redis from https://redis.io/download
```

### 3. Start Redis Server
```bash
redis-server --daemonize yes --port 6379
```

## Running the Application

### 1. Start Celery Worker
```bash
# Terminal 1 - Worker
celery -A worker worker --loglevel=info --concurrency=3
```

### 2. Start FastAPI Server
```bash
# Terminal 2 - API Server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Scaling Configuration

### Worker Concurrency
```python
# In worker.py - Adjust based on your server resources
celery_app.conf.worker_concurrency = 3  # Number of parallel jobs
```

### Queue Limits
```python
# In queue_service.py - Add rate limiting
MAX_QUEUE_SIZE = 100
MAX_JOBS_PER_USER = 2
```

## API Endpoints

### POST /generate
Generates video with optional face swap.

**Request:**
```json
{
  "prompt": "cinematic scene description",
  "face_image": "file (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "uuid-string",
  "status": "pending",
  "message": "Job added to queue"
}
```

### GET /status/{job_id}
Check job processing status.

**Response:**
```json
{
  "success": true,
  "job_id": "uuid-string",
  "status": "pending|processing|completed|failed",
  "video_url": "https://domain.com/videos/output.mp4",
  "error": null,
  "created_at": "2024-04-13T15:30:00Z",
  "updated_at": "2024-04-13T15:35:00Z"
}
```

### GET /health
System health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-04-13T15:30:00Z",
  "queue_size": 5
}
```

## Processing Pipeline

### Job Workflow
1. **Job Creation**: API receives request → saves face image → creates job → adds to Redis queue
2. **Image Generation**: Worker picks up job → generates image using Flux Schnell
3. **Face Swap**: Worker applies local OpenCV face swap if face image provided
4. **Video Generation**: Worker creates video using Animate Diff
5. **Job Completion**: Worker updates job status with video URL

### Cost Optimization
- **Image Generation**: 4 steps (low cost)
- **Video Generation**: 12 frames (reasonable quality)
- **Retry Logic**: Single retry on failures

## Monitoring

### Logs
```bash
# Worker logs
celery -A worker worker --loglevel=info

# API logs
uvicorn main:app --log-level info
```

### Health Checks
```bash
# Check Redis
redis-cli ping

# Check workers
celery -A worker inspect active

# Check API
curl http://localhost:8000/health
```

## Production Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["celery", "-A", "worker", "worker", "--loglevel=info", "--concurrency=3"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
      - REPLICATE_API_TOKEN=${REPLICATE_API_TOKEN}
  
  worker:
    build: .
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
      - REPLICATE_API_TOKEN=${REPLICATE_API_TOKEN}
    command: ["celery", "-A", "worker", "worker", "--loglevel=info", "--concurrency=3"]
```

## Troubleshooting

### Common Issues
1. **Redis Connection**: Check Redis server is running
2. **Worker Not Processing**: Check Celery worker logs
3. **API Timeouts**: Increase timeout values
4. **Replicate Failures**: Check API token and model availability

### Performance Tuning
- **Worker Concurrency**: Start with 3, increase based on CPU cores
- **Queue Size**: Monitor with `/health` endpoint
- **Memory Usage**: Monitor Redis memory consumption

## Security Notes

- **API Rate Limiting**: Implement per-user job limits
- **File Cleanup**: Schedule periodic cleanup of temp files
- **Token Security**: Use environment variables, never hardcode tokens
