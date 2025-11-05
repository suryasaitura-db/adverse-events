import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Postmarket Safety Surveillance API",
    description="Backend API for Postmarket Safety Surveillance and Adverse Event Reporting",
    version="1.0.0",
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class WorkflowStatus(BaseModel):
    name: str
    late: int
    overNormal: int
    normal: int
    total: int
    site: str
    stage: str

class AdverseEvent(BaseModel):
    id: str
    caseId: str
    patientId: str
    productName: str
    eventDescription: str
    severity: str  # Mild, Moderate, Severe
    status: str  # Open, Under Review, Closed
    reportDate: str
    reporterType: str  # Healthcare Professional, Consumer, etc.
    site: str

class CaseDetail(BaseModel):
    caseId: str
    patientInitials: str
    age: int
    gender: str
    productName: str
    eventDescription: str
    severity: str
    status: str
    workflowStage: str
    reportDate: str
    dueDate: str
    assignedTo: str
    site: str

# Mock data for workflow status
MOCK_WORKFLOW_DATA = [
    WorkflowStatus(name="Germany Data Entry", late=8, overNormal=8, normal=0, total=16, site="Germany", stage="Data Entry"),
    WorkflowStatus(name="Germany Expediting Reporting", late=43, overNormal=49, normal=0, total=92, site="Germany", stage="Expediting Reporting"),
    WorkflowStatus(name="Germany Medical Review", late=3, overNormal=3, normal=0, total=6, site="Germany", stage="Medical Review"),
    WorkflowStatus(name="Japan Reporting", late=4, overNormal=4, normal=0, total=8, site="Japan", stage="Reporting"),
    WorkflowStatus(name="Japan Validation", late=2, overNormal=2, normal=0, total=4, site="Japan", stage="Validation"),
    WorkflowStatus(name="US Medical Review", late=12, overNormal=12, normal=0, total=24, site="United States", stage="Medical Review"),
    WorkflowStatus(name="US Data Entry", late=13, overNormal=13, normal=0, total=26, site="United States", stage="Data Entry"),
    WorkflowStatus(name="US Reporting", late=23, overNormal=23, normal=0, total=46, site="United States", stage="Reporting"),
    WorkflowStatus(name="US Validation", late=8, overNormal=8, normal=0, total=16, site="United States", stage="Validation"),
]

# Mock data for adverse events
MOCK_ADVERSE_EVENTS = [
    AdverseEvent(
        id="AE001",
        caseId="CASE-2024-001",
        patientId="P12345",
        productName="DrugX-500mg",
        eventDescription="Patient reported severe headache and nausea",
        severity="Moderate",
        status="Under Review",
        reportDate="2024-01-15",
        reporterType="Healthcare Professional",
        site="Germany"
    ),
    AdverseEvent(
        id="AE002",
        caseId="CASE-2024-002",
        patientId="P12346",
        productName="VaccineY",
        eventDescription="Injection site reaction with swelling",
        severity="Mild",
        status="Open",
        reportDate="2024-01-16",
        reporterType="Consumer",
        site="United States"
    ),
    AdverseEvent(
        id="AE003",
        caseId="CASE-2024-003",
        patientId="P12347",
        productName="DrugZ-100mg",
        eventDescription="Allergic reaction with respiratory distress",
        severity="Severe",
        status="Under Review",
        reportDate="2024-01-17",
        reporterType="Healthcare Professional",
        site="Japan"
    ),
]

# API Routes
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Postmarket Safety Surveillance",
        "environment": os.getenv("ENV", "development"),
        "version": "1.0.0"
    }

@app.get("/api/workflow-status", response_model=List[WorkflowStatus])
async def get_workflow_status(
    site: Optional[str] = Query(None, description="Filter by site"),
    stage: Optional[str] = Query(None, description="Filter by workflow stage")
):
    """Get workflow status data for all sites and stages"""
    data = MOCK_WORKFLOW_DATA

    if site and site != "<All>":
        data = [item for item in data if item.site == site]

    if stage:
        data = [item for item in data if item.stage == stage]

    return data

