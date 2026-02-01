"""Seed the movements glossary with comprehensive BJJ techniques."""
import logging
import json

from rivaflow.db.database import get_connection, convert_query

logger = logging.getLogger(__name__)

# Comprehensive glossary data
MOVEMENTS = [
    # POSITIONS
    {"name": "Guard", "category": "position", "subcategory": "guard", "points": 0, "description": "Bottom position where you control opponent with your legs", "aliases": []},
    {"name": "Closed Guard", "category": "position", "subcategory": "guard", "points": 0, "description": "Legs wrapped around opponent's torso, ankles crossed", "aliases": ["Full Guard"]},
    {"name": "Open Guard", "category": "position", "subcategory": "guard", "points": 0, "description": "Legs not locked, using feet/knees to control", "aliases": []},
    {"name": "Half Guard", "category": "position", "subcategory": "guard", "points": 0, "description": "One opponent's leg trapped between yours", "aliases": []},
    {"name": "Butterfly Guard", "category": "position", "subcategory": "guard", "points": 0, "description": "Seated with feet hooked inside opponent's thighs", "aliases": []},
    {"name": "De La Riva Guard", "category": "position", "subcategory": "guard", "points": 0, "description": "One leg hooks outside opponent's leg while other foot controls hip", "aliases": ["DLR"]},
    {"name": "Spider Guard", "category": "position", "subcategory": "guard", "points": 0, "description": "Feet in opponent's biceps while gripping sleeves", "aliases": []},
    {"name": "Lasso Guard", "category": "position", "subcategory": "guard", "points": 0, "description": "Leg wraps around opponent's arm from outside", "aliases": []},
    {"name": "X-Guard", "category": "position", "subcategory": "guard", "points": 0, "description": "Legs form X shape under opponent", "aliases": []},
    {"name": "Single Leg X", "category": "position", "subcategory": "guard", "points": 0, "description": "One leg controls opponent's leg while other hooks behind knee", "aliases": ["SLX", "Ashi Garami"]},
    {"name": "Rubber Guard", "category": "position", "subcategory": "guard", "points": 0, "description": "High guard using flexibility to control with leg behind head", "aliases": []},
    {"name": "Mount", "category": "position", "subcategory": "dominant", "points": 4, "description": "Top position straddling opponent's torso", "aliases": []},
    {"name": "Back Mount", "category": "position", "subcategory": "dominant", "points": 4, "description": "Behind opponent with hooks inside their thighs", "aliases": ["Back Control", "Rear Mount"]},
    {"name": "Side Control", "category": "position", "subcategory": "dominant", "points": 3, "description": "Chest-to-chest perpendicular to opponent", "aliases": ["Side Mount", "Cross Side"]},
    {"name": "North-South", "category": "position", "subcategory": "dominant", "points": 3, "description": "Chest-to-chest facing opposite direction", "aliases": []},
    {"name": "Knee on Belly", "category": "position", "subcategory": "dominant", "points": 2, "description": "Knee placed on opponent's stomach", "aliases": ["KOB", "Knee on Stomach"]},
    {"name": "Turtle", "category": "position", "subcategory": "defensive", "points": 0, "description": "Defensive position on hands and knees", "aliases": []},
    {"name": "50/50", "category": "position", "subcategory": "neutral", "points": 0, "description": "Legs entangled with equal control", "aliases": ["Fifty Fifty"]},

    # SUBMISSIONS - CHOKES
    {"name": "Rear Naked Choke", "category": "submission", "subcategory": "choke", "points": 0, "description": "Arm around neck from back with figure-four grip", "aliases": ["RNC", "Mata Leão"]},
    {"name": "Triangle Choke", "category": "submission", "subcategory": "choke", "points": 0, "description": "Legs form triangle around neck and one arm", "aliases": ["Triangle"]},
    {"name": "Arm Triangle", "category": "submission", "subcategory": "choke", "points": 0, "description": "Your arm and opponent's shoulder compress their neck", "aliases": ["Kata Gatame"]},
    {"name": "D'Arce Choke", "category": "submission", "subcategory": "choke", "points": 0, "description": "Arm triangle threading arm under armpit", "aliases": ["Darce", "No-Gi Brabo"]},
    {"name": "Anaconda Choke", "category": "submission", "subcategory": "choke", "points": 0, "description": "Similar to D'Arce but arm goes over first", "aliases": []},
    {"name": "Guillotine", "category": "submission", "subcategory": "choke", "points": 0, "description": "Arm wraps around neck from front", "aliases": ["Guillotine Choke"]},
    {"name": "Ezekiel Choke", "category": "submission", "subcategory": "choke", "points": 0, "description": "Using sleeve grip to choke from mount or guard", "aliases": [], "gi_applicable": 1, "nogi_applicable": 0},
    {"name": "Baseball Bat Choke", "category": "submission", "subcategory": "choke", "points": 0, "description": "Collar choke using baseball bat grip", "aliases": [], "gi_applicable": 1, "nogi_applicable": 0},
    {"name": "Bow and Arrow Choke", "category": "submission", "subcategory": "choke", "points": 0, "description": "Collar choke from back pulling opponent's leg", "aliases": [], "gi_applicable": 1, "nogi_applicable": 0},
    {"name": "Cross Collar Choke", "category": "submission", "subcategory": "choke", "points": 0, "description": "Both hands grip opposite collars, forearms cross", "aliases": ["X Choke"], "gi_applicable": 1, "nogi_applicable": 0},
    {"name": "Loop Choke", "category": "submission", "subcategory": "choke", "points": 0, "description": "Quick collar choke during guard pass attempts", "aliases": [], "gi_applicable": 1, "nogi_applicable": 0},
    {"name": "Clock Choke", "category": "submission", "subcategory": "choke", "points": 0, "description": "Collar choke on turtle, walking around like clock", "aliases": [], "gi_applicable": 1, "nogi_applicable": 0},
    {"name": "Paper Cutter Choke", "category": "submission", "subcategory": "choke", "points": 0, "description": "Forearm across throat from side using collar", "aliases": [], "gi_applicable": 1, "nogi_applicable": 0},
    {"name": "North-South Choke", "category": "submission", "subcategory": "choke", "points": 0, "description": "Arm wraps head from north-south", "aliases": []},
    {"name": "Von Flue Choke", "category": "submission", "subcategory": "choke", "points": 0, "description": "Counter to guillotine using shoulder pressure", "aliases": ["Von Flue"]},

    # SUBMISSIONS - ARM LOCKS
    {"name": "Armbar", "category": "submission", "subcategory": "armlock", "points": 0, "description": "Hyperextending elbow against hips", "aliases": ["Juji-Gatame", "Straight Armbar"]},
    {"name": "Kimura", "category": "submission", "subcategory": "armlock", "points": 0, "description": "Figure-four grip rotating shoulder", "aliases": ["Double Wristlock"]},
    {"name": "Americana", "category": "submission", "subcategory": "armlock", "points": 0, "description": "Reverse Kimura from mount or side control", "aliases": ["Keylock", "V1 Armlock"]},
    {"name": "Omoplata", "category": "submission", "subcategory": "armlock", "points": 0, "description": "Shoulder lock using legs from guard", "aliases": []},
    {"name": "Wristlock", "category": "submission", "subcategory": "armlock", "points": 0, "description": "Hyperextending or rotating wrist joint", "aliases": []},

    # SUBMISSIONS - LEG LOCKS
    {"name": "Straight Ankle Lock", "category": "submission", "subcategory": "leglock", "points": 0, "description": "Achilles lock hyperextending ankle", "aliases": ["Ankle Lock", "Achilles Lock"]},
    {"name": "Heel Hook", "category": "submission", "subcategory": "leglock", "points": 0, "description": "Rotating heel to attack knee ligaments", "aliases": [], "ibjjf_legal_white": 0, "ibjjf_legal_blue": 0, "ibjjf_legal_purple": 0, "ibjjf_legal_brown": 0},
    {"name": "Inside Heel Hook", "category": "submission", "subcategory": "leglock", "points": 0, "description": "Heel hook from inside position", "aliases": [], "ibjjf_legal_white": 0, "ibjjf_legal_blue": 0, "ibjjf_legal_purple": 0, "ibjjf_legal_brown": 0},
    {"name": "Outside Heel Hook", "category": "submission", "subcategory": "leglock", "points": 0, "description": "Heel hook from outside position", "aliases": [], "ibjjf_legal_white": 0, "ibjjf_legal_blue": 0, "ibjjf_legal_purple": 0, "ibjjf_legal_brown": 0},
    {"name": "Kneebar", "category": "submission", "subcategory": "leglock", "points": 0, "description": "Hyperextending knee like an armbar", "aliases": []},
    {"name": "Toe Hold", "category": "submission", "subcategory": "leglock", "points": 0, "description": "Figure-four grip twisting foot/ankle", "aliases": []},
    {"name": "Calf Slicer", "category": "submission", "subcategory": "leglock", "points": 0, "description": "Shin behind knee, pulling foot to compress calf", "aliases": ["Calf Crush"]},

    # SWEEPS
    {"name": "Scissor Sweep", "category": "sweep", "subcategory": "closed guard", "points": 2, "description": "Knee shield and sleeve grip to reverse from closed guard", "aliases": []},
    {"name": "Hip Bump Sweep", "category": "sweep", "subcategory": "closed guard", "points": 2, "description": "Explosively sit up and bump opponent over", "aliases": ["Hip Heist"]},
    {"name": "Flower Sweep", "category": "sweep", "subcategory": "closed guard", "points": 2, "description": "Swing leg like pendulum to sweep", "aliases": ["Pendulum Sweep"]},
    {"name": "Elevator Sweep", "category": "sweep", "subcategory": "butterfly", "points": 2, "description": "Butterfly hook lifts opponent over", "aliases": []},
    {"name": "Hook Sweep", "category": "sweep", "subcategory": "butterfly", "points": 2, "description": "Using butterfly hooks to tip opponent sideways", "aliases": []},
    {"name": "Tripod Sweep", "category": "sweep", "subcategory": "open guard", "points": 2, "description": "Foot on hip, hook behind knee, hand on ankle", "aliases": []},
    {"name": "Sickle Sweep", "category": "sweep", "subcategory": "open guard", "points": 2, "description": "Foot on hip, other leg sweeps base leg", "aliases": []},
    {"name": "Berimbolo", "category": "sweep", "subcategory": "modern", "points": 2, "description": "Rolling under opponent to take back", "aliases": []},
    {"name": "Waiter Sweep", "category": "sweep", "subcategory": "half guard", "points": 2, "description": "From half guard, arm under leg like serving tray", "aliases": []},
    {"name": "Old School Sweep", "category": "sweep", "subcategory": "half guard", "points": 2, "description": "Classic half guard sweep to dog fight", "aliases": []},

    # GUARD PASSES
    {"name": "Toreando Pass", "category": "pass", "subcategory": "standing", "points": 3, "description": "Grip pants, push legs to side like bullfighter", "aliases": ["Bullfighter Pass", "Toreador Pass"]},
    {"name": "Knee Slice", "category": "pass", "subcategory": "pressure", "points": 3, "description": "Knee slides through guard cutting across thigh", "aliases": ["Knee Cut"]},
    {"name": "Over-Under Pass", "category": "pass", "subcategory": "pressure", "points": 3, "description": "One arm over leg, one under for pressure passing", "aliases": []},
    {"name": "Stack Pass", "category": "pass", "subcategory": "pressure", "points": 3, "description": "Drive opponent's knees toward face, fold them", "aliases": []},
    {"name": "Double Under Pass", "category": "pass", "subcategory": "pressure", "points": 3, "description": "Both arms under opponent's legs, stacking", "aliases": []},
    {"name": "Leg Drag", "category": "pass", "subcategory": "dynamic", "points": 3, "description": "Drag opponent's leg across their body to pass", "aliases": []},
    {"name": "Long Step Pass", "category": "pass", "subcategory": "standing", "points": 3, "description": "Wide step around guard to side control", "aliases": []},
    {"name": "X-Pass", "category": "pass", "subcategory": "dynamic", "points": 3, "description": "Step over leg while controlling, cross-step", "aliases": []},

    # TAKEDOWNS
    {"name": "Double Leg Takedown", "category": "takedown", "subcategory": "wrestling", "points": 2, "description": "Shoot both arms around opponent's legs", "aliases": ["Double Leg"]},
    {"name": "Single Leg Takedown", "category": "takedown", "subcategory": "wrestling", "points": 2, "description": "Attack one leg with various finishes", "aliases": ["Single Leg"]},
    {"name": "Ankle Pick", "category": "takedown", "subcategory": "wrestling", "points": 2, "description": "Quick grab of ankle while off-balancing", "aliases": []},
    {"name": "Arm Drag", "category": "takedown", "subcategory": "wrestling", "points": 2, "description": "Pull opponent's arm across to expose back", "aliases": []},
    {"name": "Duck Under", "category": "takedown", "subcategory": "wrestling", "points": 2, "description": "Go under opponent's arm to take back standing", "aliases": []},
    {"name": "Hip Toss", "category": "takedown", "subcategory": "judo", "points": 2, "description": "Judo throw using hip as fulcrum", "aliases": ["O Goshi"]},
    {"name": "Foot Sweep", "category": "takedown", "subcategory": "judo", "points": 2, "description": "Sweeping opponent's foot while off-balance", "aliases": ["De Ashi Barai"]},

    # ESCAPES
    {"name": "Shrimp", "category": "escape", "subcategory": "fundamental", "points": 0, "description": "Push with feet, move hips away - fundamental escape", "aliases": ["Hip Escape"]},
    {"name": "Bridge", "category": "escape", "subcategory": "fundamental", "points": 0, "description": "Explosively lifting hips off mat", "aliases": []},
    {"name": "Upa", "category": "escape", "subcategory": "mount", "points": 0, "description": "Bridge and roll opponent from mount", "aliases": ["Trap and Roll"]},
    {"name": "Elbow-Knee Escape", "category": "escape", "subcategory": "mount", "points": 0, "description": "Creating space to reguard from mount", "aliases": []},
    {"name": "Running Escape", "category": "escape", "subcategory": "side control", "points": 0, "description": "Side control escape turning away to knees", "aliases": []},
    {"name": "Granby Roll", "category": "escape", "subcategory": "advanced", "points": 0, "description": "Inverting/rolling to escape or reguard", "aliases": []},

    # MOVEMENTS & CONCEPTS
    {"name": "Frame", "category": "movement", "subcategory": "defense", "points": 0, "description": "Using bone structure to create space", "aliases": ["Framing"]},
    {"name": "Base", "category": "concept", "subcategory": "fundamental", "points": 0, "description": "Stability and balance foundation", "aliases": []},
    {"name": "Posture", "category": "concept", "subcategory": "fundamental", "points": 0, "description": "Spine alignment for control and defense", "aliases": []},
    {"name": "Pressure", "category": "concept", "subcategory": "fundamental", "points": 0, "description": "Using body weight effectively to control", "aliases": []},
    {"name": "Underhook", "category": "movement", "subcategory": "control", "points": 0, "description": "Arm under opponent's armpit for control", "aliases": []},
    {"name": "Overhook", "category": "movement", "subcategory": "control", "points": 0, "description": "Arm over opponent's arm wrapping down", "aliases": ["Whizzer"]},
]


