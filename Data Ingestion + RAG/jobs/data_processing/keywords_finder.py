import json
import yake
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class KeywordProcessorConfig:
    def __init__(self,
                 input_file: str,
                 output_file: str,
                 max_keywords: int = 5):
        self.input_file = input_file
        self.output_file = output_file
        self.max_keywords = max_keywords
        self.base_path = os.path.join('..', '..', 'data')

    @property
    def input_path(self) -> str:
        return os.path.join(self.base_path, self.input_file)

    @property
    def output_path(self) -> str:
        return os.path.join(self.base_path, self.output_file)


class KeywordProcessor:
    def __init__(self, config: KeywordProcessorConfig):
        """Initialize the keyword processor with configuration."""
        self.config = config
        self._initialize_components()

    def _initialize_components(self):
        """Initialize NLP components."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spaCy model...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

        # Initialize YAKE
        self.yake_extractor = yake.KeywordExtractor(
            lan="en",
            n=3,
            dedupLim=0.7,
            dedupFunc='seqm',
            windowsSize=3,
            top=20
        )

        # Initialize TF-IDF
        self.tfidf = TfidfVectorizer(
            ngram_range=(1, 3),
            stop_words='english',
            min_df=1
        )

    def load_articles(self) -> List[Dict[str, Any]]:
        """Load articles from JSON file."""
        try:
            with open(self.config.input_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading articles: {e}")
            return []

    def extract_keywords(self, text: str) -> List[Dict[str, float]]:
        """Extract keywords from text with scores."""
        # Get keywords from YAKE
        yake_keywords = {word: 1 / (score + 1e-5)
                         for word, score in self.yake_extractor.extract_keywords(text)}

        # Get TF-IDF scores
        tfidf_matrix = self.tfidf.fit_transform([text])
        feature_names = self.tfidf.get_feature_names_out()
        tfidf_scores = dict(zip(feature_names, tfidf_matrix.toarray()[0]))

        # Get named entities
        doc = self.nlp(text)
        entities = {ent.text.lower(): 1.0 for ent in doc.ents}

        # Combine scores
        keywords = []
        all_terms = set(yake_keywords.keys()) | set(tfidf_scores.keys()) | set(entities.keys())

        for term in all_terms:
            score = (
                    0.4 * yake_keywords.get(term, 0.0) +
                    0.4 * tfidf_scores.get(term, 0.0) +
                    0.2 * float(term.lower() in entities)
            )

            if score > 0:
                keywords.append({
                    "keyword": term,
                    "score": float(score)
                })

        # Sort by score and return top N
        keywords.sort(key=lambda x: x["score"], reverse=True)
        return keywords[:self.config.max_keywords]

    def process_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single article to add keywords."""
        try:
            processed_article = article.copy()

            if 'cleaned' in processed_article and 'content' in processed_article['cleaned']:
                # Extract keywords
                keywords = self.extract_keywords(processed_article['cleaned']['content'])

                # Add keywords to cleaned section
                processed_article['cleaned']['keywords'] = keywords

                # Update metadata
                if 'metadata' not in processed_article['cleaned']:
                    processed_article['cleaned']['metadata'] = {}

                processed_article['cleaned']['metadata'].update({
                    'keywords_extracted': True,
                    'keyword_extraction_date': datetime.now().isoformat(),
                    'num_keywords': len(keywords)
                })

            return processed_article
        except Exception as e:
            print(f"Error processing article: {e}")
            return article

    def save_articles(self, articles: List[Dict[str, Any]]) -> None:
        """Save processed articles to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.config.output_path), exist_ok=True)

            with open(self.config.output_path, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=4)

            print(f"Successfully saved processed articles to {self.config.output_file}")
        except Exception as e:
            print(f"Error saving articles: {e}")

    def run(self):
        """Run the keyword processing pipeline."""
        print("Starting keyword processing")

        # Load articles
        articles = self.load_articles()
        if not articles:
            print("No articles loaded")
            return

        # Process each article
        processed_articles = []
        total_articles = len(articles)

        for i, article in enumerate(articles, 1):
            processed_article = self.process_article(article)
            processed_articles.append(processed_article)
            print(f"Processed article {i}/{total_articles}")

        # Save results
        self.save_articles(processed_articles)
        print("Keyword processing completed")


if __name__ == "__main__":
    try:
        # Initialize configuration
        config = KeywordProcessorConfig(
            input_file="temp.json",
            output_file="temp2.json",
            max_keywords=5
        )

        # Initialize and run processor
        processor = KeywordProcessor(config)
        processor.run()

    except Exception as e:
        print(f"Error in main execution: {e}")