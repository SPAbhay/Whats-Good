from typing import List
import logging
from langchain_community.vectorstores import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from pinecone import Pinecone as PineconeClient
import os
from dotenv import load_dotenv

from ..schemas import BrandContext, PineconeResult


class SelfQueryStrategy:
    def __init__(self, index_name: str = "whats-good-articles", namespace: str = "whats-good"):
        load_dotenv()

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        # self.llm = OllamaLLM(model="mistral", temperature=0.2)
        self.llm = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            temperature=0.2,
            model='gpt-3.5-turbo-instruct'
        )
        self.pc = PineconeClient(api_key=os.getenv('PINECONE_API_KEY'))

        self.vector_store = Pinecone.from_existing_index(
            index_name=index_name,
            embedding=self.embeddings,
            namespace=namespace
        )

        self.query_prompt = PromptTemplate(
            template="""Convert this brand context into a focused search query.
            Make it specific to finding relevant industry content.

            Brand Industry: {industry}
            Brand Values: {values}
            Target Audience: {audience}

            Generate a clear, focused search query that will find relevant articles.
            Keep it under 30 words and focus on key industry terms.

            Query:""",
            input_variables=["industry", "values", "audience"]
        )

        self.index_name = index_name
        self.namespace = namespace

    async def retrieve(self, brand_context: BrandContext, limit: int = 5) -> List[PineconeResult]:
        try:
            # Generate structured query
            query = await self._generate_query(brand_context)

            # Get vector for query
            query_vector = self.embeddings.embed_query(query)

            # Search in Pinecone
            index = self.pc.Index(self.index_name)
            results = index.query(
                namespace=self.namespace,
                vector=query_vector,
                top_k=limit,
                include_metadata=True
            )

            # Process results
            return [
                PineconeResult(
                    article_id=match.id,
                    score=float(match.score),
                    strategy="self_query"
                )
                for match in results.matches
            ]

        except Exception as e:
            logging.error(f"Self-query retrieval error: {str(e)}")
            return []

    async def _generate_query(self, brand_context: BrandContext) -> str:
        try:
            response = await self.llm.ainvoke(
                self.query_prompt.format(
                    industry=brand_context.industry,
                    values=brand_context.values,
                    audience=brand_context.audience
                )
            )
            return str(response).strip()
        except Exception as e:
            logging.error(f"Query generation error: {str(e)}")
            return brand_context.industry  # Fallback to basic industry query