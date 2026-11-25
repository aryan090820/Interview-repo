import logging
import re
import sqlite3

from sqlalchemy import Engine, text

from core.config import get_settings
from core.exceptions import QueryFailedError
from db.session import engine as db_engine
from services.embeddings import HashingEmbedder, VectorIndex

logger = logging.getLogger(__name__)

TRAINING_EXAMPLES = [
    {
        "question": "how many cardiology appointments are booked",
        "sql": "SELECT COUNT(*) AS total FROM appointments WHERE department = 'cardiology' AND status = 'booked'",
    },
    {
        "question": "list every registered patient with their phone number",
        "sql": "SELECT id, full_name, phone FROM patients ORDER BY full_name",
    },
    {
        "question": "upcoming appointments scheduled from today onwards",
        "sql": "SELECT id, department, slot_date, slot_time FROM appointments WHERE status = 'booked' AND appointment_date >= DATE('now') ORDER BY slot_date, slot_time",
    },
    {
        "question": "which departments have the most appointments",
        "sql": "SELECT department, COUNT(*) AS total FROM appointments GROUP BY department ORDER BY total DESC",
    },
    {
        "question": "how many reminder notifications are still unread",
        "sql": "SELECT COUNT(*) AS unread FROM notifications WHERE read_at IS NULL",
    },
    {
        "question": "cancelled appointments grouped by patient",
        "sql": "SELECT patient_id, COUNT(*) AS cancelled FROM appointments WHERE status = 'cancelled' GROUP BY patient_id",
    },
]

COLUMN_ALIASES = {
    "appointment_date": "slot_date",
    "appointment_time": "slot_time",
    "name": "full_name",
    "dept": "department",
}

SMOKE_QUESTION = "show upcoming appointments from today"
MISSING_COLUMN = re.compile(r"no such column: (\w+)")


class QueryEngine:
    def __init__(self, embedder: HashingEmbedder, index: VectorIndex, engine: Engine, max_retries: int):
        self.embedder = embedder
        self.index = index
        self.engine = engine
        self.max_retries = max_retries

    def train(self, examples: list[dict]) -> None:
        vectors = self.embedder.embed_batch([example["question"] for example in examples])
        self.index.add(vectors, examples)
        logger.info("Query engine trained on %d examples", len(self.index))

    def generate_sql(self, question: str) -> str:
        score, example = self.index.search(self.embedder.embed(question), k=1)[0]
        logger.debug("Matched %r with score %.3f", example["question"], score)
        return example["sql"]

    def _repair(self, sql: str, error: str) -> str | None:
        match = MISSING_COLUMN.search(error)
        if match and match.group(1) in COLUMN_ALIASES:
            return re.sub(rf"\b{match.group(1)}\b", COLUMN_ALIASES[match.group(1)], sql)
        return None

    def ask(self, question: str) -> dict:
        sql = self.generate_sql(question)
        for attempt in range(1, self.max_retries + 2):
            if not sql.lstrip().upper().startswith("SELECT"):
                raise QueryFailedError("Only read-only queries are allowed")
            try:
                with self.engine.connect() as connection:
                    rows = [dict(row._mapping) for row in connection.execute(text(sql))]
                return {"question": question, "sql": sql, "attempts": attempt, "rows": rows}
            except sqlite3.OperationalError as exc:
                logger.warning("Query attempt %d failed: %s", attempt, exc)
                repaired = self._repair(sql, str(exc))
                if repaired is None:
                    break
                sql = repaired
        raise QueryFailedError(f"Could not answer question: {question}")

    def self_check(self) -> None:
        for example in self.index._payloads:
            if self.generate_sql(example["question"]) != example["sql"]:
                raise RuntimeError(f"Retrieval self-check failed for: {example['question']}")
        self.ask(SMOKE_QUESTION)
        logger.info("Query engine self-check passed")


def build_query_engine() -> QueryEngine:
    settings = get_settings()
    query_engine = QueryEngine(
        embedder=HashingEmbedder(),
        index=VectorIndex(dim=settings.embedding_dim),
        engine=db_engine,
        max_retries=settings.max_query_retries,
    )
    query_engine.train(TRAINING_EXAMPLES)
    return query_engine
