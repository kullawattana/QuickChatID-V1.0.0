"""
OpenTelemetry Service - Distributed Tracing & Monitoring
End-to-end observability for KYC flow
"""

import time
import json
from typing import Dict, Any, Optional
from contextlib import contextmanager

class TelemetryService:
    """OpenTelemetry instrumentation for KYC"""
    
    def __init__(self, service_name: str = "quickchatid-kyc"):
        self.service_name = service_name
        self.available = self._check_availability()
        self.spans = []  # Mock span storage
        
        if self.available:
            self._init_telemetry()
    
    def _check_availability(self):
        """Check if OpenTelemetry is installed"""
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            return True
        except ImportError:
            return False
    
    def _init_telemetry(self):
        """Initialize OpenTelemetry"""
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
            
            # Set up tracer provider
            provider = TracerProvider()
            processor = BatchSpanProcessor(ConsoleSpanExporter())
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)
            
            self.tracer = trace.get_tracer(self.service_name)
        except Exception as e:
            print(f"Failed to initialize OpenTelemetry: {e}")
            self.available = False
    
    @contextmanager
    def trace_span(self, name: str, attributes: Optional[Dict] = None):
        """
        Create a trace span.
        
        Usage:
            with telemetry.trace_span("kyc.document_verify", {"user_id": "123"}):
                # Do work
                pass
        """
        start_time = time.time()
        span_id = f"span_{len(self.spans)}"
        
        # Store span data
        span_data = {
            'span_id': span_id,
            'name': name,
            'start_time': start_time,
            'attributes': attributes or {}
        }
        
        try:
            if self.available:
                # Use real OpenTelemetry
                from opentelemetry import trace
                with self.tracer.start_as_current_span(name) as span:
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                    yield span
            else:
                # Mock span
                yield MockSpan(span_data)
        
        finally:
            # Record span completion
            span_data['end_time'] = time.time()
            span_data['duration_ms'] = (span_data['end_time'] - start_time) * 1000
            self.spans.append(span_data)
    
    def record_event(self, name: str, attributes: Optional[Dict] = None):
        """Record a single event"""
        event = {
            'name': name,
            'timestamp': time.time(),
            'attributes': attributes or {}
        }
        
        print(f"📊 Event: {name} | {json.dumps(attributes, ensure_ascii=False)}")
        return event
    
    def record_metric(self, name: str, value: float, unit: str = "", attributes: Optional[Dict] = None):
        """Record a metric"""
        metric = {
            'name': name,
            'value': value,
            'unit': unit,
            'timestamp': time.time(),
            'attributes': attributes or {}
        }
        
        print(f"📈 Metric: {name}={value}{unit} | {json.dumps(attributes, ensure_ascii=False)}")
        return metric
    
    def get_spans(self):
        """Get recorded spans"""
        return self.spans
    
    def clear_spans(self):
        """Clear span history"""
        self.spans = []


class MockSpan:
    """Mock span for when OpenTelemetry is not available"""
    
    def __init__(self, data: Dict):
        self.data = data
    
    def set_attribute(self, key: str, value: Any):
        self.data['attributes'][key] = value
    
    def add_event(self, name: str, attributes: Optional[Dict] = None):
        if 'events' not in self.data:
            self.data['events'] = []
        self.data['events'].append({
            'name': name,
            'attributes': attributes or {}
        })


# Singleton
_telemetry_service = None

def get_telemetry_service():
    """Get singleton instance"""
    global _telemetry_service
    if _telemetry_service is None:
        _telemetry_service = TelemetryService()
    return _telemetry_service
