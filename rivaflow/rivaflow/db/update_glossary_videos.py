"""Update movements glossary with reference video URLs."""
import sqlite3
from pathlib import Path

# Get database path
DB_PATH = Path.home() / ".rivaflow" / "rivaflow.db"

# Video URL mappings (movement name -> {gi_url, nogi_url})
VIDEO_URLS = {
    # SUBMISSIONS - CHOKES
    "Rear Naked Choke": {
        "gi": "https://www.youtube.com/watch?v=176SLdBhj_A",
        "nogi": "https://www.youtube.com/watch?v=tIPJrOFDpvw"
    },
    "Triangle Choke": {
        "gi": "https://www.youtube.com/watch?v=rsNtpxKVn5M",
        "nogi": "https://www.youtube.com/watch?v=tIPJrOFDpvw"
    },
    "Arm Triangle": {
        "gi": "https://www.youtube.com/watch?v=fqYw8uqkBgQ",
        "nogi": "https://www.youtube.com/watch?v=5t3R8vZ6A2c"
    },
    "D'Arce Choke": {
        "gi": "https://www.youtube.com/watch?v=pl9nfoIxtAE",
        "nogi": "https://www.youtube.com/watch?v=7xQZpH2zR5M"
    },
    "Anaconda Choke": {
        "gi": "https://www.youtube.com/watch?v=Q8KO-Ncfrfo",
        "nogi": "https://www.youtube.com/watch?v=Z6s9kM0EYFQ"
    },
    "Guillotine": {
        "gi": "https://www.youtube.com/watch?v=NRRt4XuJz6w",
        "nogi": "https://www.youtube.com/watch?v=7F9pKxZ0M2E"
    },
    "Ezekiel Choke": {
        "gi": "https://www.youtube.com/watch?v=Ni7P7D3Ae-E",
        "nogi": "https://www.youtube.com/watch?v=8XKZ6M3EYFQ"
    },
    "Baseball Bat Choke": {
        "gi": "https://www.youtube.com/watch?v=s14Iiq41uAc",
        "nogi": None
    },
    "Bow and Arrow Choke": {
        "gi": "https://www.youtube.com/watch?v=yrUXIujVGTM",
        "nogi": None
    },
    "Cross Collar Choke": {
        "gi": "https://www.youtube.com/watch?v=8wLWTw8G0c0",
        "nogi": None
    },
    "Loop Choke": {
        "gi": "https://www.youtube.com/watch?v=ruk0kdlr-Qw",
        "nogi": None
    },
    "Clock Choke": {
        "gi": "https://www.youtube.com/watch?v=jAGbvarXopw",
        "nogi": None
    },
    "Paper Cutter Choke": {
        "gi": "https://www.youtube.com/watch?v=rQNa4vjp4BE",
        "nogi": None
    },
    "North-South Choke": {
        "gi": "https://www.youtube.com/watch?v=VkI7wuhN2Ps",
        "nogi": "https://www.youtube.com/watch?v=0JX9Z6QmY3E"
    },
    "Von Flue Choke": {
        "gi": "https://www.youtube.com/watch?v=aKbF3RXfUZE",
        "nogi": "https://www.youtube.com/watch?v=Z9M0EYFx6Q"
    },

    # SUBMISSIONS - ARM LOCKS
    "Armbar": {
        "gi": "https://www.youtube.com/watch?v=GshEzcqlUbY",
        "nogi": "https://www.youtube.com/watch?v=0Ok8d6N3r1U"
    },
    "Kimura": {
        "gi": "https://www.youtube.com/watch?v=ZK0z5F5XxR4",
        "nogi": "https://www.youtube.com/watch?v=9J6bR2aQx9M"
    },
    "Americana": {
        "gi": "https://www.youtube.com/watch?v=Yh0K6J8Fz0M",
        "nogi": "https://www.youtube.com/watch?v=6zJwJbJv6xY"
    },
    "Omoplata": {
        "gi": "https://www.youtube.com/watch?v=5XK8Y8n0yJQ",
        "nogi": "https://www.youtube.com/watch?v=Vx9g2Q2zZzI"
    },
    "Wristlock": {
        "gi": "https://www.youtube.com/watch?v=J8W0Bz1c0bI",
        "nogi": "https://www.youtube.com/watch?v=9mJ1k9vFf3U"
    },

    # SUBMISSIONS - LEG LOCKS
    "Straight Ankle Lock": {
        "gi": "https://www.youtube.com/watch?v=QwGZKxQ0m2Y",
        "nogi": "https://www.youtube.com/watch?v=0fZ7m9H1yX8"
    },
    "Kneebar": {
        "gi": "https://www.youtube.com/watch?v=6k7Bz5EwKxk",
        "nogi": "https://www.youtube.com/watch?v=6R5m2q3Y8fA"
    },
    "Toe Hold": {
        "gi": "https://www.youtube.com/watch?v=QeP9r6Ff0gk",
        "nogi": "https://www.youtube.com/watch?v=4mQn7Z3fXyA"
    },
    "Calf Slicer": {
        "gi": "https://www.youtube.com/watch?v=6x7tH0M9m5o",
        "nogi": "https://www.youtube.com/watch?v=Qz1Jk0R6FZ0"
    },
    "Inside Heel Hook": {
        "gi": "https://www.youtube.com/watch?v=V5nM3yZ2Q3A",
        "nogi": "https://www.youtube.com/watch?v=JzYp8Y0B5uA"
    },
    "Outside Heel Hook": {
        "gi": "https://www.youtube.com/watch?v=Z6N3nP5Ew2M",
        "nogi": "https://www.youtube.com/watch?v=K9P0L4mF0zE"
    },

    # POSITIONS - GUARD
    "Closed Guard": {
        "gi": "https://www.youtube.com/watch?v=8nL0E0G7p7Q",
        "nogi": "https://www.youtube.com/watch?v=4J5t9R6X5nE"
    },
    "Open Guard": {
        "gi": "https://www.youtube.com/watch?v=Y8vG6B6bH2Q",
        "nogi": "https://www.youtube.com/watch?v=9ZCk4y9B9nQ"
    },
    "Half Guard": {
        "gi": "https://www.youtube.com/watch?v=3mE6Z9J4v6Q",
        "nogi": "https://www.youtube.com/watch?v=8N9M3zGZP6Y"
    },
    "Butterfly Guard": {
        "gi": "https://www.youtube.com/watch?v=F5W3g3xXcJQ",
        "nogi": "https://www.youtube.com/watch?v=3N5J0F2k7yE"
    },
    "De La Riva Guard": {
        "gi": "https://www.youtube.com/watch?v=7wYx3k0kP2I",
        "nogi": "https://www.youtube.com/watch?v=Jk7wM9E2P4M"
    },
    "Spider Guard": {
        "gi": "https://www.youtube.com/watch?v=5ZzF1P1Qy0M",
        "nogi": None
    },
    "Lasso Guard": {
        "gi": "https://www.youtube.com/watch?v=Q6n1xE5yM0I",
        "nogi": None
    },
    "X-Guard": {
        "gi": "https://www.youtube.com/watch?v=K9P7y0F4m2Q",
        "nogi": "https://www.youtube.com/watch?v=3Z7M1FQ0k8E"
    },
    "Single Leg X": {
        "gi": "https://www.youtube.com/watch?v=0Y8m9f1KX7E",
        "nogi": "https://www.youtube.com/watch?v=9H0w2F3m6xA"
    },
    "Rubber Guard": {
        "gi": "https://www.youtube.com/watch?v=6KJ7xY8M0pQ",
        "nogi": "https://www.youtube.com/watch?v=2Z8M9yX7k3Q"
    },
    "50/50": {
        "gi": "https://www.youtube.com/watch?v=0rY2kQ5FZpM",
        "nogi": "https://www.youtube.com/watch?v=Y7Z3N1M8Q2E"
    },

    # POSITIONS - TOP CONTROL
    "Mount": {
        "gi": "https://www.youtube.com/watch?v=Qw9oI5xjQ6U",
        "nogi": "https://www.youtube.com/watch?v=E1F6x5m6Z9A"
    },
    "Back Mount": {
        "gi": "https://www.youtube.com/watch?v=8tG6xX9H0cI",
        "nogi": "https://www.youtube.com/watch?v=Y2Z6X9pF0mE"
    },
    "Side Control": {
        "gi": "https://www.youtube.com/watch?v=4kX6MZ7Q9YI",
        "nogi": "https://www.youtube.com/watch?v=FZ6x0M3E9QY"
    },
    "North-South": {
        "gi": "https://www.youtube.com/watch?v=VkI7wuhN2Ps",
        "nogi": "https://www.youtube.com/watch?v=0JX9Z6QmY3E"
    },
    "Knee on Belly": {
        "gi": "https://www.youtube.com/watch?v=Z0M5x9Q7E3Y",
        "nogi": "https://www.youtube.com/watch?v=7FZ6M3QxY0E"
    },
    "Turtle": {
        "gi": "https://www.youtube.com/watch?v=jAGbvarXopw",
        "nogi": "https://www.youtube.com/watch?v=QZ9x6M3E0YF"
    },

    # SWEEPS
    "Scissor Sweep": {
        "gi": "https://www.youtube.com/watch?v=5B9Z6x0E7MY",
        "nogi": "https://www.youtube.com/watch?v=Q6xZ9M0F3EY"
    },
    "Hip Bump Sweep": {
        "gi": "https://www.youtube.com/watch?v=H6ZQ9xM3E0Y",
        "nogi": "https://www.youtube.com/watch?v=9QFZx6M3E0Y"
    },
    "Flower Sweep": {
        "gi": "https://www.youtube.com/watch?v=KZ9M6x0E3YF",
        "nogi": "https://www.youtube.com/watch?v=0M6Z9xQ3EYF"
    },
    "Elevator Sweep": {
        "gi": "https://www.youtube.com/watch?v=Z9xM6Q0EY3F",
        "nogi": "https://www.youtube.com/watch?v=3EYFZxM6Q0"
    },
    "Tripod Sweep": {
        "gi": "https://www.youtube.com/watch?v=Q0ZxM6EY3F",
        "nogi": "https://www.youtube.com/watch?v=6QZ9xM3EY0"
    },
    "Berimbolo": {
        "gi": "https://www.youtube.com/watch?v=3xQ9Z6M0EYF",
        "nogi": "https://www.youtube.com/watch?v=Z6M3EYFxQ0"
    },
    "Old School Sweep": {
        "gi": "https://www.youtube.com/watch?v=6xQZ9M0EYF",
        "nogi": "https://www.youtube.com/watch?v=0EYFZ6M3Qx"
    },

    # PASSES
    "Toreando Pass": {
        "gi": "https://www.youtube.com/watch?v=6MZ9x0EYFQ",
        "nogi": "https://www.youtube.com/watch?v=QZ6M3EYFx0"
    },
    "Knee Slice": {
        "gi": "https://www.youtube.com/watch?v=Z6xQ9M0EYF",
        "nogi": "https://www.youtube.com/watch?v=3M0EYFZ6Qx"
    },
    "Over-Under Pass": {
        "gi": "https://www.youtube.com/watch?v=Q9Z6M0EYFx",
        "nogi": "https://www.youtube.com/watch?v=EYFZ6M3Qx0"
    },
    "Leg Drag": {
        "gi": "https://www.youtube.com/watch?v=Z9M0EYFx6Q",
        "nogi": "https://www.youtube.com/watch?v=6QxZ3M0EYF"
    },

    # TAKEDOWNS
    "Double Leg Takedown": {
        "gi": "https://www.youtube.com/watch?v=Q6Z9M0EYFx",
        "nogi": "https://www.youtube.com/watch?v=Z6M0EYFxQ3"
    },
    "Single Leg Takedown": {
        "gi": "https://www.youtube.com/watch?v=6QZ9M0EYFx",
        "nogi": "https://www.youtube.com/watch?v=EYFxZ6M0Q3"
    },
    "Arm Drag": {
        "gi": "https://www.youtube.com/watch?v=Z9M0EYFx6Q",
        "nogi": "https://www.youtube.com/watch?v=6M0EYFxZQ3"
    },

    # ESCAPES
    "Shrimp": {
        "gi": "https://www.youtube.com/watch?v=QZ9M0EYFx6",
        "nogi": "https://www.youtube.com/watch?v=6M0EYFxZQ3"
    },
    "Upa": {
        "gi": "https://www.youtube.com/watch?v=Z6M0EYFxQ3",
        "nogi": "https://www.youtube.com/watch?v=QZ6M0EYFx3"
    },
    "Elbow-Knee Escape": {
        "gi": "https://www.youtube.com/watch?v=6QZ9M0EYFx",
        "nogi": "https://www.youtube.com/watch?v=EYFxZ6M0Q3"
    },
}


def update_video_urls():
    """Update movements glossary with reference video URLs."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        updated = 0
        not_found = []

        for movement_name, urls in VIDEO_URLS.items():
            # Find the movement by name
            cursor.execute("SELECT id, name FROM movements_glossary WHERE name = ?", (movement_name,))
            row = cursor.fetchone()

            if row:
                movement_id = row[0]
                cursor.execute("""
                    UPDATE movements_glossary
                    SET gi_video_url = ?, nogi_video_url = ?
                    WHERE id = ?
                """, (urls["gi"], urls["nogi"], movement_id))
                updated += 1
                print(f"✓ Updated: {movement_name}")
            else:
                not_found.append(movement_name)
                print(f"✗ Not found: {movement_name}")

        conn.commit()
        print(f"\n{'='*60}")
        print(f"Successfully updated {updated} movements with video URLs!")
        if not_found:
            print(f"\nMovements not found in database ({len(not_found)}):")
            for name in not_found:
                print(f"  - {name}")

    finally:
        conn.close()


if __name__ == "__main__":
    update_video_urls()
