from datetime import datetime, timezone
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..database import get_db
from ..schemas import Observation, ObservationCreate

router = APIRouter(prefix="/observations", tags=["observations"])


def _row_to_observation(row: sqlite3.Row) -> Observation:
    return Observation(
        id=row["id"],
        created_at=datetime.fromisoformat(row["created_at"]),
        location=row["location"],
        category=row["category"],
        severity=row["severity"],
        description=row["description"],
    )


@router.post("", response_model=Observation, status_code=status.HTTP_201_CREATED)
def create_observation(
    payload: ObservationCreate,
    connection: sqlite3.Connection = Depends(get_db),
) -> Observation:
    created_at = datetime.now(timezone.utc).isoformat()
    try:
        cursor = connection.execute(
            """
            INSERT INTO observations (created_at, location, category, severity, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (created_at, payload.location, payload.category, payload.severity, payload.description),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM observations WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    except sqlite3.Error as exc:
        connection.rollback()
        raise HTTPException(status_code=500, detail="Unable to save observation") from exc

    if row is None:
        raise HTTPException(status_code=500, detail="Observation was not created")
    return _row_to_observation(row)


@router.get("", response_model=list[Observation])
def list_observations(
    location: str | None = Query(default=None, min_length=1, max_length=200),
    category: str | None = Query(default=None, min_length=1, max_length=100),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    connection: sqlite3.Connection = Depends(get_db),
) -> list[Observation]:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    conditions: list[str] = []
    parameters: list[str] = []
    if location:
        conditions.append("location = ?")
        parameters.append(location.strip())
    if category:
        conditions.append("category = ?")
        parameters.append(category.strip())
    if start_date:
        conditions.append("created_at >= ?")
        parameters.append(start_date.isoformat())
    if end_date:
        conditions.append("created_at <= ?")
        parameters.append(end_date.isoformat())

    query = "SELECT * FROM observations"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY created_at DESC"
    try:
        rows = connection.execute(query, parameters).fetchall()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="Unable to retrieve observations") from exc
    return [_row_to_observation(row) for row in rows]
