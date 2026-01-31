"""Repository for gym data access."""
from typing import List, Dict, Any, Optional
from rivaflow.db.database import get_connection, execute_insert, convert_query


class GymRepository:
    """Data access layer for gyms."""

    @staticmethod
    def create(
        name: str,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: str = "Australia",
        address: Optional[str] = None,
        website: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        head_coach: Optional[str] = None,
        verified: bool = False,
        added_by_user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a new gym."""
        with get_connection() as conn:
            cursor = conn.cursor()
            gym_id = execute_insert(
                cursor,
                convert_query("""
                INSERT INTO gyms
                (name, city, state, country, address, website, email, phone, head_coach, verified, added_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """),
                (name, city, state, country, address, website, email, phone, head_coach, verified, added_by_user_id),
            )
            conn.commit()

            cursor.execute(convert_query("SELECT * FROM gyms WHERE id = ?"), (gym_id,))
            result = cursor.fetchone()

            if hasattr(result, 'keys'):
                return dict(result)
            else:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))

    @staticmethod
    def get_by_id(gym_id: int) -> Optional[Dict[str, Any]]:
        """Get a gym by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("SELECT * FROM gyms WHERE id = ?"), (gym_id,))
            result = cursor.fetchone()

            if not result:
                return None

            if hasattr(result, 'keys'):
                return dict(result)
            else:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))

    @staticmethod
    def list_all(verified_only: bool = False) -> List[Dict[str, Any]]:
        """List all gyms."""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            if verified_only:
                cursor.execute(convert_query(
                    "SELECT * FROM gyms WHERE verified = TRUE ORDER BY name"
                ))
            else:
                cursor.execute(convert_query(
                    "SELECT * FROM gyms ORDER BY verified DESC, name"
                ))
            
            results = cursor.fetchall()
            
            if not results:
                return []

            if hasattr(results[0], 'keys'):
                return [dict(row) for row in results]
            else:
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in results]

    @staticmethod
    def search(query: str, verified_only: bool = False) -> List[Dict[str, Any]]:
        """Search gyms by name or location."""
        with get_connection() as conn:
            cursor = conn.cursor()
            search_term = f"%{query}%"
            
            if verified_only:
                cursor.execute(convert_query("""
                    SELECT * FROM gyms
                    WHERE verified = TRUE
                    AND (name LIKE ? OR city LIKE ? OR state LIKE ?)
                    ORDER BY name
                    LIMIT 50
                """), (search_term, search_term, search_term))
            else:
                cursor.execute(convert_query("""
                    SELECT * FROM gyms 
                    WHERE name LIKE ? OR city LIKE ? OR state LIKE ?
                    ORDER BY verified DESC, name
                    LIMIT 50
                """), (search_term, search_term, search_term))
            
            results = cursor.fetchall()
            
            if not results:
                return []

            if hasattr(results[0], 'keys'):
                return [dict(row) for row in results]
            else:
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in results]

    @staticmethod
    def update(gym_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a gym."""
        allowed_fields = {'name', 'city', 'state', 'country', 'address', 'website', 'email', 'phone', 'head_coach', 'verified'}
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_fields:
            return GymRepository.get_by_id(gym_id)

        with get_connection() as conn:
            cursor = conn.cursor()
            
            set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
            values = list(update_fields.values())
            values.append(gym_id)

            cursor.execute(
                convert_query(f"""
                UPDATE gyms 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """),
                values,
            )
            conn.commit()

            return GymRepository.get_by_id(gym_id)

    @staticmethod
    def delete(gym_id: int) -> bool:
        """Delete a gym."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("DELETE FROM gyms WHERE id = ?"), (gym_id,))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def get_pending_gyms() -> List[Dict[str, Any]]:
        """Get all unverified (user-added) gyms."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("""
                SELECT g.*, u.first_name, u.last_name, u.email
                FROM gyms g
                LEFT JOIN users u ON g.added_by_user_id = u.id
                WHERE g.verified = FALSE
                ORDER BY g.created_at DESC
            """))
            
            results = cursor.fetchall()
            
            if not results:
                return []

            if hasattr(results[0], 'keys'):
                return [dict(row) for row in results]
            else:
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in results]

    @staticmethod
    def merge_gyms(source_gym_id: int, target_gym_id: int) -> bool:
        """
        Merge two gyms by updating all references from source to target.
        Then delete the source gym.

        This operation is atomic - all changes are committed together or rolled back on error.
        The context manager ensures automatic transaction handling:
        - Success: All changes are committed
        - Failure: All changes are rolled back

        Args:
            source_gym_id: ID of the gym to merge (will be deleted)
            target_gym_id: ID of the gym to merge into (will remain)

        Returns:
            bool: True if merge completed successfully

        Raises:
            Exception: If database operations fail (transaction will be rolled back)
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Update users with primary_gym_id = source to target
                cursor.execute(convert_query("""
                    UPDATE users SET primary_gym_id = ? WHERE primary_gym_id = ?
                """), (target_gym_id, source_gym_id))

                # Delete the source gym
                cursor.execute(convert_query("DELETE FROM gyms WHERE id = ?"), (source_gym_id,))

                # Explicit commit (also happens automatically on context exit)
                conn.commit()
                return True
            except Exception as e:
                # Rollback happens automatically via context manager
                # Re-raise to let caller handle the error
                raise Exception(f"Gym merge failed: {str(e)}") from e
