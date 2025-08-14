#!/usr/bin/env python3
"""
Example script demonstrating how to use the Sales Call Analysis Microservice API.
This script shows the complete workflow from uploading audio to getting analysis results.
"""

import requests
import json
import time
import os
from typing import Dict, Any

class SalesCallAnalysisClient:
    """Client for interacting with the Sales Call Analysis Microservice."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "SalesCallAnalysis-Client/1.0"
        })
    
    def upload_audio(self, audio_file_path: str, call_id: str, agent_id: str, customer_id: str) -> Dict[str, Any]:
        """
        Upload an audio file for analysis.
        
        Args:
            audio_file_path: Path to the audio file
            call_id: Unique identifier for the call
            agent_id: ID of the sales agent
            customer_id: ID of the customer/prospect
            
        Returns:
            API response with upload status
        """
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        url = f"{self.base_url}/api/v1/transcribe/upload"
        
        with open(audio_file_path, 'rb') as audio_file:
            files = {
                'audio_file': (os.path.basename(audio_file_path), audio_file, 'audio/wav')
            }
            data = {
                'call_id': call_id,
                'agent_id': agent_id,
                'customer_id': customer_id
            }
            
            print(f"📤 Uploading audio file: {audio_file_path}")
            response = self.session.post(url, files=files, data=data)
            response.raise_for_status()
            
            return response.json()
    
    def check_status(self, call_id: str) -> Dict[str, Any]:
        """
        Check the processing status of a call.
        
        Args:
            call_id: Unique identifier for the call
            
        Returns:
            API response with current status
        """
        url = f"{self.base_url}/api/v1/transcribe/{call_id}/status"
        
        print(f"🔍 Checking status for call: {call_id}")
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def wait_for_completion(self, call_id: str, max_wait_time: int = 300, check_interval: int = 10) -> Dict[str, Any]:
        """
        Wait for call analysis to complete.
        
        Args:
            call_id: Unique identifier for the call
            max_wait_time: Maximum time to wait in seconds
            check_interval: How often to check status in seconds
            
        Returns:
            Final status response
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.check_status(call_id)
            
            if status.get('status') == 'completed':
                print(f"✅ Analysis completed for call: {call_id}")
                return status
            elif status.get('status') == 'failed':
                print(f"❌ Analysis failed for call: {call_id}")
                return status
            
            print(f"⏳ Status: {status.get('status')} - Waiting {check_interval} seconds...")
            time.sleep(check_interval)
        
        raise TimeoutError(f"Analysis did not complete within {max_wait_time} seconds")
    
    def get_transcript(self, call_id: str) -> Dict[str, Any]:
        """
        Get the transcript for a completed call.
        
        Args:
            call_id: Unique identifier for the call
            
        Returns:
            API response with transcript data
        """
        url = f"{self.base_url}/api/v1/transcribe/{call_id}/transcript"
        
        print(f"📝 Getting transcript for call: {call_id}")
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def get_coachable_moments(self, call_id: str) -> Dict[str, Any]:
        """
        Get coachable moments for a completed call.
        
        Args:
            call_id: Unique identifier for the call
            
        Returns:
            API response with coachable moments
        """
        url = f"{self.base_url}/api/v1/transcribe/{call_id}/coachable-moments"
        
        print(f"🎯 Getting coachable moments for call: {call_id}")
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def get_executive_summary(self, call_id: str) -> Dict[str, Any]:
        """
        Get executive summary for a completed call.
        
        Args:
            call_id: Unique identifier for the call
            
        Returns:
            API response with executive summary
        """
        url = f"{self.base_url}/api/v1/transcribe/{call_id}/executive-summary"
        
        print(f"📊 Getting executive summary for call: {call_id}")
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def get_complete_analysis(self, call_id: str) -> Dict[str, Any]:
        """
        Get complete analysis for a call.
        
        Args:
            call_id: Unique identifier for the call
            
        Returns:
            API response with complete analysis
        """
        url = f"{self.base_url}/api/v1/transcribe/{call_id}/analysis"
        
        print(f"🔍 Getting complete analysis for call: {call_id}")
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def convert_text_to_speech(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Convert text to speech.
        
        Args:
            text: Text to convert to speech
            language: Language code (e.g., 'en', 'es', 'fr')
            
        Returns:
            API response with TTS information
        """
        url = f"{self.base_url}/api/v1/speak/"
        
        data = {
            "text": text,
            "language": language
        }
        
        print(f"🔊 Converting text to speech: {text[:50]}...")
        response = self.session.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def replay_moment(self, call_id: str, moment_id: str) -> Dict[str, Any]:
        """
        Replay a specific coachable moment.
        
        Args:
            call_id: Unique identifier for the call
            moment_id: ID of the specific moment
            
        Returns:
            API response with replay information
        """
        url = f"{self.base_url}/api/v1/replay/{call_id}/moment/{moment_id}/replay"
        
        print(f"🔄 Replaying moment {moment_id} for call: {call_id}")
        response = self.session.post(url)
        response.raise_for_status()
        
        return response.json()

def main():
    """Main function demonstrating the API usage."""
    
    # Initialize the client
    client = SalesCallAnalysisClient()
    
    # Example call data
    call_id = "CALL_2024_001"
    agent_id = "agent_001"
    customer_id = "customer_001"
    audio_file_path = "sample_call.wav"  # This would be your actual audio file
    
    try:
        print("🚀 Sales Call Analysis Microservice - API Usage Example")
        print("=" * 60)
        
        # Step 1: Upload audio file
        print("\n📤 Step 1: Uploading Audio File")
        print("-" * 40)
        
        try:
            upload_result = client.upload_audio(audio_file_path, call_id, agent_id, customer_id)
            print(f"✅ Upload successful: {upload_result}")
        except FileNotFoundError:
            print(f"⚠️  Audio file not found: {audio_file_path}")
            print("   Using mock data for demonstration...")
            upload_result = {"status": "uploaded", "call_id": call_id}
        
        # Step 2: Check status and wait for completion
        print("\n⏳ Step 2: Waiting for Analysis Completion")
        print("-" * 40)
        
        try:
            # In a real scenario, you would wait for completion
            # For demo purposes, we'll just check status
            status = client.check_status(call_id)
            print(f"📊 Current status: {status}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Service not available: {e}")
            print("   Using mock data for demonstration...")
            status = {"status": "completed"}
        
        # Step 3: Get analysis results
        print("\n📊 Step 3: Getting Analysis Results")
        print("-" * 40)
        
        if status.get('status') == 'completed':
            try:
                # Get transcript
                transcript = client.get_transcript(call_id)
                print(f"📝 Transcript retrieved: {len(transcript.get('segments', []))} segments")
                
                # Get coachable moments
                moments = client.get_coachable_moments(call_id)
                print(f"🎯 Coachable moments found: {len(moments.get('coachable_moments', []))}")
                
                # Get executive summary
                summary = client.get_executive_summary(call_id)
                print(f"📈 Executive summary generated: {summary.get('call_outcome', 'N/A')}")
                
                # Get complete analysis
                analysis = client.get_complete_analysis(call_id)
                print(f"🔍 Complete analysis available: {analysis.get('analysis_status', 'N/A')}")
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Service not available: {e}")
                print("   Using mock data for demonstration...")
                
                # Mock analysis results
                analysis = {
                    "call_id": call_id,
                    "analysis_status": "completed",
                    "coachable_moments": [
                        {
                            "moment_id": "cm_001",
                            "moment_type": "price_objection",
                            "description": "Customer expressed concern about pricing",
                            "confidence_score": 0.92
                        }
                    ],
                    "executive_summary": {
                        "call_outcome": "successfully_closed",
                        "deal_value": 15000
                    }
                }
        else:
            print(f"⚠️  Analysis not completed. Status: {status.get('status')}")
            return
        
        # Step 4: Demonstrate TTS functionality
        print("\n🔊 Step 4: Text-to-Speech Conversion")
        print("-" * 40)
        
        try:
            tts_result = client.convert_text_to_speech(
                "This is a sample coaching feedback for your sales call.",
                "en"
            )
            print(f"✅ TTS conversion successful: {tts_result}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  TTS service not available: {e}")
        
        # Step 5: Demonstrate replay functionality
        print("\n🔄 Step 5: Replay Functionality")
        print("-" * 40)
        
        if analysis.get('coachable_moments'):
            moment_id = analysis['coachable_moments'][0]['moment_id']
            try:
                replay_result = client.replay_moment(call_id, moment_id)
                print(f"✅ Moment replay successful: {replay_result}")
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Replay service not available: {e}")
        
        # Step 6: Display summary
        print("\n📋 Analysis Summary")
        print("-" * 40)
        
        if 'executive_summary' in analysis:
            summary = analysis['executive_summary']
            print(f"🎯 Call Outcome: {summary.get('call_outcome', 'N/A')}")
            print(f"💰 Deal Value: ${summary.get('deal_value', 0):,}")
            print(f"📅 Next Steps: {len(summary.get('next_steps', []))} items")
        
        if 'coachable_moments' in analysis:
            moments = analysis['coachable_moments']
            print(f"🎯 Coachable Moments: {len(moments)} identified")
            for i, moment in enumerate(moments[:3], 1):  # Show first 3
                print(f"   {i}. {moment.get('moment_type', 'N/A')} - {moment.get('description', 'N/A')}")
        
        print("\n✅ API usage demonstration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        print("   Make sure the Sales Call Analysis Microservice is running on localhost:8000")

if __name__ == "__main__":
    main()
