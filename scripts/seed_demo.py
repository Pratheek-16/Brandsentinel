import os
from sqlalchemy.orm import Session
from ..db import models, session
from ..core.config import settings

def seed_demo_data(db: Session):
    if not settings.seed_demo:
        return
    brands = ["novafit", "lumenbank", "asteruniversity"]
    for brand in brands:
        ws_name = brand.title().replace(" ", "")
        workspace = models.Workspace(name=ws_name)
        db.add(workspace)
        db.flush()  # get id
        # create demo users
        users = [
            (f"admin@{brand}.local", "admin"),
            (f"manager@{brand}.local", "manager"),
            (f"reviewer@{brand}.local", "reviewer"),
            (f"creator1@{brand}.local", "creator"),
            (f"creator2@{brand}.local", "creator"),
        ]
        for email, role in users:
            pwd_hash = "$2b$12$examplehashplaceholder"  # placeholder; real hash not needed for demo
            user = models.User(
                workspace_id=workspace.id,
                email=email,
                name=email.split("@")[0],
                role=role,
                password_hash=pwd_hash,
                active=True,
            )
            db.add(user)
    db.commit()

if __name__ == "__main__":
    db = session.SessionLocal()
    seed_demo_data(db)
    db.close()
