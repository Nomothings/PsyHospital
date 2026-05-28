"""
Psychiatric AI Consultation System - Flask Web API

Provides REST API endpoints for the frontend.
Uses a layered architecture: routes -> services -> repositories

How to start:
    python web/app.py

Access:
    http://localhost:5000
"""
import os
import sys
import traceback
from pathlib import Path
from flask import Flask, render_template

# Add project root and src/ to path so we can import project modules
# src/ is needed for the mental_hospital package (or install via: pip install -e .)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================
# Path configuration (loaded centrally from config module)
# ============================================================
from config import (
    DATA_DIR, LOG_DIR, RECORDS_DIR, DIAGNOSES_DIR,
)
from service_layer.evaluation_service import (
    evaluate_phase as _evaluate_phase,
    evaluate_phase2_accuracy as _evaluate_phase2_accuracy,
)

# ============================================================
# Initialize logging
# ============================================================

from service_layer.logging_config import setup_logging
setup_logging(LOG_DIR, level="INFO")

import logging
logger = logging.getLogger(__name__)

# ============================================================
# Initialize service layer
# ============================================================

from service_layer.case_service import CaseService
from service_layer.record_service import RecordService
from service_layer.diagnosis_service import DiagnosisService
case_service = CaseService(DATA_DIR)
record_service = RecordService(RECORDS_DIR)
diagnosis_service = DiagnosisService(DIAGNOSES_DIR)

# ============================================================
# Initialize route layer
# ============================================================

from routes.case_routes import register_case_routes
from routes.record_routes import register_record_routes
from routes.diagnosis_routes import register_diagnosis_routes
from routes.chat_routes import register_chat_routes
from routes.check_routes import register_check_routes
from routes.case_writing_routes import register_case_writing_routes
from routes.treatment_routes import register_treatment_routes
from routes.legacy_routes import register_legacy_routes

# ============================================================
# Flask Application
# ============================================================

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

# Register Blueprint routes (each Blueprint has its own url_prefix, independent of each other)
app.register_blueprint(register_case_routes(case_service))
app.register_blueprint(register_record_routes(record_service))
app.register_blueprint(register_diagnosis_routes(diagnosis_service))
app.register_blueprint(register_chat_routes(case_service))
app.register_blueprint(register_check_routes(case_service))
app.register_blueprint(register_case_writing_routes(record_service))
app.register_blueprint(register_treatment_routes(record_service))
app.register_blueprint(register_legacy_routes(
    case_service, _evaluate_phase, _evaluate_phase2_accuracy
))


# ============================================================
# Page routes
# ============================================================

@app.route("/")
def index():
    """Render main page"""
    return render_template("index.html")

if __name__ == "__main__":
    debug_mode = False
    print("\n" + "=" * 60)
    print("  Psychiatric AI Consultation System - Web Frontend")
    print("  URL: http://localhost:5000")
    print(f"  Debug mode: {debug_mode}")
    print("=" * 60 + "\n")
    try:
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except Exception:
        print("Flask startup failed. Traceback:")
        traceback.print_exc()
        raise
