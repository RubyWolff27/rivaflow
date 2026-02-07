"""Service for generating game plans from belt/archetype templates."""

import json
import logging
from pathlib import Path

from rivaflow.db.repositories.game_plan_node_repo import (
    GamePlanNodeRepository,
)
from rivaflow.db.repositories.game_plan_repo import (
    GamePlanRepository,
)
from rivaflow.db.repositories.glossary_repo import (
    GlossaryRepository,
)

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "data" / "game_plan_templates"


def _resolve_glossary_id(name: str) -> int | None:
    """Look up a glossary entry by name."""
    entry = GlossaryRepository.get_by_name(name)
    return entry["id"] if entry else None


def _create_nodes_recursive(
    plan_id: int,
    nodes: list[dict],
    parent_id: int | None = None,
    sort_start: int = 0,
) -> list[int]:
    """Recursively create nodes from template tree."""
    created_ids = []
    for i, node_def in enumerate(nodes):
        glossary_id = None
        linked = node_def.get("linked_glossary_names", [])
        if linked:
            glossary_id = _resolve_glossary_id(linked[0])

        node_id = GamePlanNodeRepository.create(
            plan_id=plan_id,
            name=node_def["name"],
            node_type=node_def.get("node_type", "technique"),
            parent_id=parent_id,
            glossary_id=glossary_id,
            sort_order=sort_start + i,
        )
        created_ids.append(node_id)

        children = node_def.get("children", [])
        if children:
            child_ids = _create_nodes_recursive(plan_id, children, parent_id=node_id)
            created_ids.extend(child_ids)

    return created_ids


def generate_plan_from_template(
    user_id: int,
    belt_level: str,
    archetype: str,
    style: str = "balanced",
) -> dict:
    """Generate a game plan from a template file.

    Args:
        user_id: User ID
        belt_level: e.g. 'white', 'blue'
        archetype: e.g. 'guard_player', 'top_passer'
        style: e.g. 'balanced', 'aggressive', 'defensive'

    Returns:
        Created game plan dict with id
    """
    template_name = f"{belt_level}_{archetype}.json"
    template_path = TEMPLATES_DIR / template_name

    if not template_path.exists():
        logger.warning(f"Template not found: {template_name}, " "using fallback")
        template_path = TEMPLATES_DIR / "white_guard_player.json"

    if not template_path.exists():
        raise FileNotFoundError(
            f"No game plan template found for " f"{belt_level}/{archetype}"
        )

    with open(template_path) as f:
        template = json.load(f)

    title = template.get(
        "title",
        f"{belt_level.title()} Belt - " f"{archetype.replace('_', ' ').title()}",
    )

    plan_id = GamePlanRepository.create(
        user_id=user_id,
        belt_level=belt_level,
        archetype=archetype,
        style=style,
        title=title,
    )

    nodes = template.get("nodes", [])
    _create_nodes_recursive(plan_id, nodes)

    return GamePlanRepository.get_by_id(plan_id, user_id)
