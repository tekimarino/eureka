import click
from app import create_app
from app.extensions import db
from app.models import User
from passlib.hash import bcrypt

app = create_app()

@app.cli.command("create-admin")
@click.option("--username", required=True)
@click.option("--phone", required=True)
@click.option("--password", required=True)
def create_admin(username: str, phone: str, password: str):
    """Crée un compte admin (si absent)."""
    with app.app_context():
        existing = User.query.filter_by(username=username).first()
        if existing:
            click.echo(f"User '{username}' existe déjà.")
            return
        u = User(
            username=username,
            phone=phone,
            role="admin",
            is_active=True,
            password_hash=bcrypt.hash(password),
        )
        db.session.add(u)
        db.session.commit()
        click.echo("Admin créé.")
