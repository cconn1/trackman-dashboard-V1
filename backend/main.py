from sqlite3 import IntegrityError

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

from database import Hit, Pitch, Session, SessionLocal, init_db
init_db()

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
async def upload_file(file: UploadFile = File(...), label: str = "", practice_type: str = ""):
    # Step 1 — save file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Step 2 — parse CSV
    df = pd.read_csv(file_path)
    df = df.where(pd.notnull(df), None)

    # Step 3 — create session record
    db = SessionLocal()
    try:
        session = Session(
            filename=file.filename,
            label=label or file.filename,
            pitch_count=len(df),
            practice_type=practice_type
        )
        db.add(session)
        db.flush()  # gets session.id without committing yet

        # Step 4 — insert pitches
        for _, row in df.iterrows():
            pitch = Pitch(
                session_id=session.id,
                pitch_no=row.get("PitchNo"),
                date=str(row.get("Date")) if row.get("Date") else None,
                time=str(row.get("Time")) if row.get("Time") else None,
                pitcher=row.get("Pitcher"),
                pitcher_id=str(row.get("PitcherId")) if row.get("PitcherId") else None,
                pitcher_throws=row.get("PitcherThrows"),
                pitcher_team=row.get("PitcherTeam"),
                pitcher_set=row.get("PitcherSet"),
                play_id=str(row.get("PlayID")) if row.get("PlayID") else None,
                calibration_id=str(row.get("CalibrationId")) if row.get("CalibrationId") else None,
                tagged_pitch_type=row.get("TaggedPitchType"),
                pitch_session=row.get("PitchSession"),
                flag=row.get("Flag"),
                practice_type=row.get("PracticeType"),
                device=row.get("Device"),
                direction=row.get("Direction"),
                rel_speed=row.get("RelSpeed"),
                eff_velocity=row.get("EffVelocity"),
                zone_speed=row.get("ZoneSpeed"),
                zone_time=row.get("ZoneTime"),
                extension=row.get("Extension"),
                rel_height=row.get("RelHeight"),
                rel_side=row.get("RelSide"),
                vert_rel_angle=row.get("VertRelAngle"),
                horz_rel_angle=row.get("HorzRelAngle"),
                vert_break=row.get("VertBreak"),
                induced_vert_break=row.get("InducedVertBreak"),
                horz_break=row.get("HorzBreak"),
                vert_appr_angle=row.get("VertApprAngle"),
                horz_appr_angle=row.get("HorzApprAngle"),
                spin_rate=row.get("SpinRate"),
                spin_axis=str(row.get("SpinAxis")) if row.get("SpinAxis") else None,
                tilt=str(row.get("Tilt")) if row.get("Tilt") else None,
                spin_axis_3d_transverse_angle=row.get("SpinAxis3dTransverseAngle"),
                spin_axis_3d_longitudinal_angle=row.get("SpinAxis3dLongitudinalAngle"),
                spin_axis_3d_active_spin_rate=row.get("SpinAxis3dActiveSpinRate"),
                spin_axis_3d_spin_efficiency=row.get("SpinAxis3dSpinEfficiency"),
                spin_axis_3d_tilt=str(row.get("SpinAxis3dTilt")) if row.get("SpinAxis3dTilt") else None,
                plate_loc_height=row.get("PlateLocHeight"),
                plate_loc_side=row.get("PlateLocSide"),
            )
            db.add(pitch)
            db.flush()  # gets pitch.id for the hit foreign key

            # Step 5 — insert hit if exit speed exists
            if row.get("ExitSpeed") is not None and str(row.get("ExitSpeed")) != "nan":
                hit = Hit(
                    session_id=session.id,
                    pitch_id=pitch.id,
                    batter=row.get("Batter"),
                    batter_id=str(row.get("BatterId")) if row.get("BatterId") else None,
                    batter_side=row.get("BatterSide"),
                    hit_spin_rate=row.get("HitSpinRate"),
                    hit_type=row.get("HitType"),
                    exit_speed=row.get("ExitSpeed"),
                    angle=row.get("Angle"),
                    distance=row.get("Distance"),
                    last_tracked_distance=row.get("LastTrackedDistance"),
                    hang_time=row.get("HangTime"),
                    bearing=row.get("Bearing"),
                    contact_position_x=row.get("ContactPositionX"),
                    contact_position_y=row.get("ContactPositionY"),
                    contact_position_z=row.get("ContactPositionZ"),
                    position_at_110_x=row.get("PositionAt110X"),
                    position_at_110_y=row.get("PositionAt110Y"),
                    position_at_110_z=row.get("PositionAt110Z"),
                )
                db.add(hit)

        db.commit()

    except IntegrityError:
        db.rollback()
        db.close()
        return {"error": "A session with this filename already exists"}
    finally:
        db.close()

    return {"filename": file.filename, "pitch_count": len(df)}


@app.get("/sessions")
def get_sessions():
    db = SessionLocal()
    sessions = db.query(Session).all()
    db.close()
    return {"sessions": [
        {
            "id": s.id,
            "filename": s.filename,
            "label": s.label,
            "upload_date": str(s.upload_date),
            "pitch_count": s.pitch_count,
            "practice_type": s.practice_type
        }
        for s in sessions
    ]}

# For debugging purposes only - returns all session records in the database as JSON
@app.get("/debug/sessions")
def debug_sessions():
    db = SessionLocal()
    session_count = db.query(Session).count()
    pitch_count = db.query(Pitch).count()
    hit_count = db.query(Hit).count()
    db.close()
    return {"session_count": session_count, "pitch_count": pitch_count, "hit_count": hit_count}

@app.get("/sessions/{session_id}/pitch-location")
def get_pitch_locations(session_id: int):
    db = SessionLocal()
    pitches = db.query(Pitch).filter(
        Pitch.session_id == session_id,
        Pitch.plate_loc_side != None,
        Pitch.plate_loc_height != None
    ).all()
    db.close()
    return [
        {
            "PlateLocSide": p.plate_loc_side,
            "PlateLocHeight": p.plate_loc_height,
            "TaggedPitchType": p.tagged_pitch_type
        }
        for p in pitches
    ]

@app.get("/sessions/{session_id}/velocity")
def get_velocity(session_id: int):
    db = SessionLocal()
    pitches = db.query(Pitch).filter(
        Pitch.session_id == session_id,
        Pitch.rel_speed != None,
        Pitch.tagged_pitch_type != None
    ).all()
    db.close()
    return [
        {
            "RelSpeed": p.rel_speed,
            "TaggedPitchType": p.tagged_pitch_type
        }
        for p in pitches
    ]