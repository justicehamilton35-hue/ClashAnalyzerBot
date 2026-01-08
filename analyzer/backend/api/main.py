"""
FastAPI Backend for Clash Royale Analyzer
Provides REST API for video upload and analysis
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import uuid
import os
from pathlib import Path
import shutil
import json
from datetime import datetime
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from analyzer.engine.analyzer import ClashRoyaleAnalyzer


app = FastAPI(
    title="Clash Royale Analyzer API",
    description="Stockfish for Clash Royale - Video analysis API",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage paths
UPLOAD_DIR = Path("analyzer/data/videos")
ANALYSIS_DIR = Path("analyzer/data/analysis_results")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory storage for analysis status (use Redis/DB in production)
analysis_jobs = {}


# Pydantic models
class AnalysisRequest(BaseModel):
    """Request model for starting analysis"""
    fps: int = 2
    save_frames: bool = False


class AnalysisStatus(BaseModel):
    """Analysis job status"""
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: float  # 0.0 to 1.0
    message: str
    result_path: Optional[str] = None
    error: Optional[str] = None


class AnalysisResult(BaseModel):
    """Complete analysis result"""
    job_id: str
    video_path: str
    analysis_timestamp: str
    accuracy_score: float
    playstyle: str
    move_quality: Dict
    timeline: List[Dict]
    moves: List[Dict]
    insights: Dict


# Initialize analyzer (singleton)
try:
    analyzer = ClashRoyaleAnalyzer()
except Exception as e:
    print(f"Warning: Could not initialize analyzer: {e}")
    analyzer = None


@app.get("/")
def root():
    """API root endpoint"""
    return {
        "name": "Clash Royale Analyzer API",
        "version": "1.0.0",
        "description": "Stockfish for Clash Royale",
        "endpoints": {
            "upload": "/api/upload",
            "analyze": "/api/analyze/{job_id}",
            "status": "/api/status/{job_id}",
            "result": "/api/result/{job_id}",
            "jobs": "/api/jobs"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "analyzer_initialized": analyzer is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a Clash Royale gameplay video

    Returns:
        job_id: Unique identifier for this analysis job
    """
    # Validate file type
    if not file.filename.endswith(('.mp4', '.MP4')):
        raise HTTPException(status_code=400, detail="Only MP4 files are supported")

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Save uploaded file
    video_path = UPLOAD_DIR / f"{job_id}.mp4"

    try:
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")

    # Create analysis job
    analysis_jobs[job_id] = {
        "job_id": job_id,
        "status": "uploaded",
        "progress": 0.0,
        "message": "Video uploaded successfully",
        "video_path": str(video_path),
        "upload_timestamp": datetime.now().isoformat(),
        "result_path": None,
        "error": None
    }

    return {
        "job_id": job_id,
        "message": "Video uploaded successfully",
        "video_size_mb": video_path.stat().st_size / (1024 * 1024)
    }


@app.post("/api/analyze/{job_id}")
async def start_analysis(job_id: str,
                        background_tasks: BackgroundTasks,
                        request: AnalysisRequest = AnalysisRequest()):
    """
    Start analyzing an uploaded video

    Args:
        job_id: Job ID from upload endpoint
        request: Analysis configuration
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = analysis_jobs[job_id]

    if job["status"] == "processing":
        raise HTTPException(status_code=400, detail="Analysis already in progress")

    if job["status"] == "completed":
        raise HTTPException(status_code=400, detail="Analysis already completed")

    # Update status
    analysis_jobs[job_id]["status"] = "processing"
    analysis_jobs[job_id]["message"] = "Starting analysis..."
    analysis_jobs[job_id]["progress"] = 0.1

    # Start background analysis
    background_tasks.add_task(
        run_analysis,
        job_id,
        job["video_path"],
        request.fps,
        request.save_frames
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Analysis started"
    }


async def run_analysis(job_id: str, video_path: str, fps: int, save_frames: bool):
    """Background task to run analysis"""
    try:
        if not analyzer:
            raise Exception("Analyzer not initialized")

        # Update progress
        analysis_jobs[job_id]["progress"] = 0.2
        analysis_jobs[job_id]["message"] = "Processing video..."

        # Create output directory
        output_dir = ANALYSIS_DIR / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run analysis
        result = analyzer.analyze_video(
            video_path,
            output_dir=str(output_dir),
            fps=fps,
            save_frames=save_frames
        )

        # Update job status
        analysis_jobs[job_id]["status"] = "completed"
        analysis_jobs[job_id]["progress"] = 1.0
        analysis_jobs[job_id]["message"] = "Analysis completed"
        analysis_jobs[job_id]["result_path"] = str(output_dir / "analysis_report.json")
        analysis_jobs[job_id]["completion_timestamp"] = datetime.now().isoformat()

    except Exception as e:
        # Update job with error
        analysis_jobs[job_id]["status"] = "failed"
        analysis_jobs[job_id]["progress"] = 0.0
        analysis_jobs[job_id]["message"] = "Analysis failed"
        analysis_jobs[job_id]["error"] = str(e)


@app.get("/api/status/{job_id}")
def get_analysis_status(job_id: str):
    """
    Get status of an analysis job

    Returns:
        AnalysisStatus with current progress
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = analysis_jobs[job_id]

    return AnalysisStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        result_path=job.get("result_path"),
        error=job.get("error")
    )


@app.get("/api/result/{job_id}")
def get_analysis_result(job_id: str):
    """
    Get complete analysis result

    Returns:
        Full analysis report
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = analysis_jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not completed (status: {job['status']})"
        )

    result_path = job.get("result_path")
    if not result_path or not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Result file not found")

    # Load result
    with open(result_path, 'r') as f:
        result = json.load(f)

    return result


@app.get("/api/jobs")
def list_jobs():
    """
    List all analysis jobs

    Returns:
        List of all jobs with their status
    """
    return {
        "total_jobs": len(analysis_jobs),
        "jobs": [
            {
                "job_id": job_id,
                "status": job["status"],
                "upload_timestamp": job.get("upload_timestamp"),
                "completion_timestamp": job.get("completion_timestamp")
            }
            for job_id, job in analysis_jobs.items()
        ]
    }


@app.delete("/api/job/{job_id}")
def delete_job(job_id: str):
    """
    Delete an analysis job and its data

    Args:
        job_id: Job ID to delete
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = analysis_jobs[job_id]

    # Delete video file
    video_path = Path(job["video_path"])
    if video_path.exists():
        video_path.unlink()

    # Delete result directory
    result_dir = ANALYSIS_DIR / job_id
    if result_dir.exists():
        shutil.rmtree(result_dir)

    # Remove from jobs
    del analysis_jobs[job_id]

    return {"message": f"Job {job_id} deleted successfully"}


@app.get("/api/download/{job_id}/{file_type}")
def download_file(job_id: str, file_type: str):
    """
    Download analysis files

    Args:
        job_id: Job ID
        file_type: Type of file (report, timeline, summary)
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = analysis_jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")

    result_dir = ANALYSIS_DIR / job_id

    file_map = {
        "report": result_dir / "analysis_report.json",
        "timeline": result_dir / "game_timeline.json",
        "summary": result_dir / "summary.txt"
    }

    if file_type not in file_map:
        raise HTTPException(status_code=400, detail="Invalid file type")

    file_path = file_map[file_type]

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_path,
        filename=f"{job_id}_{file_type}.{file_path.suffix}",
        media_type="application/octet-stream"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