@app.get("/api/adverse-events", response_model=List[AdverseEvent])
async def get_adverse_events(
    site: Optional[str] = Query(None, description="Filter by site"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of results")
):
    """Get adverse event reports"""
    data = MOCK_ADVERSE_EVENTS

    if site:
        data = [event for event in data if event.site == site]

    if severity:
        data = [event for event in data if event.severity == severity]

    if status:
        data = [event for event in data if event.status == status]

    return data[:limit]

@app.get("/api/adverse-events/{event_id}", response_model=AdverseEvent)
async def get_adverse_event(event_id: str):
    """Get detailed information about a specific adverse event"""
    for event in MOCK_ADVERSE_EVENTS:
        if event.id == event_id:
            return event
    raise HTTPException(status_code=404, detail="Adverse event not found")

@app.get("/api/cases")
async def get_cases(
    site: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    workflow_stage: Optional[str] = Query(None),
    limit: int = Query(50)
):
    """Get case list with filters"""
    # Mock case data
    cases = [
        {
            "caseId": f"CASE-2024-{str(i).zfill(3)}",
            "patientInitials": f"P.{chr(65 + (i % 26))}",
            "productName": ["DrugX-500mg", "VaccineY", "DrugZ-100mg"][i % 3],
            "status": ["Open", "Under Review", "Closed"][i % 3],
            "workflowStage": ["Data Entry", "Medical Review", "Reporting", "Validation"][i % 4],
            "reportDate": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
            "site": ["Germany", "United States", "Japan"][i % 3],
            "severity": ["Mild", "Moderate", "Severe"][i % 3]
        }
        for i in range(1, 51)
    ]

    if site:
        cases = [c for c in cases if c["site"] == site]
    if status:
        cases = [c for c in cases if c["status"] == status]
    if workflow_stage:
        cases = [c for c in cases if c["workflowStage"] == workflow_stage]

    return cases[:limit]

@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    """Get summary statistics for dashboard"""
    total_late = sum(item.late for item in MOCK_WORKFLOW_DATA)
    total_over_normal = sum(item.overNormal for item in MOCK_WORKFLOW_DATA)
    total_normal = sum(item.normal for item in MOCK_WORKFLOW_DATA)

    return {
        "totalCases": total_late + total_over_normal + total_normal,
        "lateCases": total_late,
        "overNormalCases": total_over_normal,
        "normalCases": total_normal,
        "totalAdverseEvents": len(MOCK_ADVERSE_EVENTS),
        "criticalEvents": len([e for e in MOCK_ADVERSE_EVENTS if e.severity == "Severe"]),
        "sitesCount": 3,
        "openCases": len([e for e in MOCK_ADVERSE_EVENTS if e.status in ["Open", "Under Review"]])
    }

@app.get("/api/dashboard/kpis")
async def get_dashboard_kpis():
    """Get KPI statistics for overview dashboard"""
    total_late = sum(item.late for item in MOCK_WORKFLOW_DATA)
    total_over_normal = sum(item.overNormal for item in MOCK_WORKFLOW_DATA)
    total_normal = sum(item.normal for item in MOCK_WORKFLOW_DATA)

    return {
        "totalCases": total_late + total_over_normal + total_normal,
        "totalDrugs": 150,  # Mock data - replace with actual Unity Catalog query
        "highRiskDrugs": 12,  # Mock data - replace with actual Unity Catalog query
        "totalAdverseEvents": len(MOCK_ADVERSE_EVENTS)
    }

@app.get("/api/sites")
async def get_sites():
    """Get list of available sites"""
    return [
        {"id": "germany", "name": "Relsys Germany", "country": "Germany"},
        {"id": "japan", "name": "Relsys Japan", "country": "Japan"},
        {"id": "us", "name": "Relsys United States", "country": "United States"}
    ]

# Serve static files from frontend build
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React SPA for all non-API routes"""
        # Serve static files
        if full_path.startswith("assets/"):
            file_path = static_dir / full_path
            if file_path.exists():
                return FileResponse(file_path)

        # Serve index.html for all other routes (SPA client-side routing)
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)

        raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