def seed_glossary():
    """Seed the movements glossary with comprehensive techniques."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if already seeded
        cursor.execute(convert_query("SELECT COUNT(*) as count FROM movements_glossary WHERE custom = 0"))
        result = cursor.fetchone()
        # Handle both tuple (SQLite/raw) and dict (PostgreSQL RealDictCursor) results
        if hasattr(result, 'keys'):
            seeded_count = result['count']
        else:
            seeded_count = result[0]

        if seeded_count > 0:
            logger.info(f"Glossary already seeded with {seeded_count} techniques. Skipping.")
            return

        # Insert all movements
        inserted = 0
        for movement in MOVEMENTS:
            # Set defaults for optional fields
            movement.setdefault("gi_applicable", 1)
            movement.setdefault("nogi_applicable", 1)
            movement.setdefault("ibjjf_legal_white", 1)
            movement.setdefault("ibjjf_legal_blue", 1)
            movement.setdefault("ibjjf_legal_purple", 1)
            movement.setdefault("ibjjf_legal_brown", 1)
            movement.setdefault("ibjjf_legal_black", 1)
            movement.setdefault("points", 0)
            movement.setdefault("subcategory", None)
            movement.setdefault("description", "")

            # Convert aliases list to JSON string
            aliases_json = json.dumps(movement.get("aliases", []))

            try:
                cursor.execute(convert_query("""
                    INSERT INTO movements_glossary (
                        name, category, subcategory, points, description,
                        aliases, gi_applicable, nogi_applicable,
                        ibjjf_legal_white, ibjjf_legal_blue, ibjjf_legal_purple,
                        ibjjf_legal_brown, ibjjf_legal_black, custom
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """), (
                    movement["name"],
                    movement["category"],
                    movement["subcategory"],
                    movement["points"],
                    movement["description"],
                    aliases_json,
                    movement["gi_applicable"],
                    movement["nogi_applicable"],
                    movement["ibjjf_legal_white"],
                    movement["ibjjf_legal_blue"],
                    movement["ibjjf_legal_purple"],
                    movement["ibjjf_legal_brown"],
                    movement["ibjjf_legal_black"],
                ))
                inserted += 1
            except Exception as e:
                # Handle IntegrityError from both sqlite3 and psycopg2
                if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                    logger.warning(f"Skipping duplicate: {movement['name']}")
                    continue
                else:
                    raise

        conn.commit()
        logger.info(f"Successfully seeded {inserted} techniques into glossary!")


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    seed_glossary()
