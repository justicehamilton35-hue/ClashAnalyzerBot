"""
ClashFish Web API Server
FastAPI server for mobile uploads and analysis
"""
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict
import os
import uuid
import shutil
from pathlib import Path
import json
from datetime import datetime

from video_processor import VideoProcessor
from clashfish_engine import ClashFishEngine
from mistake_detector import MistakeDetector
from report_generator import ReportGenerator

# Initialize FastAPI app
app = FastAPI(
    title="ClashFish API",
    description="AI-powered Clash Royale coaching API",
    version="1.0.0"
)

# CORS middleware for mobile access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for mobile
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = Path("uploads")
REPORTS_DIR = Path("reports")
MODELS_DIR = Path("models")

UPLOAD_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# In-memory job storage (use Redis in production)
jobs: Dict[str, Dict] = {}

# Load latest DQN model
def get_latest_model():
    """Find the latest trained model"""
    model_files = list(MODELS_DIR.glob("model_*.pth"))
    if not model_files:
        return None
    latest = max(model_files, key=lambda p: p.stat().st_mtime)
    return str(latest)


class AnalysisStatus(BaseModel):
    """Analysis job status"""
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: int  # 0-100
    message: str
    report_url: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


@app.get("/")
async def root():
    """API information"""
    return {
        "name": "ClashFish API",
        "version": "1.0.0",
        "description": "AI-powered Clash Royale coaching",
        "endpoints": {
            "upload": "/upload",
            "status": "/status/{job_id}",
            "report": "/report/{job_id}",
            "report_html": "/report/{job_id}/html"
        }
    }


@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload a Clash Royale screen recording for analysis

    Args:
        file: Video file (MP4, MOV, AVI)

    Returns:
        Job ID for tracking analysis progress
    """
    # Validate file type
    allowed_extensions = [".mp4", ".mov", ".avi", ".mkv"]
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Save uploaded file
    video_path = UPLOAD_DIR / f"{job_id}{file_ext}"

    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create job entry
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "message": "Video uploaded, queued for analysis",
        "created_at": datetime.now().isoformat(),
        "video_path": str(video_path),
        "filename": file.filename
    }

    # Start background analysis
    background_tasks.add_task(analyze_video, job_id, video_path)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Video uploaded successfully. Analysis starting...",
        "status_url": f"/status/{job_id}"
    }


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """
    Get analysis status for a job

    Args:
        job_id: Job ID from upload

    Returns:
        Current analysis status
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    return AnalysisStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        report_url=f"/report/{job_id}" if job["status"] == "completed" else None,
        created_at=job["created_at"],
        completed_at=job.get("completed_at")
    )


@app.get("/report/{job_id}")
async def get_report(job_id: str):
    """
    Get JSON analysis report

    Args:
        job_id: Job ID

    Returns:
        Complete analysis report in JSON format
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not complete. Status: {job['status']}"
        )

    # Load report
    report_path = REPORTS_DIR / f"{job_id}.json"

    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    with open(report_path, "r") as f:
        report = json.load(f)

    return report


@app.get("/report/{job_id}/html", response_class=HTMLResponse)
async def get_report_html(job_id: str):
    """
    Get HTML analysis report

    Args:
        job_id: Job ID

    Returns:
        HTML formatted report
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != "completed":
        return f"""
        <html>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1>Analysis in Progress</h1>
            <p>Status: {job['status']}</p>
            <p>Progress: {job['progress']}%</p>
            <p>{job['message']}</p>
            <p><a href="/status/{job_id}">Check Status</a></p>
        </body>
        </html>
        """

    # Load HTML report
    report_path = REPORTS_DIR / f"{job_id}.html"

    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    with open(report_path, "r") as f:
        html = f.read()

    return html


@app.get("/report/{job_id}/text")
async def get_report_text(job_id: str):
    """Get plain text report"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not complete")

    report_path = REPORTS_DIR / f"{job_id}.txt"

    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        report_path,
        media_type="text/plain",
        filename=f"clashfish_report_{job_id}.txt"
    )


def analyze_video(job_id: str, video_path: Path):
    """
    Background task to analyze video

    Args:
        job_id: Job ID
        video_path: Path to uploaded video
    """
    try:
        # Update status
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["message"] = "Extracting frames from video..."

        # Load model
        model_path = get_latest_model()
        if not model_path:
            raise Exception("No trained model found")

        # Process video
        processor = VideoProcessor(fps=2.0)
        game_states, actions = processor.process_video(str(video_path))

        jobs[job_id]["progress"] = 40
        jobs[job_id]["message"] = f"Analyzing {len(actions)} moves..."

        # Analyze with engine
        engine = ClashFishEngine(model_path)
        analysis = engine.analyze_game(game_states, actions)

        jobs[job_id]["progress"] = 70
        jobs[job_id]["message"] = "Detecting mistakes..."

        # Detect mistakes
        detector = MistakeDetector()
        mistakes = detector.detect_all_mistakes(game_states, actions, analysis.move_evaluations)

        jobs[job_id]["progress"] = 85
        jobs[job_id]["message"] = "Generating reports..."

        # Generate reports
        generator = ReportGenerator()

        # JSON report
        json_report = generator.generate_json_report(analysis, mistakes)
        with open(REPORTS_DIR / f"{job_id}.json", "w") as f:
            f.write(json_report)

        # HTML report
        html_report = generator.generate_html_report(analysis, mistakes)
        with open(REPORTS_DIR / f"{job_id}.html", "w") as f:
            f.write(html_report)

        # Text report
        text_report = generator.generate_text_report(analysis, mistakes)
        with open(REPORTS_DIR / f"{job_id}.txt", "w") as f:
            f.write(text_report)

        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = "Analysis complete!"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["analysis_summary"] = {
            "accuracy": round(analysis.accuracy_score, 2),
            "total_moves": analysis.total_moves,
            "blunders": analysis.blunders,
            "overall_rating": round(analysis.overall_rating, 2)
        }

    except Exception as e:
        # Handle errors
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Analysis failed: {str(e)}"
        jobs[job_id]["error"] = str(e)

        print(f"Analysis failed for {job_id}: {e}")
        import traceback
        traceback.print_exc()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    model_path = get_latest_model()

    return {
        "status": "healthy",
        "model_loaded": model_path is not None,
        "model_path": model_path,
        "jobs_count": len(jobs)
    }


if __name__ == "__main__":
    import uvicorn

    print("Starting ClashFish API server...")
    print("Model:", get_latest_model())
    print("Access at: http://localhost:8000")
    print("Docs at: http://localhost:8000/docs")

    uvicorn.run(app, host="0.0.0.0", port=8000)
