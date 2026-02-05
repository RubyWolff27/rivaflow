"""Service layer for friends (training partners and instructors) operations."""

from rivaflow.db.repositories import FriendRepository


class FriendService:
    """Business logic for friends."""

    def __init__(self):
        self.repo = FriendRepository()

    def create_friend(
        self,
        user_id: int,
        name: str,
        friend_type: str = "training-partner",
        belt_rank: str | None = None,
        belt_stripes: int = 0,
        instructor_certification: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        notes: str | None = None,
    ) -> dict:
        """Create a new friend."""
        return self.repo.create(
            user_id=user_id,
            name=name,
            friend_type=friend_type,
            belt_rank=belt_rank,
            belt_stripes=belt_stripes,
            instructor_certification=instructor_certification,
            phone=phone,
            email=email,
            notes=notes,
        )

    def get_friend(self, user_id: int, friend_id: int) -> dict | None:
        """Get a friend by ID."""
        return self.repo.get_by_id(user_id, friend_id)

    def get_friend_by_name(self, user_id: int, name: str) -> dict | None:
        """Get a friend by exact name match."""
        return self.repo.get_by_name(user_id, name)

    def list_friends(self, user_id: int, order_by: str = "name ASC") -> list[dict]:
        """Get all friends."""
        return self.repo.list_all(user_id, order_by=order_by)

    def list_instructors(self, user_id: int) -> list[dict]:
        """Get all friends who are instructors."""
        instructors = self.repo.list_by_type(user_id, "instructor", order_by="name ASC")
        both = self.repo.list_by_type(user_id, "both", order_by="name ASC")
        return instructors + both

    def list_training_partners(self, user_id: int) -> list[dict]:
        """Get all friends who are training partners."""
        partners = self.repo.list_by_type(user_id, "training-partner", order_by="name ASC")
        both = self.repo.list_by_type(user_id, "both", order_by="name ASC")
        return partners + both

    def search_friends(self, user_id: int, query: str) -> list[dict]:
        """Search friends by name."""
        return self.repo.search(user_id, query)

    def update_friend(
        self,
        user_id: int,
        friend_id: int,
        name: str | None = None,
        friend_type: str | None = None,
        belt_rank: str | None = None,
        belt_stripes: int | None = None,
        instructor_certification: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        notes: str | None = None,
    ) -> dict | None:
        """Update a friend."""
        return self.repo.update(
            user_id=user_id,
            friend_id=friend_id,
            name=name,
            friend_type=friend_type,
            belt_rank=belt_rank,
            belt_stripes=belt_stripes,
            instructor_certification=instructor_certification,
            phone=phone,
            email=email,
            notes=notes,
        )

    def delete_friend(self, user_id: int, friend_id: int) -> bool:
        """Delete a friend."""
        return self.repo.delete(user_id, friend_id)

    def format_belt_display(self, friend: dict) -> str:
        """Format belt rank and stripes for display."""
        if not friend.get("belt_rank"):
            return "Unranked"

        rank = friend["belt_rank"].title()
        stripes = friend.get("belt_stripes", 0)

        if stripes > 0:
            return f"{rank} Belt ({stripes} stripe{'s' if stripes > 1 else ''})"
        return f"{rank} Belt"
