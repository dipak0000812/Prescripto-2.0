"""
Prescripto AI 2.0 — CLI User Creation Script.
Seeds or creates an initial user (OPERATOR, REVIEWER, or ADMIN) with bcrypt-hashed credentials.
"""
import argparse
import sys
import uuid

from prescripto.db.session import SessionLocal
from prescripto.db.models.users import User
from prescripto.auth.crypto import hash_password
from prescripto.audit.logger import configure_logging, get_logger

configure_logging("INFO")
logger = get_logger("prescripto.scripts.create_user")


def create_or_update_user(
    username: str,
    email: str,
    password: str,
    role: str = "OPERATOR",
    is_active: bool = True,
) -> User:
    role_upper = role.upper()
    if role_upper not in {"OPERATOR", "REVIEWER", "ADMIN"}:
        raise ValueError(f"Invalid role: {role}. Must be one of OPERATOR, REVIEWER, ADMIN.")

    db = SessionLocal()
    try:
        user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        hashed = hash_password(password)

        if user:
            user.username = username
            user.email = email
            user.hashed_password = hashed
            user.role = role_upper
            user.is_active = is_active
            db.commit()
            db.refresh(user)
            logger.info("user_updated", actor_id=str(user.id), status="UPDATED")
            return user

        user = User(
            id=uuid.uuid4(),
            username=username,
            email=email,
            hashed_password=hashed,
            role=role_upper,
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("user_created", actor_id=str(user.id), status="CREATED")
        return user
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update a Prescripto user.")
    parser.add_argument("--username", required=True, help="Username for authentication")
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--password", required=True, help="Plaintext password to hash")
    parser.add_argument(
        "--role",
        default="OPERATOR",
        choices=["OPERATOR", "REVIEWER", "ADMIN"],
        help="RBAC role assigned to the user",
    )
    parser.add_argument(
        "--inactive",
        action="store_true",
        help="Flag to create user in inactive state",
    )

    args = parser.parse_args()
    try:
        user = create_or_update_user(
            username=args.username,
            email=args.email,
            password=args.password,
            role=args.role,
            is_active=not args.inactive,
        )
        print(f"Success: User '{user.username}' ({user.role}) ready with id={user.id}")
    except Exception as exc:
        logger.error("user_creation_failed", error_type=type(exc).__name__)
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
