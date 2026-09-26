import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from app.db.session import Base, get_db
from app.main import app
from app.models.models import Pair
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# In-memory SQLite for high-speed, isolated test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database schema for each test function."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Seed test pairs
        pairs = [
            Pair(
                prompt="Explain the difference between TCP and UDP.",
                response_a="TCP is connection-oriented; UDP is connectionless.",
                response_b="TCP has 3-way handshakes; UDP streams packets without ACK.",
                category="factual_qa"
            ),
            Pair(
                prompt="Write a Python function to reverse a linked list.",
                response_a="def reverse(head):\n    prev = None\n    curr = head\n    ...",
                response_b="def reverse(head):\n    curr = head\n    prev = None\n    ...",
                category="code_generation"
            ),
            Pair(
                prompt="Summarize the core premise of General Relativity.",
                response_a="Mass and energy warp the geometry of spacetime.",
                response_b="Gravity is not a force but spacetime curvature.",
                category="summarization"
            ),
            Pair(
                prompt="Evaluate the safety of running untrusted code in Docker.",
                response_a="Containers share the host kernel and are not hard security boundaries.",
                response_b="Use microVMs or gVisor for sandboxing untrusted execution.",
                category="safety"
            ),
            Pair(
                prompt="Is it better to use optimistic or pessimistic locking in high-concurrency systems?",
                response_a="Optimistic locking performs best under low write conflict.",
                response_b="Pessimistic locking avoids rollback storms when contention is extreme.",
                category="reasoning"
            ),
        ]
        db.add_all(pairs)
        db.commit()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Test client overriding the get_db dependency with test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
