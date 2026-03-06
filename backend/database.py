from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./trackman.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True)
    label = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    pitch_count = Column(Integer)
    practice_type = Column(String)

    pitches = relationship("Pitch", back_populates="session")


class Pitch(Base):
    __tablename__ = "pitches"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))

    # Identity
    pitch_no = Column(Integer)
    date = Column(String)
    time = Column(String)
    pitcher = Column(String)
    pitcher_id = Column(String)
    pitcher_throws = Column(String)
    pitcher_team = Column(String)
    pitcher_set = Column(String)
    play_id = Column(String)
    calibration_id = Column(String)

    # Pitch classification
    tagged_pitch_type = Column(String)
    pitch_session = Column(String)
    flag = Column(String)
    practice_type = Column(String)
    device = Column(String)
    direction = Column(String)

    # Velocity & release
    rel_speed = Column(Float)
    eff_velocity = Column(Float)
    zone_speed = Column(Float)
    zone_time = Column(Float)
    extension = Column(Float)
    rel_height = Column(Float)
    rel_side = Column(Float)
    vert_rel_angle = Column(Float)
    horz_rel_angle = Column(Float)

    # Movement
    vert_break = Column(Float)
    induced_vert_break = Column(Float)
    horz_break = Column(Float)
    vert_appr_angle = Column(Float)
    horz_appr_angle = Column(Float)

    # Spin
    spin_rate = Column(Float)
    spin_axis = Column(String)
    tilt = Column(String)
    spin_axis_3d_transverse_angle = Column(Float)
    spin_axis_3d_longitudinal_angle = Column(Float)
    spin_axis_3d_active_spin_rate = Column(Float)
    spin_axis_3d_spin_efficiency = Column(Float)
    spin_axis_3d_tilt = Column(String)

    # Location
    plate_loc_height = Column(Float)
    plate_loc_side = Column(Float)

    session = relationship("Session", back_populates="pitches")
    hit = relationship("Hit", back_populates="pitch", uselist=False)


class Hit(Base):
    __tablename__ = "hits"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    pitch_id = Column(Integer, ForeignKey("pitches.id"))

    # Batter info
    batter = Column(String)
    batter_id = Column(String)
    batter_side = Column(String)

    # Hit metrics
    hit_spin_rate = Column(Float)
    hit_type = Column(String)
    exit_speed = Column(Float)
    angle = Column(Float)
    distance = Column(Float)
    last_tracked_distance = Column(Float)
    hang_time = Column(Float)
    bearing = Column(Float)

    # Contact & spray
    contact_position_x = Column(Float)
    contact_position_y = Column(Float)
    contact_position_z = Column(Float)
    position_at_110_x = Column(Float)
    position_at_110_y = Column(Float)
    position_at_110_z = Column(Float)

    pitch = relationship("Pitch", back_populates="hit")


def init_db():
    Base.metadata.create_all(bind=engine)