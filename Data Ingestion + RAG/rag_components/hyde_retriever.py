from typing import List, Dict
from langchain_community.vectorstores import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from pinecone import Pinecone as PineconeClient
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
from tqdm import tqdm


class HyDERetriever:
    def __init__(self, index_name: str = "articles", namespace: str = "Whats-Good"):
        """
        Initialize HyDE (Hypothetical Document Embeddings) Retriever
        """
        load_dotenv()

        self.pc = PineconeClient(api_key=os.getenv('PINECONE_API_KEY'))
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        self.llm = OllamaLLM(
            model="mistral",
            temperature=0.2
        )

        self.index_name = index_name
        self.namespace = namespace
        self.vector_store = Pinecone.from_existing_index(
            index_name=self.index_name,
            embedding=self.embeddings,
            namespace=self.namespace
        )

        self.setup_logging()
        self.setup_prompts()

    def setup_logging(self):
        """Setup logging configuration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        logging.basicConfig(
            filename=f'hyde_retriever_{timestamp}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def setup_prompts(self):
        """Setup prompts for HyDE"""
        self.hyde_prompt = PromptTemplate(
            input_variables=["brand_description", "categories"],
            template="""
            Given a brand's description and its category interests, generate a hypothetical ideal article 
            that would be perfectly relevant for this brand. The article should be concise (150 words max) 
            and match the brand's interests and category preferences. Do not use placeholders like [Brand Name].
            Use 'the company' or 'this innovative startup' instead.

            Brand Description: {brand_description}
            Category Interests: {categories}

            Generate a concise article (exactly 150 words) that would be highly relevant for this brand, 
            focusing on their key interests and industry categories. Make it informative and specific.

            Hypothetical Article:
            """
        )

        self.multi_hyde_prompt = PromptTemplate(
            input_variables=["brand_description", "categories", "aspect"],
            template="""
            Given a brand's description and category interests, generate a hypothetical ideal article 
            focusing specifically on the following aspect of their business. Do not use placeholders 
            like [Brand Name]. Use 'the company' or 'this innovative startup' instead.

            Brand Description: {brand_description}
            Category Interests: {categories}
            Focus Aspect: {aspect}

            Generate a concise article (exactly 150 words) that focuses specifically on the mentioned aspect
            while considering their category interests. Make it informative and specific.

            Hypothetical Article:
            """
        )

    def truncate_to_word_limit(self, text: str, word_limit: int = 150) -> str:
        """
        Truncate text to specified word limit at sentence boundary
        """
        # Remove any placeholder text
        text = text.replace("[Brand Name]", "the company")

        # Split into title and content if there's a title
        if "Title:" in text:
            title, content = text.split("\n", 1)
            main_text = content.strip()
        else:
            title = ""
            main_text = text.strip()

        # Count words in main text
        words = main_text.split()
        if len(words) <= word_limit:
            return text if not title else f"{title}\n{main_text}"

        # Find last complete sentence within word limit
        truncated = ' '.join(words[:word_limit])
        last_period = truncated.rfind('.')

        if last_period > 0:
            truncated = truncated[:last_period + 1]
        else:
            truncated = truncated + '.'

        return f"{title}\n{truncated}" if title else truncated

    def generate_hypothetical_document(self,
                                       brand_description: str,
                                       category_weights: Dict[str, float]) -> str:
        """
        Generate a hypothetical ideal document based on brand description
        """
        try:
            categories_str = ", ".join(
                [f"{cat} (importance: {weight})"
                 for cat, weight in category_weights.items()]
            )

            print("\nDebug - Generating hypothetical document...")
            response = self.llm.invoke(
                self.hyde_prompt.format(
                    brand_description=brand_description,
                    categories=categories_str
                )
            )

            # Clean and truncate response
            document = str(response).strip()
            truncated_document = self.truncate_to_word_limit(document)

            print(f"\nDebug - Document word count: {len(truncated_document.split())}")
            return truncated_document

        except Exception as e:
            print(f"\nDebug - Error: {str(e)}")
            logging.error(f"Error generating document: {str(e)}")
            return ""

    def generate_multi_aspect_documents(self,
                                        brand_description: str,
                                        category_weights: Dict[str, float]) -> List[str]:
        """
        Generate multiple hypothetical documents focusing on different aspects
        """
        aspects = [
            "core technology and innovation",
            "market positioning and business strategy",
            "industry impact and applications",
            "future growth potential"
        ]

        documents = []
        categories_str = ", ".join(
            [f"{cat} (importance: {weight})"
             for cat, weight in category_weights.items()]
        )

        print(f"\nDebug - Generating {len(aspects)} aspect-specific documents...")

        for aspect in tqdm(aspects, desc="Generating documents"):
            try:
                response = self.llm.invoke(
                    self.multi_hyde_prompt.format(
                        brand_description=brand_description,
                        categories=categories_str,
                        aspect=aspect
                    )
                )

                document = str(response).strip()
                truncated_document = self.truncate_to_word_limit(document)

                if truncated_document:
                    documents.append(truncated_document)
                    print(f"\nDebug - Generated document for {aspect}")
                    print(f"Word count: {len(truncated_document.split())}")

            except Exception as e:
                print(f"\nDebug - Error generating document for {aspect}: {str(e)}")
                logging.error(f"Error generating document for aspect '{aspect}': {str(e)}")
                continue

        return documents


def main():
    """Example usage"""
    try:
        retriever = HyDERetriever()

        # Test brand profile
        brand_description = """
        We are a healthcare technology startup focusing on developing AI-powered diagnostic tools.
        Our main focus is on improving patient care through innovative technology solutions.
        We also provide data analytics services to healthcare providers for better decision making.
        """

        category_weights = {
            "healthcare": 1.0,
            "technology": 0.9,
            "science": 0.7,
            "business": 0.5
        }

        # Test single document generation
        print("\nTesting single document generation...")
        single_doc = retriever.generate_hypothetical_document(
            brand_description=brand_description,
            category_weights=category_weights
        )
        print("\nSingle Document:")
        print(single_doc)

        # Test multi-aspect document generation
        print("\nTesting multi-aspect document generation...")
        multi_docs = retriever.generate_multi_aspect_documents(
            brand_description=brand_description,
            category_weights=category_weights
        )

        print(f"\nGenerated {len(multi_docs)} aspect-specific documents:")
        for i, doc in enumerate(multi_docs, 1):
            print(f"\nDocument {i}:")
            print(doc)
            print("-" * 50)

    except Exception as e:
        print(f"Error in main: {str(e)}")


if __name__ == "__main__":
    main()