from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True) # Ensure the upload directory exists when the server starts


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Trackman Dashboard API"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"filename": file.filename}

@app.get("/sessions")
def get_sessions():
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".csv")]
    return {"sessions": files}

@app.get("/sessions/{session}/pitch-location")
def get_pitch_locations(session: str):
    file_path = os.path.join(UPLOAD_DIR, session)
    df = pd.read_csv(file_path)
    df = df[["PlateLocSide", "PlateLocHeight", "TaggedPitchType"]]
    df = df.fillna("")
    df = df[(df["PlateLocSide"] != "") & (df["PlateLocHeight"] != "")]
    return df.to_dict(orient="records")

@app.get("/sessions/{session}/velocity")
def get_velocity(session: str):
    file_path = os.path.join(UPLOAD_DIR, session)
    df = pd.read_csv(file_path)
    df = df[["RelSpeed", "TaggedPitchType"]]
    df = df.fillna("")
    df = df[(df["TaggedPitchType"] != "") & (df["RelSpeed"] != "")]
    df["RelSpeed"] = df["RelSpeed"].astype(float)
    return df.to_dict(orient="records")