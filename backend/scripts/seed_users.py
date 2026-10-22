"""
Seed Default Users (Operator, Reviewer, Admin) and Active Model Version.
Idempotent: skips already existing users.
"""
import uuid
from prescripto.db.session import SessionLocal
from prescripto.db.models.users import User
from prescripto.db.models.enums import Role
from prescripto.db.models.registry import ModelVersion
from prescripto.auth.crypto import hash_password
from prescripto.config.settings import settings


def seed_users():
    db = SessionLocal()
    try:
        users_to_seed = [
            {
                "username": "test_operator",
                "email": "operator@prescripto.local",
                "password": "OperatorPass123!",
                "role": Role.OPERATOR.value,
            },
            {
                "username": "test_reviewer",
                "email": "reviewer@prescripto.local",
                "password": "ReviewerPass123!",
                "role": Role.REVIEWER.value,
            },
            {
                "username": "test_admin",
                "email": "admin@prescripto.local",
                "password": "AdminPass123!",
                "role": Role.ADMIN.value,
            },
            {
                "username": "doctor_sharma",
                "email": "doctor.sharma@prescripto.local",
                "password": "DoctorPass123!",
                "role": Role.REVIEWER.value,
            },
            {
                "username": "doctor",
                "email": "doctor@prescripto.local",
                "password": "DoctorPass123!",
                "role": Role.REVIEWER.value,
            },
        ]

        created_count = 0
        for u_data in users_to_seed:
            existing = db.query(User).filter(User.username == u_data["username"]).first()
            if not existing:
                user = User(
                    id=uuid.uuid4(),
                    username=u_data["username"],
                    email=u_data["email"],
                    hashed_password=hash_password(u_data["password"]),
                    role=u_data["role"],
                    is_active=True,
                )
                db.add(user)
                created_count += 1

        # Seed model version if missing
        existing_model = db.query(ModelVersion).filter(
            ModelVersion.model_name == settings.OCR_MODEL_NAME,
            ModelVersion.model_version == settings.OCR_MODEL_VERSION,
        ).first()

        if not existing_model:
            model = ModelVersion(
                id=uuid.uuid4(),
                model_name=settings.OCR_MODEL_NAME,
                model_version=settings.OCR_MODEL_VERSION,
                checkpoint_sha256="0" * 64,
                artifact_storage_key=f"models/{settings.OCR_MODEL_NAME}/{settings.OCR_MODEL_VERSION}/model.onnx",
                framework="PyTorch",
                license="Apache-2.0",
            )
            db.add(model)

        db.commit()
        print(f"Successfully seeded {created_count} users and active model version.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()
