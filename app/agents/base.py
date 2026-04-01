import dspy
import os
from app.config.settings import settings
from strands.telemetry import StrandsTelemetry
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry import trace


class BaseAgent:
    _otel_initialized = False   # ⭐ class-level flag
    _otel_provider = None       # ⭐ class-level tracer provider cache

    def __init__(self):
        # 1. Logic Observability (LangSmith)
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT

        # 2. Operational Observability (Strands OTEL → Grafana Cloud)
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = settings.GRAFANA_OTEL_ENDPOINT
        os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = settings.GRAFANA_OTEL_HEADERS
        os.environ["OTEL_SERVICE_NAME"] = "strands-agent"

        # ⭐ Initialize OTEL only once
        if not BaseAgent._otel_initialized:
            self._initialize_otel()
            BaseAgent._otel_initialized = True

        # 3. Strands Telemetry (reuse provider to avoid duplicate set_tracer_provider calls)
        provider = BaseAgent._otel_provider or trace.get_tracer_provider()
        self.telemetry = StrandsTelemetry(tracer_provider=provider)

        # 4. LM Configuration
        self.lm = dspy.LM(
            model="groq/llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY,
            api_base="https://api.groq.com/openai/v1",
            cache=False
        )

        # 5. Global DSPy Config
        dspy.settings.configure(lm=self.lm)


    # ---------------------------------------------------------
    # ⭐ One-time OTEL initialization
    # ---------------------------------------------------------
    def _initialize_otel(self):
        resource = Resource.create({
            "service.name": "strands-agent",
            "service.namespace": "agentic-system",
            "service.instance.id": "planner-node"
        })

        provider = TracerProvider(resource=resource)

        # Parse OTLP headers safely
        raw_headers = settings.GRAFANA_OTEL_HEADERS or ""
        headers = {}
        for entry in [x.strip() for x in raw_headers.split(",") if x.strip()]:
            if "=" not in entry:
                continue
            key, value = entry.split("=", 1)
            headers[key.strip()] = value.strip()

        exporter = OTLPSpanExporter(
            endpoint=settings.GRAFANA_OTEL_ENDPOINT,
            headers=headers,
        )

        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

        # Avoid overriding the global provider if already set by another part of the app.
        existing_provider = trace.get_tracer_provider()

        # Acceptably replace proxy/no-op provider, but skip if a real provider already exists.
        from opentelemetry.trace import NoOpTracerProvider, ProxyTracerProvider

        if isinstance(existing_provider, (NoOpTracerProvider, ProxyTracerProvider)):
            try:
                trace.set_tracer_provider(provider)
                print("✅ OTEL TracerProvider set successfully")
            except Exception as exc:
                msg = str(exc)
                if "Overriding of current TracerProvider is not allowed" in msg:
                    print("⚠️ OTEL TracerProvider already set (race or existing config) — keeping current provider")
                else:
                    raise
            BaseAgent._otel_provider = trace.get_tracer_provider()
            return

        # If a provider is already set and it's not a proxy/noop, preserve it and skip.
        print("⚠️ OTEL TracerProvider already set — skipping override")
        BaseAgent._otel_provider = existing_provider


