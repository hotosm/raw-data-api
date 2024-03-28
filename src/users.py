# Third party imports
from pydantic import BaseModel

# Reader imports
from postgres import AsyncPostgres


class UserUpdate(BaseModel):
    osm_id: int
    role: int


class Users:
    """
    Users class provides CRUD operations for interacting with the 'users' table in the database.

    Methods:
    - create_user(osm_id: int, role: int) -> Dict[str, Any]: Inserts a new user into the database.
    - read_user(osm_id: int) -> Dict[str, Any]: Retrieves user information based on the given osm_id.
    - update_user(osm_id: int, update_data: UserUpdate) -> Dict[str, Any]: Updates user information based on the given osm_id.
    - delete_user(osm_id: int) -> Dict[str, Any]: Deletes a user based on the given osm_id.
    - read_users(skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]: Retrieves a list of users with optional pagination.

    Usage:
    users = Users()
    """

    def __init__(self) -> None:
        """
        Initializes an instance of the Users class, connecting to the database.
        """
        dbdict = get_db_connection_params()
        self.db = AsyncPostgres(dbdict)
        self.db.establish_pool()

    async def create_user(self, osm_id, role):
        """
        Inserts a new user into the 'users' table and returns the created user's osm_id.

        Args:
        - osm_id (int): The OSM ID of the new user.
        - role (int): The role of the new user.

        Returns:
        - Dict[str, Any]: A dictionary containing the osm_id of the newly created user.

        Raises:
        - HTTPException: If the user creation fails.
        """
        query = "INSERT INTO users (osm_id, role) VALUES (%s, %s) RETURNING osm_id;"
        await self.db.execute(query, osm_id, role)
        new_osm_id = await self.db.fetchval(query, osm_id, role)
        return {"osm_id": new_osm_id}

    async def read_user(self, osm_id):
        """
        Retrieves user information based on the given osm_id.

        Args:
        - osm_id (int): The OSM ID of the user to retrieve.

        Returns:
        - Dict[str, Any]: A dictionary containing user information if the user is found.
                        If the user is not found, returns a default user with 'role' set to 3.

        Raises:
        - HTTPException: If there's an issue with the database query.
        """
        query = "SELECT * FROM users WHERE osm_id = %s;"
        result = await self.db.fetchrow(query, osm_id)
        if result:
            return dict(result)
        else:
            # Return a default user with 'role' set to 3 if the user is not found
            return {"osm_id": osm_id, "role": 3}

    async def update_user(self, osm_id, update_data):
        """
        Updates user information based on the given osm_id.

        Args:
        - osm_id (int): The OSM ID of the user to update.
        - update_data (UserUpdate): The data to update for the user.

        Returns:
        - Dict[str, Any]: A dictionary containing the updated user information.

        Raises:
        - HTTPException: If the user with the given osm_id is not found.
        """
        query = "UPDATE users SET osm_id = %s, role = %s WHERE osm_id = %s RETURNING *;"
        await self.db.execute(query, update_data.osm_id, update_data.role, osm_id)
        updated_user = await self.db.fetchrow(
            query, update_data.osm_id, update_data.role, osm_id
        )
        if updated_user:
            return dict(updated_user)
        raise HTTPException(status_code=404, detail="User not found")

    async def delete_user(self, osm_id):
        """
        Deletes a user based on the given osm_id.

        Args:
        - osm_id (int): The OSM ID of the user to delete.

        Returns:
        - Dict[str, Any]: A dictionary containing the deleted user information.

        Raises:
        - HTTPException: If the user with the given osm_id is not found.
        """
        query = "DELETE FROM users WHERE osm_id = %s RETURNING *;"
        await self.db.execute(query, osm_id)
        deleted_user = await self.db.fetchrow(query, osm_id)
        if deleted_user:
            return dict(deleted_user)
        raise HTTPException(status_code=404, detail="User not found")

    async def read_users(self, skip=0, limit=10):
        """
        Retrieves a list of users with optional pagination.

        Args:
        - skip (int): The number of users to skip (for pagination).
        - limit (int): The maximum number of users to retrieve (for pagination).

        Returns:
        - List[Dict[str, Any]]: A list of dictionaries containing user information.
        """
        query = "SELECT * FROM users OFFSET %s LIMIT %s;"
        users_list = await self.db.fetch(query, skip, limit)
        return [dict(user) for user in users_list]
