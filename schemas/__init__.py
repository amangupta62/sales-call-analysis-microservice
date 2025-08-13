"""Schemas package for sales call analysis microservice."""

from .sales_call import (
    SalesCallBase,
    SalesCallCreate,
    SalesCallResponse,
    TranscriptSegment,
    TranscriptResponse,
    CoachableMomentResponse,
    ExecutiveSummaryResponse,
    TTSRequest,
    TTSResponse,
    AudioUploadResponse,
    CoachableMomentDetectionResponse,
    SalesCallAnalysisResponse
)

__all__ = [
    "SalesCallBase",
    "SalesCallCreate", 
    "SalesCallResponse",
    "TranscriptSegment",
    "TranscriptResponse",
    "CoachableMomentResponse",
    "ExecutiveSummaryResponse",
    "TTSRequest",
    "TTSResponse",
    "AudioUploadResponse",
    "CoachableMomentDetectionResponse",
    "SalesCallAnalysisResponse"
]
