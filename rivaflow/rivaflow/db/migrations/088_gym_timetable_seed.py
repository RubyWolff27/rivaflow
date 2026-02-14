"""Seed Alliance Jiu Jitsu Drummoyne timetable data.

Run with: python -m rivaflow.db.migrations.088_gym_timetable_seed
"""

from rivaflow.db.database import convert_query, get_connection

# Alliance Drummoyne timetable (kids classes excluded)
# day_of_week: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday,
#              5=Saturday, 6=Sunday
ALLIANCE_DRUMMOYNE_CLASSES = [
    # Tuesday & Thursday 6:30 AM
    (1, "06:30", "07:30", "Beginner/Intermediate", "gi", "all"),
    (3, "06:30", "07:30", "Beginner/Intermediate", "gi", "all"),
    # Weekday lunchtime 12:00
    (0, "12:00", "13:00", "Beginner/Intermediate Gi", "gi", "all"),
    (1, "12:00", "13:00", "Beginner/Intermediate Gi", "gi", "all"),
    (2, "12:00", "13:00", "Beginner/Intermediate Gi", "gi", "all"),
    (3, "12:00", "13:00", "Beginner/Intermediate Gi", "gi", "all"),
    (4, "12:00", "13:00", "No Gi", "no-gi", "all"),
    # Monday evening
    (0, "17:30", "19:00", "Intermediate/Advanced Gi", "gi", "advanced"),
    (0, "19:00", "20:00", "Fundamentals Gi", "gi", "beginner"),
    # Tuesday evening
    (1, "17:00", "18:00", "Fundamentals Gi", "gi", "beginner"),
    (1, "18:30", "20:00", "Intermediate/Advanced Gi", "gi", "advanced"),
    # Wednesday evening
    (2, "17:30", "19:00", "Intermediate/Advanced Gi", "gi", "advanced"),
    (2, "19:00", "20:00", "Fundamentals Gi", "gi", "beginner"),
    # Thursday evening
    (3, "17:30", "18:30", "Fundamentals", "gi", "beginner"),
    (3, "18:30", "20:00", "Intermediate/Advanced Gi", "gi", "advanced"),
    # Friday evening
    (4, "17:30", "18:30", "No Gi", "no-gi", "all"),
    (4, "17:30", "18:30", "Fundamentals", "gi", "beginner"),
    # Saturday
    (5, "10:00", "11:00", "Fundamentals Gi", "gi", "beginner"),
    (5, "11:00", "12:00", "Open Mat", "open-mat", "all"),
    (5, "17:30", "18:30", "No Gi", "no-gi", "all"),
]


def seed():
    """Insert Alliance Drummoyne timetable if gym exists."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Find Alliance Drummoyne gym
        cursor.execute(
            convert_query("SELECT id FROM gyms WHERE name LIKE ?"),
            ("%Alliance%Drummoyne%",),
        )
        row = cursor.fetchone()
        if not row:
            print("Alliance Drummoyne gym not found — " "skipping timetable seed.")
            return

        gym_id = row["id"] if hasattr(row, "keys") else row[0]

        # Check if classes already seeded
        cursor.execute(
            convert_query("SELECT COUNT(*) FROM gym_classes WHERE gym_id = ?"),
            (gym_id,),
        )
        count_row = cursor.fetchone()
        count = (
            count_row["count"]
            if hasattr(count_row, "keys") and "count" in count_row
            else (
                list(count_row.values())[0]
                if hasattr(count_row, "values")
                else count_row[0]
            )
        )
        if count > 0:
            print(f"Gym {gym_id} already has {count} classes — " "skipping seed.")
            return

        # Insert classes
        for (
            day,
            start,
            end,
            name,
            ctype,
            level,
        ) in ALLIANCE_DRUMMOYNE_CLASSES:
            cursor.execute(
                convert_query("""
                    INSERT INTO gym_classes
                    (gym_id, day_of_week, start_time, end_time,
                     class_name, class_type, level)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """),
                (gym_id, day, start, end, name, ctype, level),
            )

        print(f"Seeded {len(ALLIANCE_DRUMMOYNE_CLASSES)} classes " f"for gym {gym_id}.")


if __name__ == "__main__":
    seed()
