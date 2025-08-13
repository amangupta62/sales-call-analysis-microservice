"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.sales_call import SalesCall, Transcript, CoachableMoment, ExecutiveSummary


class TestTranscriptionEndpoints:
    """Test transcription-related endpoints."""
    
    def test_upload_audio_success(self, client: TestClient, sample_audio_file: bytes):
        """Test successful audio upload."""
        response = client.post(
            "/api/v1/transcribe/upload",
            data={
                "call_id": "test_call_001",
                "agent_id": "agent_001",
                "customer_id": "customer_001"
            },
            files={"audio_file": ("test.wav", sample_audio_file, "audio/wav")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["call_id"] == "test_call_001"
        assert data["status"] == "uploaded"
        assert "message" in data
    
    def test_upload_audio_duplicate_call_id(self, client: TestClient, sample_audio_file: bytes, db_session: Session):
        """Test upload with duplicate call ID."""
        # Create existing call
        existing_call = SalesCall(
            call_id="test_call_001",
            agent_id="agent_001",
            customer_id="customer_001",
            audio_file_path="/test/path",
            status="completed"
        )
        db_session.add(existing_call)
        db_session.commit()
        
        response = client.post(
            "/api/v1/transcribe/upload",
            data={
                "call_id": "test_call_001",
                "agent_id": "agent_002",
                "customer_id": "customer_002"
            },
            files={"audio_file": ("test.wav", sample_audio_file, "audio/wav")}
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_get_transcription_status(self, client: TestClient, db_session: Session):
        """Test getting transcription status."""
        # Create test call
        call = SalesCall(
            call_id="test_call_001",
            agent_id="agent_001",
            customer_id="customer_001",
            audio_file_path="/test/path",
            status="processing"
        )
        db_session.add(call)
        db_session.commit()
        
        response = client.get("/api/v1/transcribe/test_call_001/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["call_id"] == "test_call_001"
        assert data["status"] == "processing"
    
    def test_get_transcription_status_not_found(self, client: TestClient):
        """Test getting status for non-existent call."""
        response = client.get("/api/v1/transcribe/nonexistent_call/status")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_list_sales_calls(self, client: TestClient, db_session: Session):
        """Test listing sales calls."""
        # Create test calls
        calls = [
            SalesCall(
                call_id=f"test_call_{i}",
                agent_id=f"agent_{i}",
                customer_id=f"customer_{i}",
                audio_file_path=f"/test/path_{i}",
                status="completed"
            )
            for i in range(3)
        ]
        
        for call in calls:
            db_session.add(call)
        db_session.commit()
        
        response = client.get("/api/v1/transcribe/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("call_id" in call for call in data)
    
    def test_list_sales_calls_with_filter(self, client: TestClient, db_session: Session):
        """Test listing sales calls with status filter."""
        # Create calls with different statuses
        calls = [
            SalesCall(
                call_id="completed_call",
                agent_id="agent_1",
                customer_id="customer_1",
                audio_file_path="/test/path",
                status="completed"
            ),
            SalesCall(
                call_id="processing_call",
                agent_id="agent_2",
                customer_id="customer_2",
                audio_file_path="/test/path",
                status="processing"
            )
        ]
        
        for call in calls:
            db_session.add(call)
        db_session.commit()
        
        response = client.get("/api/v1/transcribe/?status=completed")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "completed"


class TestTTSEndpoints:
    """Test text-to-speech endpoints."""
    
    def test_text_to_speech_success(self, client: TestClient, sample_tts_request: dict):
        """Test successful TTS conversion."""
        response = client.post("/api/v1/speak/", json=sample_tts_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "audio_file_path" in data
        assert "duration_seconds" in data
        assert "text_length" in data
    
    def test_text_to_speech_empty_text(self, client: TestClient):
        """Test TTS with empty text."""
        response = client.post("/api/v1/speak/", json={"text": "", "language": "en"})
        
        assert response.status_code == 400
        assert "cannot be empty" in response.json()["detail"]
    
    def test_get_supported_languages(self, client: TestClient):
        """Test getting supported languages."""
        response = client.get("/api/v1/speak/languages")
        
        assert response.status_code == 200
        data = response.json()
        assert "supported_languages" in data
        assert "default_language" in data
        assert "tts_engine" in data
    
    def test_get_tts_status(self, client: TestClient):
        """Test getting TTS service status."""
        response = client.get("/api/v1/speak/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "engine" in data


class TestReplayEndpoints:
    """Test replay functionality endpoints."""
    
    def test_get_coachable_moments_for_replay(self, client: TestClient, db_session: Session):
        """Test getting coachable moments for replay."""
        # Create test call with moments
        call = SalesCall(
            call_id="test_call_001",
            agent_id="agent_001",
            customer_id="customer_001",
            audio_file_path="/test/path",
            status="completed"
        )
        db_session.add(call)
        db_session.flush()
        
        moment = CoachableMoment(
            sales_call_id=call.id,
            moment_type="objection",
            confidence=0.85,
            start_time=2.0,
            end_time=3.0,
            description="Test objection",
            transcript_segment="This is expensive"
        )
        db_session.add(moment)
        db_session.commit()
        
        response = client.get("/api/v1/replay/test_call_001/moments")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["moment_type"] == "objection"
    
    def test_get_moment_types(self, client: TestClient, db_session: Session):
        """Test getting available moment types."""
        # Create test call with moments
        call = SalesCall(
            call_id="test_call_001",
            agent_id="agent_001",
            customer_id="customer_001",
            audio_file_path="/test/path",
            status="completed"
        )
        db_session.add(call)
        db_session.flush()
        
        moments = [
            CoachableMoment(
                sales_call_id=call.id,
                moment_type="objection",
                confidence=0.85,
                start_time=2.0,
                end_time=3.0,
                description="Test objection",
                transcript_segment="This is expensive"
            ),
            CoachableMoment(
                sales_call_id=call.id,
                moment_type="buying_signal",
                confidence=0.90,
                start_time=5.0,
                end_time=6.0,
                description="Test buying signal",
                transcript_segment="I'm interested"
            )
        ]
        
        for moment in moments:
            db_session.add(moment)
        db_session.commit()
        
        response = client.get("/api/v1/replay/test_call_001/moment-types")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_moments"] == 2
        assert len(data["moment_types"]) == 2


class TestHealthEndpoints:
    """Test health and configuration endpoints."""
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Sales Call Analysis Microservice"
        assert "endpoints" in data
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_config_endpoint(self, client: TestClient):
        """Test configuration endpoint."""
        response = client.get("/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "debug" in data
        assert "log_level" in data
        assert "audio_max_size_mb" in data
