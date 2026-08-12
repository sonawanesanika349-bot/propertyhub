import os
from typing import Any, Literal, cast, overload

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables from .env locally.
# On Render, these variables are provided through the Environment settings.
load_dotenv()

app = Flask(__name__)

# Production secret key must be provided through the environment.
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY is not configured")


def conn():
    """Create a PostgreSQL connection using DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    return psycopg2.connect(database_url)


@overload
def q(
    sql: str,
    args: tuple[Any, ...] = (),
    one: Literal[True] = False,
    commit: bool = False
) -> dict[str, Any] | None: ...


@overload
def q(
    sql: str,
    args: tuple[Any, ...] = (),
    one: Literal[False] = False,
    commit: bool = False
) -> list[dict[str, Any]]: ...


def q(
    sql: str,
    args: tuple[Any, ...] = (),
    one: bool = False,
    commit: bool = False
):
    """Execute a PostgreSQL query and return dictionary-like results."""
    c = conn()
    cur = c.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(sql, args)

        data = (
            cur.fetchone() if one else cur.fetchall()
        ) if cur.description else None

        if commit:
            c.commit()

        if data is None:
            return None

        if one:
            return cast(dict[str, Any], {
                str(k): v for k, v in data.items()
            })

        return [
            cast(dict[str, Any], {
                str(k): v for k, v in row.items()
            })
            for row in data
        ]

    except Exception:
        if commit:
            c.rollback()
        raise

    finally:
        cur.close()
        c.close()


def setup():
    """
    Optional local database setup.

    This function is kept for local development only.
    The production Supabase database should be initialized
    by running schema.sql in the Supabase SQL Editor.
    """
    with open("schema.sql", encoding="utf-8") as f:
        sql = f.read()

    c = conn()
    cur = c.cursor()

    try:
        cur.execute(sql)
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        cur.close()
        c.close()

    users_result = q("SELECT COUNT(*) AS c FROM users", one=True)

    if not users_result or users_result.get("c", 0) == 0:
        demo = [
            (
                "Admin",
                "admin@propertyhub.com",
                "admin123",
                "admin"
            ),
            (
                "Secretary",
                "secretary@propertyhub.com",
                "secretary123",
                "secretary"
            ),
            (
                "Watchman",
                "watchman@propertyhub.com",
                "watchman123",
                "watchman"
            ),
            (
                "Resident",
                "resident@propertyhub.com",
                "resident123",
                "resident"
            ),
        ]

        for x in demo:
            q(
                """
                INSERT INTO users
                (name, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    x[0],
                    x[1],
                    generate_password_hash(x[2]),
                    x[3]
                ),
                commit=True
            )

    properties_result = q(
        "SELECT COUNT(*) AS c FROM properties",
        one=True
    )

    if not properties_result or properties_result.get("c", 0) == 0:
        properties = [
            (
                "Green Valley 2 BHK",
                "Nashik Road",
                "Apartment",
                15000,
                "Available",
                "2 BHK with parking and security"
            ),
            (
                "Sunrise 3 BHK",
                "Gangapur Road",
                "Apartment",
                22000,
                "Available",
                "Spacious family apartment"
            ),
            (
                "Royal Villa",
                "College Road",
                "Villa",
                35000,
                "Available",
                "Premium villa with garden"
            ),
        ]

        for x in properties:
            q(
                """
                INSERT INTO properties
                (title, location, property_type, rent, status, description)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                x,
                commit=True
            )

    amenities_result = q(
        "SELECT COUNT(*) AS c FROM amenities",
        one=True
    )

    if not amenities_result or amenities_result.get("c", 0) == 0:
        amenities = [
            ("Swimming Pool", "🏊", "Pool booking"),
            ("Gym", "🏋️", "Gym booking"),
            ("Clubhouse", "🎉", "Event booking"),
            ("Community Hall", "🏛️", "Hall booking"),
        ]

        for x in amenities:
            q(
                """
                INSERT INTO amenities
                (name, icon, description)
                VALUES (%s, %s, %s)
                """,
                x,
                commit=True
            )


@app.context_processor
def context():
    try:
        properties = q(
            "SELECT COUNT(*) AS c FROM properties",
            one=True
        )

        available = q(
            "SELECT COUNT(*) AS c FROM properties WHERE status='Available'",
            one=True
        )

        complaints = q(
            "SELECT COUNT(*) AS c FROM complaints WHERE status!='Resolved'",
            one=True
        )

        bookings = q(
            "SELECT COUNT(*) AS c FROM bookings",
            one=True
        )

        return {
            "stats": {
                "properties": properties["c"] if properties else 0,
                "available": available["c"] if available else 0,
                "complaints": complaints["c"] if complaints else 0,
                "bookings": bookings["c"] if bookings else 0,
            }
        }

    except Exception:
        return {
            "stats": {
                "properties": 0,
                "available": 0,
                "complaints": 0,
                "bookings": 0,
            }
        }


@app.route("/")
def home():
    return render_template(
        "index.html",
        properties=q(
            "SELECT * FROM properties ORDER BY id DESC"
        ),
        amenities=q(
            "SELECT * FROM amenities ORDER BY id"
        )
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            q(
                """
                INSERT INTO users
                (name, email, password_hash, role)
                VALUES (%s, %s, %s, 'resident')
                """,
                (
                    request.form["name"],
                    request.form["email"],
                    generate_password_hash(request.form["password"])
                ),
                commit=True
            )

            flash("Registration successful", "success")
            return redirect(url_for("login"))

        except Exception:
            flash("Email already registered or invalid", "danger")

    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = q(
            "SELECT * FROM users WHERE email=%s",
            (request.form["email"],),
            one=True
        )

        if u and check_password_hash(
            u["password_hash"],
            request.form["password"]
        ):
            session.update(
                user_id=u["id"],
                name=u["name"],
                role=u["role"]
            )
            return redirect(url_for("dashboard"))

        flash("Invalid email/password", "danger")

    return render_template("auth.html", mode="login")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    return redirect(url_for(session["role"]))


@app.route("/resident")
def resident():
    if session.get("role") != "resident":
        return redirect(url_for("dashboard"))

    return render_template(
        "resident.html",
        complaints=q(
            """
            SELECT * FROM complaints
            WHERE resident_id=%s
            ORDER BY id DESC
            """,
            (session["user_id"],)
        ),
        bookings=q(
            """
            SELECT b.*, a.name AS amenity
            FROM bookings b
            JOIN amenities a ON a.id=b.amenity_id
            WHERE b.user_id=%s
            ORDER BY b.id DESC
            """,
            (session["user_id"],)
        ),
        properties=q(
            "SELECT * FROM properties ORDER BY id DESC"
        )
    )


@app.route("/secretary")
def secretary():
    if session.get("role") != "secretary":
        return redirect(url_for("dashboard"))

    return render_template(
        "secretary.html",
        properties=q(
            "SELECT * FROM properties ORDER BY id DESC"
        ),
        complaints=q(
            """
            SELECT c.*, u.name AS resident_name
            FROM complaints c
            LEFT JOIN users u ON u.id=c.resident_id
            ORDER BY c.id DESC
            """
        )
    )


@app.route("/watchman")
def watchman():
    if session.get("role") != "watchman":
        return redirect(url_for("dashboard"))

    return render_template(
        "watchman.html",
        visitors=q(
            "SELECT * FROM visitors ORDER BY id DESC"
        )
    )


@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    return render_template(
        "admin.html",
        users=q(
            "SELECT id, name, email, role FROM users ORDER BY id"
        ),
        properties=q(
            "SELECT * FROM properties ORDER BY id DESC"
        ),
        complaints=q(
            """
            SELECT c.*, u.name AS resident_name
            FROM complaints c
            LEFT JOIN users u ON u.id=c.resident_id
            ORDER BY c.id DESC
            """
        )
    )


@app.post("/property/create")
def property_create():
    if session.get("role") not in ("admin", "secretary"):
        return redirect(url_for("dashboard"))

    q(
        """
        INSERT INTO properties
        (title, location, property_type, rent, status, description)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        tuple(
            request.form[x]
            for x in [
                "title",
                "location",
                "property_type",
                "rent",
                "status",
                "description"
            ]
        ),
        commit=True
    )

    return redirect(url_for("dashboard"))


