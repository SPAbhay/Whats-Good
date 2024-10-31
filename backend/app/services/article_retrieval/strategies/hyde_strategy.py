from typing import List, Optional
import logging
from datetime import datetime
from langchain_community.vectorstores import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from pinecone import Pinecone as PineconeClient
import os
from dotenv import load_dotenv

from ..schemas import BrandContext, PineconeResult


class HyDEStrategy:
    def __init__(self, index_name: str = "whats-good-articles", namespace: str = "whats-good"):
        self.hyde_prompt = None
        self.logger = None
        load_dotenv()

        # Initialize base components
        self.pc = PineconeClient(api_key=os.getenv('PINECONE_API_KEY'))
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        # self.llm = OllamaLLM(model="mistral", temperature=0.2)
        self.llm = OpenAI(model='gpt-3.5-turbo-instruct', api_key=os.getenv('OPENAI_API_KEY'), temperature=0.2)

        self.index_name = index_name
        self.namespace = namespace
        # Initialize vector store
        self.vector_store = Pinecone.from_existing_index(
            index_name=self.index_name,
            embedding=self.embeddings,
            namespace=self.namespace
        )

        # Setup logging
        self.setup_logging()
        self.setup_prompts()

    def setup_logging(self):
        """Configure logging for the HyDE strategy"""
        self.logger = logging.getLogger('hyde_strategy')
        if not self.logger.handlers:
            handler = logging.FileHandler(f'hyde_strategy_{datetime.now().strftime("%Y%m%d")}.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def setup_prompts(self):
        """Initialize prompts for HyDE"""
        self.hyde_prompt = PromptTemplate(
            template="""Given a brand's context, generate a hypothetical article snippet that would be 
            highly relevant for this brand. Focus on their industry expertise and values.

            Brand Context:
            Industry & Focus: {industry}
            Core Values & USPs: {values}
            Target Audience: {audience}

            Requirements:
            1. Keep it focused on industry trends and innovations
            2. Align with the brand's values and approach
            3. Make it relevant for their target audience
            4. Write 2-3 concise paragraphs (max 200 words)
            5. Be specific and use industry terminology
            6. Focus on actionable insights and clear value propositions

            Generate a relevant article snippet:""",
            input_variables=["industry", "values", "audience"]
        )

    async def retrieve(self, brand_context: BrandContext, limit: int = 5) -> List[PineconeResult]:
        """
        Retrieve relevant article IDs using HyDE strategy
        """
        try:
            # Generate hypothetical document
            self.logger.info(f"Generating hypothetical document for brand {brand_context.brand_id}")
            hypo_doc = await self._generate_hypothetical_document(brand_context)

            if not hypo_doc:
                self.logger.warning(f"Failed to generate hypothetical document for brand {brand_context.brand_id}")
                return []

            # Get similar documents from vector store
            self.logger.info("Searching for similar articles")
            results = await self._search_similar_articles(hypo_doc, limit * 2)  # Get extra for filtering

            # Process and return results
            return self._process_results(results[:limit])

        except Exception as e:
            self.logger.error(f"Error in HyDE retrieval: {str(e)}")
            return []

    async def _generate_hypothetical_document(self, brand_context: BrandContext) -> Optional[str]:
        """Generate a hypothetical document based on brand context"""
        try:
            response = await self.llm.ainvoke(
                self.hyde_prompt.format(
                    industry=brand_context.industry,
                    values=brand_context.values,
                    audience=brand_context.audience
                )
            )

            # Clean and validate response
            doc = str(response).strip()
            if len(doc.split()) < 20:  # Basic validation
                self.logger.warning("Generated document too short, might be low quality")
                return None

            return doc

        except Exception as e:
            self.logger.error(f"Error generating hypothetical document: {str(e)}")
            return None

    async def _search_similar_articles(self, hypothetical_doc: str, limit: int) -> List[dict]:
        """Search for similar articles in vector store"""
        try:
            # Debug log the document
            self.logger.info(f"Searching with document: {hypothetical_doc[:200]}...")

            # Get embeddings for the hypothetical document
            vector = self.embeddings.embed_query(hypothetical_doc)
            self.logger.info(f"Generated embedding vector length: {len(vector)}")

            # Search in Pinecone
            index = self.pc.Index(self.index_name)

            # Debug log Pinecone index stats
            stats = index.describe_index_stats()
            self.logger.info(f"Pinecone index stats: {stats}")

            results = index.query(
                namespace=self.namespace,
                vector=vector,
                top_k=limit,
                include_metadata=True
            )

            self.logger.info(f"Pinecone search results: {results.matches}")
            return results.matches

        except Exception as e:
            self.logger.error(f"Error in vector search: {str(e)}")
            return []

    def _process_results(self, raw_results: List[dict]) -> List[PineconeResult]:
        """Process raw Pinecone results into structured format"""
        processed_results = []

        for result in raw_results:
            try:
                processed_results.append(
                    PineconeResult(
                        article_id=result['id'],
                        score=float(result['score']),
                        strategy="hyde"
                    )
                )
            except Exception as e:
                self.logger.error(f"Error processing result {result['id']}: {str(e)}")
                continue

        return processed_results

    async def cleanup(self):
        """Cleanup resources if needed"""
        try:
            # Add any cleanup code here
            pass
        except Exception as e:
            self.logger.error(f"Error in cleanup: {str(e)}")