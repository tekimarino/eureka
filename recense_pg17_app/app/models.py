from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from .extensions import db

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False, default="agent")  # admin/superviseur/agent
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

class Zone(db.Model):
    __tablename__ = "zones"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    objective = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

class Center(db.Model):
    __tablename__ = "centers"
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)
    code = db.Column(db.String(30), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

class Record(db.Model):
    __tablename__ = "records"
    id = db.Column(db.BigInteger, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    center_id = db.Column(db.Integer, db.ForeignKey("centers.id", ondelete="SET NULL"), nullable=True)
    agent_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending/approved/rejected
    payload = db.Column(JSONB, nullable=False, default=dict)  # infos électeur
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class KVStore(db.Model):
    __tablename__ = "kv_store"
    k = db.Column(db.Text, primary_key=True)
    v = db.Column(JSONB, nullable=False, default=dict)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
