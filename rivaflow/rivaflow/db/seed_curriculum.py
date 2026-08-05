"""Seed the AJJ purple-belt curriculum slots for a user.

Usage::

    python -m rivaflow.db.seed_curriculum <user_id> [--draft] [--belt purple]

``--draft`` attaches Ruby's DRAFT slate to every of-choice slot. Without it the
of-choice slots are created undeclared, ready for him to fill in the UI. The
seed is a no-op when the user already has slots, unless ``--force`` is given.
"""

import argparse
import logging

from rivaflow.core.services.curriculum_service import DEFAULT_BELT, CurriculumService

logger = logging.getLogger(__name__)


def seed_curriculum(
    user_id: int,
    with_draft: bool = False,
    belt: str = DEFAULT_BELT,
    force: bool = False,
) -> dict:
    """Create the ~90 syllabus slots for *user_id*."""
    result = CurriculumService().seed_user(
        user_id=user_id, with_draft=with_draft, belt=belt, force=force
    )
    if result["skipped"]:
        logger.info(
            "User %s already has %s %s slots — nothing seeded (use --force to add)",
            user_id,
            result["existing"],
            belt,
        )
    else:
        logger.info(
            "Seeded %s %s curriculum slots for user %s (draft slate: %s)",
            result["seeded"],
            belt,
            user_id,
            with_draft,
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("user_id", type=int)
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Attach Ruby's DRAFT slate to the of-choice slots",
    )
    parser.add_argument("--belt", default=DEFAULT_BELT)
    parser.add_argument(
        "--force", action="store_true", help="Seed even if slots already exist"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    seed_curriculum(
        user_id=args.user_id,
        with_draft=args.draft,
        belt=args.belt,
        force=args.force,
    )


if __name__ == "__main__":
    main()
