"""Pytest configuration and fixtures for testing."""

import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from main import app
from models.database import Base, get_db
from config.settings import settings


# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with test database."""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_audio_file():
    """Sample audio file content for testing."""
    # This would be a small test audio file in practice
    return b"fake_audio_content"


@pytest.fixture
def sample_sales_call_data():
    """Sample sales call data for testing."""
    return {
        "call_id": "test_call_001",
        "agent_id": "agent_001",
        "customer_id": "customer_001"
    }


@pytest.fixture
def sample_transcript_data():
    """Sample transcript data for testing."""
    return {
        "full_transcript": "Hello, this is a test call. How can I help you today?",
        "segments": [
            {
                "speaker_id": "speaker_1",
                "text": "Hello, this is a test call. How can I help you today?",
                "start_time": 0.0,
                "end_time": 3.5,
                "confidence": 0.95,
                "sentiment_score": 0.2,
                "sentiment_label": "positive"
            }
        ],
        "sentiment_scores": {
            "positive": 1,
            "negative": 0,
            "neutral": 0,
            "average_score": 0.2,
            "overall_label": "positive"
        },
        "duration": 3.5
    }


@pytest.fixture
def sample_coachable_moment_data():
    """Sample coachable moment data for testing."""
    return {
        "moment_type": "objection",
        "confidence": 0.85,
        "start_time": 2.0,
        "end_time": 3.0,
        "description": "Customer objection detected: expensive",
        "transcript_segment": "This seems expensive",
        "recommendations": [
            "Acknowledge the customer's concern",
            "Provide value proposition"
        ]
    }


@pytest.fixture
def sample_tts_request():
    """Sample TTS request data for testing."""
    return {
        "text": "This is a test text for TTS conversion",
        "language": "en",
        "speed": 1.0
    }
