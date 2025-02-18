from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource

######## Tracer import
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

######## Metrics import
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

######## Logs import
import logging
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

#### Flask import
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from flask import Flask, render_template

# Load Env File
import os
from dotenv import load_dotenv
load_dotenv()

# Load envs
OTEL_ENDPOINT = os.getenv("OTEL_ENDPOINT")
APP_NAME = os.getenv("APP_NAME") 
APP_VERSION = os.getenv("APP_VERSION")

# Set service name and version
resource = Resource(attributes={
    SERVICE_NAME: APP_NAME,
    SERVICE_VERSION: APP_VERSION
})

######## Traces
traceProvider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://"+OTEL_ENDPOINT+":4318/v1/traces"))
traceProvider.add_span_processor(processor)
trace.set_tracer_provider(traceProvider)

######## Metrics
reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="http://"+OTEL_ENDPOINT+":4318/v1/metrics")
)
meterProvider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(meterProvider)

######## Logs
# Create and set the logger provider
logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)

# Create the OTLP log exporter that sends logs to configured destination
exporter = OTLPLogExporter(endpoint="http://"+OTEL_ENDPOINT+":4317")
logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

# Attach OTLP handler to root logger
handler = LoggingHandler(logger_provider=logger_provider)

def sendlog(message, handler):
    logging.getLogger().addHandler(handler)
    # You can use logging directly anywhere in your app now
    logging.warning(message)
    # Ensure the logger is shutdown before exiting so all pending logs are exported
    logger_provider.shutdown()

# Flask app
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

# Route to serve the index.html file
@app.route("/")
def index():
    sendlog("Home loaded", handler)
    return render_template("index.html")

# Route to serve force an Exception
@app.route("/splunk")
def error():
    raise Exception("Unexpected error")

# Custom 500 handler
@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500

# Custom 404 handler
@app.errorhandler(404)
def page_not_found(error):
    sendlog("404 error", handler)
    return render_template("404.html"), 404 

# Main application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)