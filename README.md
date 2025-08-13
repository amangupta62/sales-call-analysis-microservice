# Sales Call Analysis Microservice

A comprehensive, scalable microservice for processing sales call audio recordings, identifying coachable moments, providing structured transcripts, and generating executive summaries using AI-powered analysis.

## 🚀 Features

- **Audio Transcription**: Convert audio to text using OpenAI Whisper with speaker diarization
- **Sentiment Analysis**: Analyze emotional tone and sentiment using HuggingFace transformers
- **Coachable Moment Detection**: Automatically identify key learning opportunities (objections, buying signals, etc.)
- **Executive Summaries**: Generate comprehensive call summaries with action items
- **Text-to-Speech**: Convert text back to audio for replay functionality
- **Background Processing**: Async processing using Celery and Redis
- **RESTful API**: FastAPI-based API with automatic documentation
- **Scalable Architecture**: Microservice design with clear separation of concerns

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   Celery Worker │    │   PostgreSQL    │
│   (Port 8000)   │◄──►│   (Background)  │◄──►│   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Audio Files  │    │     Redis       │    │   TTS Output    │
│   (Uploads)    │    │   (Message Q)   │    │   (Generated)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Task Queue**: Celery + Redis
- **AI/ML**: OpenAI Whisper, HuggingFace Transformers
- **TTS**: gTTS, pyttsx3
- **Audio Processing**: librosa, pydub
- **Containerization**: Docker, Docker Compose
- **Testing**: pytest, coverage
- **CI/CD**: GitHub Actions

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+
- FFmpeg (for audio processing)

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sales-call-analysis
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Celery Monitor: http://localhost:5555

### Option 2: Local Development

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up database and Redis**
   ```bash
   # Start PostgreSQL and Redis (using Docker or local installation)
   docker run -d --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15
   docker run -d --name redis -p 6379:6379 redis:7
   ```

3. **Set environment variables**
   ```bash
   export DATABASE_URL="postgresql://postgres:password@localhost:5432/sales_calls_db"
   export REDIS_URL="redis://localhost:6379/0"
   export CELERY_BROKER_URL="redis://localhost:6379/0"
   export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
   ```

4. **Initialize database**
   ```bash
   python -c "from models.database import create_tables; create_tables()"
   ```

5. **Start Celery worker**
   ```bash
   celery -A workers.celery_app worker --loglevel=info
   ```

6. **Start the application**
   ```bash
   python main.py
   ```

## 📚 API Endpoints

### Transcription Endpoints

- `POST /api/v1/transcribe/upload` - Upload audio file for analysis
- `GET /api/v1/transcribe/{call_id}/status` - Get transcription status
- `GET /api/v1/transcribe/{call_id}/transcript` - Get transcript
- `GET /api/v1/transcribe/{call_id}/coachable-moments` - Get coachable moments
- `GET /api/v1/transcribe/{call_id}/executive-summary` - Get executive summary
- `GET /api/v1/transcribe/{call_id}/analysis` - Get complete analysis

### Text-to-Speech Endpoints

- `POST /api/v1/speak/` - Convert text to speech
- `GET /api/v1/speak/audio/{filename}` - Download generated audio
- `POST /api/v1/speak/batch` - Batch TTS conversion
- `GET /api/v1/speak/languages` - Get supported languages

### Replay Endpoints

- `GET /api/v1/replay/{call_id}/moments` - Get moments for replay
- `POST /api/v1/replay/{call_id}/moment/{moment_id}/replay` - Replay moment
- `POST /api/v1/replay/{call_id}/moment/{moment_id}/replay-with-recommendations` - Replay with coaching

## 🔧 Configuration

Key configuration options in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sales_calls_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Audio Processing
AUDIO_MAX_SIZE_MB=50
SUPPORTED_AUDIO_FORMATS=wav,mp3,m4a

# AI Models
WHISPER_MODEL=base
SENTIMENT_MODEL=cardiffnlp/twitter-roberta-base-sentiment-latest

# TTS
TTS_ENGINE=gtts
TTS_LANGUAGE=en

# Coachable Moments
COACHABLE_MOMENT_THRESHOLD=0.7
```

## 📖 Usage Examples

### 1. Upload and Analyze Audio

```bash
curl -X POST "http://localhost:8000/api/v1/transcribe/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "call_id=call_001" \
  -F "agent_id=agent_001" \
  -F "customer_id=customer_001" \
  -F "audio_file=@sample_call.wav"
```

### 2. Check Processing Status

```bash
curl -X GET "http://localhost:8000/api/v1/transcribe/call_001/status"
```

### 3. Get Complete Analysis

```bash
curl -X GET "http://localhost:8000/api/v1/transcribe/call_001/analysis"
```

### 4. Convert Text to Speech

```bash
curl -X POST "http://localhost:8000/api/v1/speak/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test message", "language": "en"}'
```

### 5. Replay Coachable Moment

```bash
curl -X POST "http://localhost:8000/api/v1/replay/call_001/moment/1/replay" \
  -H "accept: application/json"
```

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html
```

## 🐳 Docker Commands

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Access container shell
docker-compose exec app bash
```

## 📊 Monitoring

- **Health Check**: `GET /health`
- **Configuration**: `GET /config`
- **Celery Monitor**: http://localhost:5555 (Flower)
- **API Documentation**: http://localhost:8000/docs

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running and accessible
   - Check DATABASE_URL in .env file

2. **Redis Connection Error**
   - Ensure Redis is running and accessible
   - Check REDIS_URL in .env file

3. **Audio Processing Errors**
   - Ensure FFmpeg is installed
   - Check audio file format and size

4. **Model Loading Issues**
   - Ensure sufficient disk space for AI models
   - Check internet connection for model downloads

### Logs

```bash
# View application logs
docker-compose logs -f app

# View worker logs
docker-compose logs -f celery_worker

# View database logs
docker-compose logs -f postgres
```

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**: Use proper secrets management
2. **Database**: Use managed PostgreSQL service
3. **Redis**: Use managed Redis service
4. **Storage**: Use cloud storage for audio files
5. **Monitoring**: Implement proper logging and monitoring
6. **Scaling**: Use Kubernetes or similar for horizontal scaling

### Kubernetes Deployment

```yaml
# Example deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sales-call-analysis
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sales-call-analysis
  template:
    metadata:
      labels:
        app: sales-call-analysis
    spec:
      containers:
      - name: app
        image: your-registry/sales-call-analysis:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

## 🙏 Acknowledgments

- OpenAI for Whisper speech recognition
- HuggingFace for transformer models
- FastAPI for the web framework
- Celery for background task processing
- PostgreSQL and Redis communities

---

**Built with ❤️ for better sales coaching and analysis**
