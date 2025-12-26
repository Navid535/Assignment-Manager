import sqlite3
import datetime
from typing import Optional, List, Dict, Any

_JALALI_AVAILABLE = False
try:
    from persiantools.jdatetime import JalaliDate

    _JALALI_BACKEND = "persiantools"
    _JALALI_AVAILABLE = True
except Exception:
    try:
        import jdatetime

        _JALALI_BACKEND = "jdatetime"
        _JALALI_AVAILABLE = True
    except Exception:
        _JALALI_BACKEND = None
        _JALALI_AVAILABLE = False


class AssignmentError(Exception):
    pass


class DuplicateNameError(AssignmentError):
    pass


class InvalidDateError(AssignmentError):
    pass


def _jalali_to_gregorian(jalali_date: str) -> str:
    if not _JALALI_AVAILABLE:
        raise InvalidDateError(
            "Jalali date is not available"
            "Install 'persiantools' or 'jdatetime' to accept Jalali dates"
            "persiantools is more recommended"
        )
    parts = jalali_date.split("-")
    if len(parts) != 3:
        raise InvalidDateError(f"Invalid Jalali date format: {jalali_date!r}")
    year, month, day = map(int, parts)
    if _JALALI_BACKEND == "persiantools":
        g = JalaliDate(year, month, day).to_gregorian()
        return g.strftime("%Y-%m-%d")
    else:
        g = jdatetime.date(year, month, day).to_gregorian()
        return g.strftime("%Y-%m-%d")


def _gregorian_to_jalali(iso_date_str: str) -> str:
    y, m, d = map(int, iso_date_str.split("-"))
    if _JALALI_BACKEND == "persiantools":
        j = JalaliDate.to_jalali(datetime.date(y, m, d))
        return j.strftime("%Y-%m-%d")
    elif _JALALI_BACKEND == "jdatetime":
        j = jdatetime.date.fromgregorian(year=y, month=m, day=d)
        return j.strftime("%Y-%m-%d")
    else:
        raise InvalidDateError(
            "Cannot convert Gregorian to Jalali because no jalali backend is installed."
        )


def _normalizing_deadline(deadline: str) -> str:
    if not isinstance(deadline, str):
        raise InvalidDateError(
            "Deadline must be a string in YYYY-MM-DD format or jalali '1400-01-01' format"
        )
    deadline = deadline.strip()
    if deadline.count("-") == 2 and deadline.startswith("14"):
        return _jalali_to_gregorian(deadline)
    try:
        datetime.datetime.strptime(deadline, "%Y-%m-%d")
        return deadline
    except ValueError:
        raise InvalidDateError(
            f"deadline not in ISO format 'YYYY-MM-DD'\n: {deadline!r}'"
        )


class AssignmentManager:
    def __init__(self, db_path: str = "assignments.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.ensure_schema()

    def ensure_schema(self):
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS assignments (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL UNIQUE,
                            deadline TEXT NOT NULL,
                            stars INTEGER DEFAULT 0)
        """
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_deadline ON assignments(deadline)"
        )
        self.conn.commit()

    def close(self):
        try:
            self.conn.commit()
        finally:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def add(self, name: str, deadline: str, stars: int = 0) -> int:
        name = name.strip()
        if not name:
            raise ValueError("Name cannot be empty")

        dl_iso = _normalizing_deadline(deadline)
        stars = int(stars) if stars is not None else 0
        try:
            self.cursor.execute(
                "INSERT INTO assignments (name, deadline, stars) VALUES (?, ?, ?)",
                (name, dl_iso, stars),
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e).upper():
                raise DuplicateNameError(
                    f"An assignment with name '{name!r}' already exists."
                ) from e
            raise

    def get_by_id(self, id_: int) -> Optional[Dict[str, any]]:
        r = self.cursor.execute(
            "SELECT * FROM assignments WHERE id = ?", (id_,)
        ).fetchone()
        return self._row_to_dict(r) if r else None

    def get_all(self, ob: str = "deadline", asc: bool = True) -> List[Dict[str, any]]:
        assert ob in ("deadline", "stars", "name", "id"), "unsupported order_by value"
        asc_desc = "ASC" if asc else "DESC"
        rows = self.cursor.execute(
            f"SELECT * FROM assignments ORDER BY {ob} {asc_desc}"
        ).fetchall()

        return [self._row_to_dict(r) for r in rows]

    def search(self, qry: str) -> List[Dict[str, any]]:
        pattern = f"%{qry.strip()}%"
        rows = self.cursor.execute(
            "SELECT * FROM assignments WHERE name LIKE ? ORDER BY deadline ASC",
            (pattern,),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def update_by_id(
        self,
        id_: int,
        name: Optional[str] = None,
        deadline: Optional[str] = None,
        stars: Optional[int] = None,
    ) -> bool:
        fields = []
        params = []
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("Name cannot be empty")
            fields.append("name = ?")
            params.append(name)
        if deadline is not None:
            deadline = _normalizing_deadline(deadline)
            fields.append("deadline = ?")
            params.append(deadline)
        if stars is not None:
            fields.append("stars = ?")
            params.append(int(stars))
        if not fields:
            return False
        params.append(id_)
        sql = f"UPDATE assignments SET {', '.join(fields)} WHERE id = ?"
        try:
            self.cursor.execute(sql, tuple(params))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e).upper():
                raise DuplicateNameError("Name conflict during update.") from e
            raise

    def delete_by_id(self, id_: int) -> bool:
        self.cursor.execute("DELETE FROM assignments WHERE id = ?", (id_,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def count(self) -> int:
        return int(
            self.cursor.execute("SELECT COUNT(*) FROM assignments").fetchone()[0]
        )

    def get_upcoming(self, days: int = 7) -> List[Dict[str, Any]]:
        today = datetime.date.today()
        limit = today + datetime.timedelta(days=days)
        rows = self.cursor.execute(
            "SELECT * FROM assignments WHERE deadline BETWEEN ? AND ? ORDER BY deadline ASC",
            (today.strftime("%Y-%m-%d"), limit.strftime("%Y-%m-%d")),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    @staticmethod
    def days_remaining_from_iso(iso_date_str: str) -> int:
        d = datetime.datetime.strptime(iso_date_str, "%Y-%m-%d").date()
        return (d - datetime.date.today()).days

    def _row_to_dict(self, r):
        d = dict(r)
        try:
            d["deadline_jalali"] = _gregorian_to_jalali(d["deadline"])
        except InvalidDateError:
            d["deadline_jalali"] = None
        return d
