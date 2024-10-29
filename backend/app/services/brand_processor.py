from typing import Optional
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.brand import Brand

class ProcessedBrandProfile(BaseModel):
    """Simple, focused structure for processed brand information"""
    processed_brand_name: str = Field(
        description="Clean, professional brand name",
        max_length=50
    )
    processed_industry: str = Field(
        description="Main industry and focus area combined",
        max_length=100
    )
    processed_target_audience: str = Field(
        description="Clear target audience description with key characteristics",
        max_length=150
    )
    processed_brand_values: str = Field(
        description="Core brand values and unique selling points",
        max_length=200
    )
    processed_social_presence: Optional[str] = Field(
        description="Social media strategy summary, if provided",
        max_length=150,
        default="Not provided - Please add your social media presence details."
    )

class BrandProcessor:
    def __init__(self, model_name: str = "mistral"):
        self.llm = OllamaLLM(model=model_name)
        self.parser = PydanticOutputParser(pydantic_object=ProcessedBrandProfile)

    async def process_brand_responses(self, brand_id: int, db: AsyncSession) -> Optional[Brand]:
        query = select(Brand).where(and_(Brand.id == brand_id))
        result = await db.execute(query)
        brand = result.scalar_one_or_none()

        if not brand:
            return None

        try:
            # Process only if we have the basic required information
            if not all([brand.raw_brand_name, brand.raw_industry_focus,
                       brand.raw_target_audience, brand.raw_unique_value]):
                raise ValueError("Missing required brand information")

            prompt = """Analyze and refine this brand information into a professional format.
            Only work with the information provided - do not make assumptions or add details.
            If any information is unclear or missing, indicate it needs to be provided.

            Raw Information:
            Brand Name: {raw_brand_name}
            Industry & Focus: {raw_industry_focus}
            Target Audience: {raw_target_audience}
            Unique Value & Core Values: {raw_unique_value}
            Social Platforms: {raw_social_platforms}
            Successful Content: {raw_successful_content}

            Requirements:
            1. Keep the refined content clear and concise
            2. Use professional, industry-standard terminology
            3. For missing or unclear information, use placeholder text indicating it needs to be provided
            4. Format social media information only if it's provided
            5. Focus on accuracy over completeness

            {format_instructions}

            Refined profile:"""

            formatted_prompt = PromptTemplate(
                template=prompt,
                input_variables=[
                    "raw_brand_name",
                    "raw_industry_focus",
                    "raw_target_audience",
                    "raw_unique_value",
                    "raw_social_platforms",
                    "raw_successful_content"
                ],
                partial_variables={"format_instructions": self.parser.get_format_instructions()}
            )

            # Process with placeholder handling
            result = await self.llm.ainvoke(
                formatted_prompt.format(
                    raw_brand_name=brand.raw_brand_name or "[Brand name needed]",
                    raw_industry_focus=brand.raw_industry_focus or "[Industry focus needed]",
                    raw_target_audience=brand.raw_target_audience or "[Target audience needed]",
                    raw_unique_value=brand.raw_unique_value or "[Brand values needed]",
                    raw_social_platforms=brand.raw_social_platforms or "Not provided",
                    raw_successful_content=brand.raw_successful_content or "No content history provided"
                )
            )

            processed = self.parser.parse(result)

            # Update brand with processed information
            brand.processed_brand_name = processed.processed_brand_name
            brand.processed_industry = processed.processed_industry
            brand.processed_target_audience = processed.processed_target_audience
            brand.processed_brand_values = processed.processed_brand_values
            brand.processed_social_presence = (
                processed.processed_social_presence
                if brand.raw_social_platforms
                else "Not provided - Add your social media strategy here."
            )

            await db.commit()
            await db.refresh(brand)
            return brand

        except Exception as e:
            print(f"Error processing brand responses: {e}")
            await db.rollback()
            return None