@app.post("/property/<int:pid>/edit")
def property_edit(pid):
    if session.get("role") not in ("admin", "secretary"):
        return redirect(url_for("dashboard"))

    q(
        """
        UPDATE properties
        SET title=%s,
            location=%s,
            property_type=%s,
            rent=%s,
            status=%s,
            description=%s
        WHERE id=%s
        """,
        (
            request.form["title"],
            request.form["location"],
            request.form["property_type"],
            request.form["rent"],
            request.form["status"],
            request.form["description"],
            pid
        ),
        commit=True
    )

    return redirect(url_for("dashboard"))


@app.post("/property/<int:pid>/delete")
def property_delete(pid):
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    q(
        "DELETE FROM properties WHERE id=%s",
        (pid,),
        commit=True
    )

    return redirect(url_for("dashboard"))


@app.post("/complaint/create")
def complaint_create():
    if session.get("role") != "resident":
        return redirect(url_for("dashboard"))

    q(
        """
        INSERT INTO complaints
        (resident_id, title, category, description)
        VALUES (%s, %s, %s, %s)
        """,
        (
            session["user_id"],
            request.form["title"],
            request.form["category"],
            request.form["description"]
        ),
        commit=True
    )

    return redirect(url_for("dashboard"))


@app.post("/complaint/<int:cid>/status")
def complaint_status(cid):
    if session.get("role") not in ("admin", "secretary"):
        return redirect(url_for("dashboard"))

    q(
        """
        UPDATE complaints
        SET status=%s, updated_at=NOW()
        WHERE id=%s
        """,
        (
            request.form["status"],
            cid
        ),
        commit=True
    )

    return redirect(url_for("dashboard"))


