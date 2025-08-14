# Full Workflow Demo Script

## 🚀 Overview

The `full_workflow_demo.py` script demonstrates the **complete end-to-end functionality** of the Sales Call Analysis Microservice, from audio input to text-to-speech output.

## 🔄 Complete Workflow Demonstrated

### **Step 1: Audio Input Preparation**
- Creates sample audio files for demonstration
- Supports custom audio file uploads
- Generates realistic audio patterns (sine waves with variations)

### **Step 2: Audio Upload & Processing**
- Uploads audio to the microservice
- Handles file validation and error cases
- Provides real-time upload status

### **Step 3: Analysis Processing**
- Waits for AI-powered analysis completion
- Monitors processing status
- Handles timeouts gracefully

### **Step 4: Results Retrieval**
- Fetches complete transcript
- Retrieves coachable moments
- Gets executive summary
- Downloads complete analysis

### **Step 5: Analysis Display**
- Shows comprehensive call analysis
- Displays sentiment scores
- Lists coachable moments with confidence scores
- Presents performance metrics

### **Step 6: Text-to-Speech Conversion**
- Converts executive summary to audio
- Generates coaching feedback audio
- Creates accessible audio versions of insights

### **Step 7: Workflow Summary**
- Shows complete process completion
- Lists all accomplished tasks
- Demonstrates business value

## 🛠️ Installation & Setup

### **Prerequisites**
```bash
# Install required packages
pip install -r requirements_demo.txt

# Or install manually
pip install requests numpy
```

### **Service Requirements**
- Sales Call Analysis Microservice running on `localhost:8000`
- All services (FastAPI, Celery, Redis, PostgreSQL) operational

## 🎯 Usage

### **Basic Demo (Recommended)**
```bash
cd examples
python full_workflow_demo.py

# Choose option 1 for sample audio
```

### **Custom Audio Demo**
```bash
cd examples
python full_workflow_demo.py

# Choose option 2 and provide your audio file path
```

### **Programmatic Usage**
```python
from full_workflow_demo import FullWorkflowDemo

# Initialize demo
demo = FullWorkflowDemo(base_url="http://your-service:8000")

# Run with sample audio
demo.run_full_workflow(use_sample_audio=True)

# Run with custom audio
demo.run_full_workflow(use_sample_audio=False, audio_file_path="path/to/audio.wav")
```

## 📁 Generated Files

The demo creates several files in the `examples/temp/` directory:

- **Sample Audio**: `sample_call_[timestamp].wav`
- **Executive Summary Audio**: `executive_summary_DEMO_CALL_001.wav`
- **Coaching Feedback Audio**: `coaching_feedback_DEMO_CALL_001.wav`

## 🔧 Customization

### **Modify Demo Parameters**
```python
# Change demo call details
demo.demo_call_id = "YOUR_CALL_ID"
demo.demo_agent_id = "YOUR_AGENT_ID"
demo.demo_customer_id = "YOUR_CUSTOMER_ID"

# Adjust audio generation
audio_file = demo.create_sample_audio(duration_seconds=60)  # 1 minute
```

### **Custom Audio Generation**
```python
# Generate different audio patterns
def create_custom_audio(self, duration_seconds: int = 30):
    # Your custom audio generation logic
    pass
```

### **Extend Analysis Display**
```python
def custom_display(self, analysis: Dict[str, Any]):
    # Your custom display logic
    pass
```

## 🎵 Audio File Support

### **Supported Formats**
- **Primary**: WAV (16-bit, mono, 16kHz)
- **Generated**: WAV files for TTS output
- **Custom**: Any audio format your service supports

### **Audio Generation**
- **Sample Rate**: 16,000 Hz (optimal for speech)
- **Channels**: Mono (single channel)
- **Bit Depth**: 16-bit
- **Pattern**: Multi-frequency sine waves with silence variations

## 🚨 Error Handling

### **Service Unavailable**
- Gracefully falls back to mock data
- Continues demonstration with simulated results
- Provides clear error messages

### **File Issues**
- Handles missing audio files
- Creates temporary directories automatically
- Cleans up generated files after demo

### **Network Issues**
- Retries failed API calls
- Implements timeout handling
- Shows connection status

## 📊 Mock Data

When the service is unavailable, the demo uses comprehensive mock data:

- **Realistic Transcript**: 1,247 words with confidence scores
- **Coachable Moments**: Price objections, feature explanations
- **Executive Summary**: Successful close with $15,000 deal value
- **Performance Metrics**: Objections handled, close rates, efficiency scores

## 🔍 Debugging

### **Enable Verbose Logging**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### **Check Service Status**
```bash
# Test if service is running
curl http://localhost:8000/health

# Check API documentation
curl http://localhost:8000/docs
```

### **Common Issues**
1. **Service Not Running**: Start the microservice first
2. **Port Conflicts**: Check if port 8000 is available
3. **Dependencies**: Install required packages
4. **Audio Permissions**: Ensure write access to temp directory

## 🎯 Business Value Demonstration

This demo showcases:

- **End-to-End Automation**: Complete workflow from audio to insights
- **AI-Powered Analysis**: Real-time transcription and coaching detection
- **Business Intelligence**: Executive summaries and performance metrics
- **Accessibility**: Audio versions of all insights
- **Scalability**: Can handle multiple concurrent calls
- **Integration Ready**: Clean API for system integration

## 🔗 Related Files

- **`sample_call_analysis.md`**: Human-readable analysis example
- **`api_response_example.json`**: API response structure
- **`api_usage_example.py`**: Basic API usage examples
- **`README.md`**: General examples overview

## 🚀 Next Steps

After running the demo:

1. **Review Results**: Understand the analysis output
2. **Customize**: Modify for your specific use case
3. **Integrate**: Connect with your existing systems
4. **Scale**: Deploy to production environment
5. **Extend**: Add custom analysis features

---

*This demo provides a comprehensive understanding of how the Sales Call Analysis Microservice transforms raw audio into actionable business intelligence.*
