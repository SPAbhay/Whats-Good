import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from .base_class import AsyncSessionLocal
from ..models.brand import Brand
from ..models.user import User
from ..models.article import Article

async def seed_test_data():
    async with AsyncSessionLocal() as session:
        try:
            # Create brands
            brands = [
                Brand(brand_identity="Tech Brand"),
                Brand(brand_identity="Fashion Brand")
            ]
            session.add_all(brands)
            await session.flush()
            print("Created brands:")
            for brand in brands:
                print(f"- {brand.brand_identity} (ID: {brand.id})")

            # Create test user
            user = User(
                email="test@example.com",
                hashed_password="test_password_hashed"
            )
            session.add(user)
            await session.flush()
            print(f"\nCreated user: {user.email}")

            # Create articles
            articles = [
                Article(
                    content="This is a tech article about AI and its impact on future technology. The field of artificial intelligence has seen remarkable progress...",
                    summarized_content="Article about AI's impact on technology",
                    source_url="https://tech.example.com/ai-article",
                    brand_id=brands[0].id,
                    insights={
                        "youtube": [
                            {"title": "AI Future", "views": 10000, "engagement_rate": 0.85},
                            {"title": "Tech Trends", "views": 5000, "engagement_rate": 0.75}
                        ],
                        "reddit": [
                            {"title": "AI Discussion", "upvotes": 500, "comments": 100},
                            {"title": "Tech News", "upvotes": 300, "comments": 50}
                        ]
                    }
                ),
                Article(
                    content="Fashion trends for 2024 show a shift towards sustainable and ethical fashion. Consumers are increasingly conscious...",
                    summarized_content="2024 Fashion trends focusing on sustainability",
                    source_url="https://fashion.example.com/trends-2024",
                    brand_id=brands[1].id,
                    insights={
                        "youtube": [
                            {"title": "Fashion Trends", "views": 15000, "engagement_rate": 0.9},
                            {"title": "Sustainable Fashion", "views": 8000, "engagement_rate": 0.8}
                        ],
                        "reddit": [
                            {"title": "Fashion Discussion", "upvotes": 700, "comments": 150},
                            {"title": "Style Tips", "upvotes": 400, "comments": 80}
                        ]
                    }
                )
            ]
            session.add_all(articles)
            await session.commit()
            print("\nCreated articles:")
            for article in articles:
                print(f"- ID: {article.id}, Brand ID: {article.brand_id}")

            print("\nAll test data created successfully!")

        except Exception as e:
            print(f"Error seeding data: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(seed_test_data())