@app.post("/booking/create")
def booking_create():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    q(
        """
        INSERT INTO bookings
        (user_id, amenity_id, booking_date, slot)
        VALUES (%s, %s, %s, %s)
        """,
        (
            session["user_id"],
            request.form["amenity_id"],
            request.form["booking_date"],
            request.form["slot"]
        ),
        commit=True
    )

    return redirect(url_for("dashboard"))


@app.post("/booking/<int:bid>/cancel")
def booking_cancel(bid):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    q(
        """
        UPDATE bookings
        SET status='Cancelled'
        WHERE id=%s AND user_id=%s
        """,
        (
            bid,
            session["user_id"]
        ),
        commit=True
    )

    return redirect(url_for("dashboard"))


@app.post("/visitor/create")
def visitor_create():
    if session.get("role") not in ("watchman", "admin"):
        return redirect(url_for("dashboard"))

    q(
        """
        INSERT INTO visitors
        (visitor_name, phone, purpose, visit_date)
        VALUES (%s, %s, %s, %s)
        """,
        (
            request.form["visitor_name"],
            request.form["phone"],
            request.form["purpose"],
            request.form["visit_date"]
        ),
        commit=True
    )

    return redirect(url_for("dashboard"))


@app.post("/visitor/<int:vid>/status")
def visitor_status(vid):
    if session.get("role") not in ("watchman", "admin"):
        return redirect(url_for("dashboard"))

    q(
        """
        UPDATE visitors
        SET status=%s
        WHERE id=%s
        """,
        (
            request.form["status"],
            vid
        ),
        commit=True
    )

    return redirect(url_for("dashboard"))


@app.post("/user/<int:uid>/role")
def user_role(uid):
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    q(
        """
        UPDATE users
        SET role=%s
        WHERE id=%s
        """,
        (
            request.form["role"],
            uid
        ),
        commit=True
    )

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    # Local development only.
    # The production Render server will use:
    # gunicorn app:app
    app.run(debug=True)