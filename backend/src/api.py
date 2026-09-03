from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.models import GraphOutput
from src.pipeline import load_live, process_iam_data

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

@app.get("/api/graph", response_model=GraphOutput)
def get_graph():
    try:
        iam_data = load_live()
        graph_output = process_iam_data(iam_data)
        graph_output.metadata.source = "live"
        return graph_output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
