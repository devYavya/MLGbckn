"""
MongoDB Database Configuration for Multi-tenant SaaS
"""
from motor.motor_asyncio import AsyncIOMotorClient
from src.utils.config import get_settings

settings = get_settings()

# MongoDB Connection
client = AsyncIOMotorClient(settings.MONGODB_URI)

# Main SaaS Database
saas_db = client.agra_heritage_saas

# Collections
super_admins_collection = saas_db.super_admins
companies_collection = saas_db.companies
pricing_plans_collection = saas_db.pricing_plans
users_collection = saas_db.users

# Indexes for performance and data integrity
async def create_indexes():
    """Create necessary indexes for optimal performance"""
    
    # Super Admins indexes
    await super_admins_collection.create_index("email", unique=True)
    await super_admins_collection.create_index("username", unique=True)
    
    # Companies indexes
    await companies_collection.create_index("email", unique=True)
    await companies_collection.create_index("name")
    await companies_collection.create_index("status")
    await companies_collection.create_index("subscription_plan_id")
    await companies_collection.create_index("created_at")
    
    # Users indexes (Critical for multi-tenant isolation)
    await users_collection.create_index([("email", 1)], unique=True)
    await users_collection.create_index([("username", 1), ("company_id", 1)], unique=True)
    await users_collection.create_index("company_id")  # Critical for tenant isolation
    await users_collection.create_index([("company_id", 1), ("role", 1)])
    await users_collection.create_index([("company_id", 1), ("is_active", 1)])
    
    # Pricing plans indexes
    await pricing_plans_collection.create_index("name", unique=True)
    await pricing_plans_collection.create_index("is_active")
    
    print("Database indexes created successfully")

# Utility functions for database operations
async def get_company_user_count(company_id: str) -> int:
    """Get current user count for a company"""
    return await users_collection.count_documents({
        "company_id": company_id,
        "is_active": True
    })

async def update_company_user_count(company_id: str):
    """Update the current_user_count field for a company"""
    count = await get_company_user_count(company_id)
    await companies_collection.update_one(
        {"id": company_id},
        {"$set": {"current_user_count": count}}
    )

# Company-specific database operations
class CompanyDatabase:
    """Handles company-scoped database operations"""
    
    def __init__(self, company_id: str):
        self.company_id = company_id
    
    async def get_users(self, skip: int = 0, limit: int = 100):
        """Get users for this company only"""
        cursor = users_collection.find(
            {"company_id": self.company_id}
        ).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_user_by_id(self, user_id: str):
        """Get a user by ID, scoped to company"""
        return await users_collection.find_one({
            "id": user_id,
            "company_id": self.company_id
        })
    
    async def get_user_by_email(self, email: str):
        """Get a user by email, scoped to company"""
        return await users_collection.find_one({
            "email": email,
            "company_id": self.company_id
        })
    
    async def create_user(self, user_data: dict):
        """Create a user for this company"""
        user_data["company_id"] = self.company_id
        result = await users_collection.insert_one(user_data)
        await update_company_user_count(self.company_id)
        return result
    
    async def update_user(self, user_id: str, update_data: dict):
        """Update a user, scoped to company"""
        result = await users_collection.update_one(
            {"id": user_id, "company_id": self.company_id},
            {"$set": update_data}
        )
        return result
    
    async def delete_user(self, user_id: str):
        """Soft delete a user (set inactive)"""
        result = await users_collection.update_one(
            {"id": user_id, "company_id": self.company_id},
            {"$set": {"is_active": False}}
        )
        await update_company_user_count(self.company_id)
        return result

# Initialize database setup
async def init_database():
    """Initialize database with indexes and default data"""
    await create_indexes()
    
    # Create default pricing plans if they don't exist
    existing_plans = await pricing_plans_collection.count_documents({})
    if existing_plans == 0:
        default_plans = [
            {
                "id": "plan_basic",
                "name": "Basic Plan",
                "description": "Perfect for small teams",
                "price": 29.99,
                "currency": "USD",
                "billing_cycle": "monthly",
                "max_users": 10,
                "features": ["User Management", "Basic Analytics", "Email Support"],
                "is_active": True
            },
            {
                "id": "plan_pro",
                "name": "Pro Plan", 
                "description": "For growing businesses",
                "price": 79.99,
                "currency": "USD",
                "billing_cycle": "monthly",
                "max_users": 50,
                "features": ["User Management", "Advanced Analytics", "Priority Support", "API Access"],
                "is_active": True
            },
            {
                "id": "plan_enterprise",
                "name": "Enterprise Plan",
                "description": "For large organizations",
                "price": 199.99,
                "currency": "USD", 
                "billing_cycle": "monthly",
                "max_users": None,  # Unlimited
                "features": ["User Management", "Advanced Analytics", "24/7 Support", "API Access", "Custom Integrations"],
                "is_active": True
            }
        ]
        
        await pricing_plans_collection.insert_many(default_plans)
        print("Default pricing plans created")
