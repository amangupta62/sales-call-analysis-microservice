# Examples Directory

This directory contains comprehensive examples demonstrating the capabilities of the Sales Call Analysis Microservice.

## 📁 Files Overview

### 1. `sample_call_analysis.md`
**Complete example of a sales call analysis output**

This file shows what the microservice produces when analyzing a real sales call:

- **Raw Audio Transcription**: Complete speech-to-text output with timestamps
- **AI-Powered Analysis**: Sentiment analysis, coachable moments, and insights
- **Coachable Moments**: 5 specific moments identified with coaching recommendations
- **Executive Summary**: Business-focused summary with action items
- **Replay Functionality**: Audio clips and coaching feedback

**Perfect for**: Understanding the complete output format and business value

### 2. `api_response_example.json`
**Actual API response format**

This JSON file shows the exact structure of API responses:

- **Call Metadata**: Basic call information
- **Transcription Data**: Speech-to-text results with confidence scores
- **Sentiment Analysis**: Detailed sentiment breakdown
- **Coachable Moments**: Structured coaching opportunities
- **Performance Metrics**: Quantitative call analysis
- **Replay URLs**: Audio access endpoints

**Perfect for**: Developers integrating with the API

### 3. `api_usage_example.py`
**Python client implementation**

A complete Python script showing how to use the microservice:

- **Audio Upload**: How to submit audio files for analysis
- **Status Checking**: Monitoring analysis progress
- **Result Retrieval**: Getting transcripts, moments, and summaries
- **TTS Conversion**: Text-to-speech functionality
- **Moment Replay**: Accessing specific coaching moments

**Perfect for**: Developers building integrations or testing the API

## 🚀 How to Use These Examples

### For Business Users
1. **Read `sample_call_analysis.md`** to understand the output quality
2. **Focus on the Executive Summary** section for business insights
3. **Review Coachable Moments** to see coaching opportunities
4. **Check Performance Metrics** for quantitative analysis

### For Developers
1. **Study `api_response_example.json`** for API structure
2. **Run `api_usage_example.py`** to test the API
3. **Modify the Python script** for your specific use case
4. **Use the examples** as templates for your integration

### For Sales Managers
1. **Review the coaching recommendations** in coachable moments
2. **Understand the performance metrics** and what they mean
3. **See how objections are handled** and scored
4. **Learn about the replay functionality** for training

## 🔧 Running the Python Example

### Prerequisites
```bash
pip install requests
```

### Basic Usage
```bash
# Make sure the microservice is running
cd examples
python api_usage_example.py
```

### Customization
```python
# Modify these variables in the script
call_id = "YOUR_CALL_ID"
agent_id = "YOUR_AGENT_ID"
customer_id = "YOUR_CUSTOMER_ID"
audio_file_path = "path/to/your/audio.wav"
```

## 📊 What You'll Learn

### From the Sample Analysis
- **How coachable moments are identified** with confidence scores
- **What coaching recommendations look like** with specific improvements
- **How sentiment analysis works** throughout the call
- **What executive summaries contain** for business decisions

### From the API Response
- **Complete data structure** for integration
- **Confidence scores** and reliability metrics
- **Audio access URLs** for replay functionality
- **Performance metrics** for call evaluation

### From the Python Script
- **Complete API workflow** from upload to results
- **Error handling** and status checking
- **How to integrate** with your existing systems
- **Best practices** for API usage

## 🎯 Key Takeaways

1. **Business Value**: The microservice transforms raw audio into actionable insights
2. **Technical Excellence**: Clean API design with comprehensive data
3. **Coaching Focus**: Specific, actionable feedback for sales improvement
4. **Scalability**: Can handle multiple calls simultaneously
5. **Integration Ready**: Well-structured API for easy system integration

## 🔗 Related Documentation

- **Main README**: Project overview and setup
- **API Documentation**: Available at `/docs` when service is running
- **Docker Setup**: Containerized deployment instructions
- **Configuration**: Environment variables and settings

---

*These examples demonstrate the real-world capabilities of the Sales Call Analysis Microservice. Use them to understand the value proposition, technical implementation, and business impact.*
