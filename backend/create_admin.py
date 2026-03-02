import asyncio
from app.database import AsyncSessionLocal
from app.models import User
from app.auth import hash_password

async def insert_admin():
    async with AsyncSessionLocal() as db:
        admin_user = User(
            username="admin",
            email="admin@promptrank.com",
            password_hash=hash_password("admin"),
            role="admin",
            rating=1500
        )
        db.add(admin_user)
        try:
            await db.commit()
            print("Admin user created successfully")
        except Exception as e:
            print("Error creating admin user:", e)

if __name__ == "__main__":
    asyncio.run(insert_admin())
