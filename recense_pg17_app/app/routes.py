from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from passlib.hash import bcrypt
from sqlalchemy import func

from .extensions import db
from .models import User, Zone, Center, Record

bp = Blueprint("api", __name__)

@bp.get("/health")
def health():
    return jsonify({"ok": True})

# AUTH
@bp.post("/auth/login")
def login():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    u = User.query.filter_by(username=username).first()
    if not u or not u.is_active or not bcrypt.verify(password, u.password_hash):
        return jsonify({"error": "Identifiants invalides"}), 401

    token = create_access_token(identity={"id": u.id, "role": u.role, "username": u.username})
    return jsonify({"access_token": token})

@bp.get("/auth/me")
@jwt_required()
def me():
    return jsonify(get_jwt_identity())

# USERS
@bp.get("/users")
@jwt_required()
def list_users():
    users = User.query.order_by(User.id.desc()).all()
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "phone": u.phone,
        "role": u.role,
        "is_active": u.is_active,
    } for u in users])

@bp.post("/users")
@jwt_required()
def create_user():
    ident = get_jwt_identity()
    if ident.get("role") != "admin":
        return jsonify({"error": "admin only"}), 403

    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    phone = (data.get("phone") or "").strip()
    role = (data.get("role") or "agent").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "username/password requis"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username existe déjà"}), 409

    u = User(username=username, phone=phone, role=role, is_active=True, password_hash=bcrypt.hash(password))
    db.session.add(u)
    db.session.commit()
    return jsonify({"id": u.id}), 201

@bp.patch("/users/<int:user_id>/deactivate")
@jwt_required()
def deactivate_user(user_id: int):
    ident = get_jwt_identity()
    if ident.get("role") != "admin":
        return jsonify({"error": "admin only"}), 403

    u = User.query.get_or_404(user_id)
    u.is_active = False
    db.session.commit()
    return jsonify({"ok": True})

# ZONES / CENTERS
@bp.get("/zones")
@jwt_required()
def list_zones():
    zones = Zone.query.order_by(Zone.name.asc()).all()
    return jsonify([{"id": z.id, "name": z.name, "objective": z.objective} for z in zones])

@bp.post("/zones")
@jwt_required()
def create_zone():
    ident = get_jwt_identity()
    if ident.get("role") != "admin":
        return jsonify({"error": "admin only"}), 403
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    objective = data.get("objective")
    if not name:
        return jsonify({"error": "name requis"}), 400
    z = Zone(name=name, objective=objective)
    db.session.add(z)
    db.session.commit()
    return jsonify({"id": z.id}), 201

@bp.post("/centers")
@jwt_required()
def create_center():
    ident = get_jwt_identity()
    if ident.get("role") != "admin":
        return jsonify({"error": "admin only"}), 403
    data = request.get_json(force=True)
    zone_id = data.get("zone_id")
    name = (data.get("name") or "").strip()
    code = (data.get("code") or "").strip()
    if not zone_id or not name:
        return jsonify({"error": "zone_id/name requis"}), 400
    c = Center(zone_id=zone_id, name=name, code=code)
    db.session.add(c)
    db.session.commit()
    return jsonify({"id": c.id}), 201

# RECORDS
@bp.post("/records")
@jwt_required()
def create_record():
    ident = get_jwt_identity()
    data = request.get_json(force=True)
    r = Record(
        zone_id=data.get("zone_id"),
        center_id=data.get("center_id"),
        agent_id=ident.get("id"),
        status="pending",
        payload=data.get("payload") or {},
    )
    db.session.add(r)
    db.session.commit()
    return jsonify({"id": r.id}), 201

@bp.get("/records")
@jwt_required()
def list_records():
    zone_id = request.args.get("zone_id", type=int)
    q = Record.query
    if zone_id:
        q = q.filter(Record.zone_id == zone_id)
    records = q.order_by(Record.updated_at.desc()).limit(200).all()
    return jsonify([{
        "id": r.id,
        "zone_id": r.zone_id,
        "center_id": r.center_id,
        "agent_id": r.agent_id,
        "supervisor_id": r.supervisor_id,
        "status": r.status,
        "payload": r.payload,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    } for r in records])

@bp.post("/records/<int:record_id>/approve")
@jwt_required()
def approve_record(record_id: int):
    ident = get_jwt_identity()
    if ident.get("role") not in ("admin", "superviseur"):
        return jsonify({"error": "superviseur/admin only"}), 403

    r = Record.query.get_or_404(record_id)
    r.status = "approved"
    r.supervisor_id = ident.get("id")
    db.session.commit()
    return jsonify({"ok": True})

@bp.get("/stats/zone/<int:zone_id>")
@jwt_required()
def stats_zone(zone_id: int):
    total = db.session.query(func.count(Record.id)).filter(Record.zone_id == zone_id).scalar() or 0
    approved = db.session.query(func.count(Record.id)).filter(Record.zone_id == zone_id, Record.status == "approved").scalar() or 0
    z = Zone.query.get(zone_id)
    objective = z.objective if z else None
    progression = (approved / objective) if objective else None
    return jsonify({"total": total, "approved": approved, "objective": objective, "progression": progression})
