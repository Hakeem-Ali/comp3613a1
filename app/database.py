import logging
import threading
import time
from contextlib import contextmanager

from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError
from sqlmodel import SQLModel, Session, create_engine, select

from app.config import get_settings
from app.models.rewards import Award, Milestone
from app.repositories.user import UserRepository
from app.schemas.user import AdminCreate, RegularUserCreate
from app.utilities.security import encrypt_password

logger = logging.getLogger(__name__)

_schema_lock = threading.Lock()


def sqlalchemy_uri(uri: str) -> str:
    """Accept Render's postgres:// URLs in the sync SQLAlchemy engine."""
    if uri.startswith("postgres://"):
        return "postgresql+psycopg2://" + uri[len("postgres://") :]
    if uri.startswith("postgresql://"):
        return "postgresql+psycopg2://" + uri[len("postgresql://") :]
    return uri


engine = create_engine(
    sqlalchemy_uri(get_settings().database_uri),
    echo=get_settings().env.lower()
    in ["dev", "development", "test", "testing", "staging"],
    pool_size=get_settings().db_pool_size,
    max_overflow=get_settings().db_additional_overflow,
    pool_timeout=get_settings().db_pool_timeout,
    pool_recycle=get_settings().db_pool_recycle,
)


def create_db_and_tables() -> None:
    # Ensure model modules are imported so tables are registered on metadata.
    import app.models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def drop_all() -> None:
    SQLModel.metadata.drop_all(bind=engine)


def is_db_not_ready_error(exc: BaseException) -> bool:
    """True when Postgres is unreachable or the schema/tables are missing."""
    if isinstance(exc, OperationalError):
        return True
    if isinstance(exc, ProgrammingError):
        return True
    if isinstance(exc, DBAPIError) and getattr(exc, "connection_invalidated", False):
        return True

    text = str(exc).lower()
    markers = (
        "does not exist",
        "undefinedtable",
        "undefined table",
        "no such table",
        "relation ",
        "could not connect",
        "connection refused",
        "connection timed out",
        "server closed the connection",
        "the database system is starting up",
        "remaining connection slots",
        "too many connections",
        "ssl connection has been closed",
    )
    return any(m in text for m in markers)


def ensure_db_and_tables(
    *,
    retries: int = 8,
    delay_seconds: float = 2.0,
) -> None:
    """Create tables, retrying while the prod DB is still coming up."""
    last: BaseException | None = None
    for attempt in range(1, retries + 1):
        try:
            with _schema_lock:
                create_db_and_tables()
            if attempt > 1:
                logger.info("Database schema ready after %s attempt(s)", attempt)
            return
        except Exception as exc:  # noqa: BLE001 — first-boot resilience
            last = exc
            if not is_db_not_ready_error(exc) or attempt >= retries:
                raise
            logger.warning(
                "Database not ready (attempt %s/%s): %s",
                attempt,
                retries,
                exc,
            )
            time.sleep(delay_seconds * attempt)
    if last is not None:
        raise last


def seed_demo_data() -> None:
    """Ensure the Campus Rewards demo users and award metadata exist."""
    with Session(engine) as session:
        repo = UserRepository(session)
        demo_users = [
            ("bob", "bob@example.com", "bobpass", "regular_user"),
            ("admin", "admin@example.com", "adminpass", "admin"),
        ]
        for username, email, password, role in demo_users:
            if repo.get_by_username(username) is None:
                payload_cls = AdminCreate if role == "admin" else RegularUserCreate
                repo.create(payload_cls(username=username, email=email, password=encrypt_password(password), role=role))

        milestone_seed = [
            ("Bronze Contributor", 10, "First volunteer milestone", "milestone"),
            ("Silver Contributor", 40, "Steady campus impact", "milestone"),
            ("Gold Contributor", 80, "Major campus contribution", "trophy"),
            ("Platinum Contributor", 120, "Top campus volunteer", "workspace_premium"),
        ]
        for index, (name, required_hours, description, icon) in enumerate(milestone_seed, start=1):
            existing = session.exec(select(Milestone).where(Milestone.name == name)).one_or_none()
            if existing is None:
                session.add(
                    Milestone(
                        name=name,
                        required_hours=required_hours,
                        description=description,
                        badge_icon=icon,
                        display_order=index,
                    )
                )

        award_seed = [
            ("Wireless Headphones", 75, "Perfect for study sessions and campus life.", "headphones", True),
            ("Gift Card", 50, "Flexible rewards for everyday essentials.", "card_giftcard", True),
            ("Campus T-Shirt", 25, "Show your campus pride.", "checkroom", True),
        ]
        for name, required_hours, description, icon, active in award_seed:
            existing = session.exec(select(Award).where(Award.name == name)).one_or_none()
            if existing is None:
                session.add(
                    Award(
                        name=name,
                        required_hours=required_hours,
                        description=description,
                        icon=icon,
                        active=active,
                    )
                )

        session.commit()


def recover_if_uninitialized(exc: BaseException) -> bool:
    """If *exc* looks like a missing schema, create tables and return True."""
    if not is_db_not_ready_error(exc):
        return False
    logger.warning("Uninitialized database detected; creating tables: %s", exc)
    ensure_db_and_tables()
    return True


def _session_generator():
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()


def get_session():
    yield from _session_generator()


@contextmanager
def get_cli_session():
    yield from _session_generator()
