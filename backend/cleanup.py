import asyncio
from sqlalchemy import delete
from app.database import async_session_maker
from app.models import User

async def main():
    async with async_session_maker() as session:
        # Delete everyone except 'admin'
        # Depending on if there are foreign keys, we might need to delete submissions first, or cascade handles it.
        # Let's try simple delete on User, but if it fails we might need to delete other dependent data.
        try:
            result = await session.execute(delete(User).where(User.username != 'admin'))
            await session.commit()
            print("Deleted mock users")
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
