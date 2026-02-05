"""Cursor-based pagination utilities for efficient pagination of large datasets."""

from typing import Any


def encode_cursor(date: str, item_type: str, item_id: int) -> str:
    """
    Encode pagination cursor from item metadata.

    Args:
        date: ISO format date string
        item_type: Type of the item (e.g., "session", "readiness")
        item_id: ID of the item

    Returns:
        Encoded cursor string
    """
    return f"{date}:{item_type}:{item_id}"


def decode_cursor(cursor: str) -> tuple[str, str, int] | None:
    """
    Decode pagination cursor to item metadata.

    Args:
        cursor: Encoded cursor string

    Returns:
        Tuple of (date, item_type, item_id) or None if invalid
    """
    try:
        parts = cursor.split(":")
        if len(parts) == 3:
            date_str, item_type, item_id_str = parts
            return (date_str, item_type, int(item_id_str))
    except (ValueError, IndexError):
        pass
    return None


def paginate_with_cursor(
    items: list[dict[str, Any]],
    limit: int,
    offset: int = 0,
    cursor: str | None = None,
) -> dict[str, Any]:
    """
    Apply cursor-based pagination to a list of items.

    Supports both cursor-based (efficient for large datasets) and offset-based
    (backward compatibility) pagination.

    Args:
        items: List of items to paginate (must be pre-sorted)
        limit: Maximum items to return
        offset: Pagination offset (used if cursor not provided)
        cursor: Cursor for pagination (format: "date:type:id")

    Returns:
        Pagination result with items, cursor, next_cursor, and metadata
    """
    total_items = len(items)
    cursor_pos = None

    if cursor:
        # Parse cursor and find position
        cursor_data = decode_cursor(cursor)
        if cursor_data:
            cursor_date, cursor_type, cursor_id = cursor_data

            # Find the position of the cursor in the items list
            for i, item in enumerate(items):
                if (
                    item.get("date") == cursor_date
                    and item.get("type") == cursor_type
                    and item.get("id") == cursor_id
                ):
                    cursor_pos = i + 1  # Start from next item
                    break

    # Determine slice position
    if cursor_pos is not None:
        start_pos = cursor_pos
    else:
        start_pos = offset

    # Get paginated slice
    paginated_items = items[start_pos : start_pos + limit]

    # Generate next cursor from last item
    next_cursor = None
    if paginated_items and len(paginated_items) == limit and start_pos + limit < total_items:
        last_item = paginated_items[-1]
        next_cursor = encode_cursor(last_item["date"], last_item["type"], last_item["id"])

    return {
        "items": paginated_items,
        "total": total_items,
        "limit": limit,
        "offset": offset if not cursor else start_pos,
        "cursor": cursor,
        "next_cursor": next_cursor,
        "has_more": start_pos + limit < total_items,
    }
