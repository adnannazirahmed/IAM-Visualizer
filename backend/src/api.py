import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict

from src.models import GraphOutput
from src.pipeline import load_sample, load_live, process_iam_data

app = FastAPI(title="AWS IAM Privilege-Escalation Visualizer API")

# Configure CORS for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/samples")
def list_samples() -> Dict[str, List[str]]:
    import glob
    from pathlib import Path
    
    base_dir = Path(__file__).parent.parent
    sample_dir = base_dir / "sample_data"
    
    samples = []
    if sample_dir.exists():
        for file in sample_dir.glob("*.json"):
            samples.append(file.stem)
            
    return {"samples": samples}

@app.get("/api/graph", response_model=GraphOutput)
def get_graph(source: str = Query("sample"), dataset: str = Query("small_org")):
    try:
        if source == "live":
            iam_data = load_live()
            graph_output = process_iam_data(iam_data)
            graph_output.metadata.source = "live"
            return graph_output
        elif source == "sample":
            iam_data = load_sample(dataset)
            graph_output = process_iam_data(iam_data)
            graph_output.metadata.source = "sample"
            return graph_output
        else:
            raise HTTPException(status_code=400, detail="Invalid source parameter. Must be 'sample' or 'live'.")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
