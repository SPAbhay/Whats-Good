import json
from typing import List, Dict, Optional
from datetime import datetime
import spacy
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from dotenv import load_dotenv

load_dotenv()


class ArticleProcessorConfig:
    def __init__(self, input_file: str, output_file: str, model_name: str = "en_core_web_sm"):
        self.input_file = input_file
        self.output_file = output_file
        self.model_name = model_name

        # Refined cleanup patterns to be more specific
        self.cleanup_patterns = {
            # Only remove standalone advertisement markers
            'advertisement': r'(?i)^\s*ADVERTISEMENT\s*$\n?',

            # Only remove specific call-to-actions
            'call_to_action': r'(?i)(Do you want.*?Sign up here:.*?\n|More information here\.|Explore More.*?\n)',

            # Remove specific newsletter/subscription blocks
            'subscription': r'(?i)(Subscribe to our.*?\n|Sign up for our.*?\n)',

            # Remove only full promotional lines
            'promotional': r'(?i)(^TechCrunch\+ is.*?subscription.*?\n)',

            # Remove empty lines but preserve paragraph structure
            'empty_lines': r'\n{3,}',

            # Only remove standalone URLs
            'urls': r'(?i)^\s*https?://\S+\s*$\n?'
        }

        # Content that should be preserved even if matching patterns
        self.preserve_phrases = [
            'Twitter Blue',
            'Twitter API',
            'Facebook Groups',
            'Instagram Reels',
            'social media',
            'social network'
        ]

class ArticleProcessor:
    def __init__(self, config: ArticleProcessorConfig):
        self.config = config
        self.nlp = spacy.load(self.config.model_name)

    def read_articles(self) -> List[Dict]:
        input_file_path = os.path.join('..', '..', 'data/', self.config.input_file)
        try:
            with open(input_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading file {input_file_path}: {e}")
            return []

    def clean_text(self, text: str) -> str:
        """
        Enhanced text cleaning that preserves important content
        """
        if not text:
            return ""

        # Store original text
        clean_text = text

        # Preserve important phrases by temporarily replacing them
        preserved = {}
        for i, phrase in enumerate(self.config.preserve_phrases):
            if phrase.lower() in clean_text.lower():
                marker = f"PRESERVED_CONTENT_{i}"
                clean_text = re.sub(
                    re.escape(phrase),
                    marker,
                    clean_text,
                    flags=re.IGNORECASE
                )
                preserved[marker] = phrase

        # Apply cleanup patterns
        for pattern in self.config.cleanup_patterns.values():
            clean_text = re.sub(pattern, '\n', clean_text)

        # Normalize whitespace while preserving paragraph structure
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = re.sub(r'\n\s+\n', '\n\n', clean_text)

        # Restore preserved phrases
        for marker, phrase in preserved.items():
            clean_text = clean_text.replace(marker, phrase)

        return clean_text.strip()

    def process_single_article(self, article: Dict) -> Dict:
        """
        Process a single article with enhanced cleaning
        """
        try:
            original_title = article.get('title', '')
            original_content = article.get('content', '')

            # Clean content while preserving structure
            clean_title = self.clean_text(original_title)
            clean_content = self.clean_text(original_content)

            # Process author field
            author = article.get('author', [])
            if isinstance(author, list):
                author = [a.strip() for a in author if a.strip()]

            # Print compression ratio if content is significantly shortened
            if original_content and len(clean_content) / len(original_content) < 0.95:
                print(len(clean_content) / len(original_content))
                print(clean_title)

            # Construct the processed article output
            return {
                'original': {
                    'title': original_title,
                    'content': original_content
                },
                'cleaned': {
                    'title': clean_title,
                    'content': clean_content,
                    'metadata': {
                        'original_length': len(original_content),
                        'cleaned_length': len(clean_content),
                        'processing_date': datetime.now().isoformat(),
                        'has_author': bool(author),
                        'word_count': len(clean_content.split()),
                        'compression_ratio': len(clean_content) / len(original_content) if original_content else 0,
                        'paragraphs': len([p for p in clean_content.split('\n\n') if p.strip()])
                    }
                },
                'author': author,
                'source': article.get('source', ''),
                'publish_date': article.get('publish_date'),
                'category': article.get('category', '')
            }
        except Exception as e:
            print(f"Error processing article: {e}")
            return {}

    def process_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Process multiple articles in parallel.
        """
        processed_articles = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_article = {executor.submit(self.process_single_article, article): article
                                 for article in articles}
            for future in as_completed(future_to_article):
                try:
                    processed_article = future.result()
                    if processed_article:
                        processed_articles.append(processed_article)
                except Exception as e:
                    print(f"Error in article processing: {e}")
        return processed_articles

    def save_to_json(self, articles: List[Dict]):
        """
        Save processed articles to JSON file.
        """
        output_file_path = os.path.join('..', '..', 'data/', self.config.output_file)
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(articles, json_file, ensure_ascii=False, indent=4)
        print(f"Processed articles saved to {self.config.output_file}")

    def run(self):
        """
        Main execution method to process all articles.
        """
        print("Starting article processing...")
        raw_articles = self.read_articles()
        print(f"Found {len(raw_articles)} articles to process")

        processed_articles = self.process_articles(raw_articles)
        print(f"Successfully processed {len(processed_articles)} articles")

        self.save_to_json(processed_articles)
        print("Article processing completed")

if __name__ == "__main__":
    config = ArticleProcessorConfig(
        input_file="newsapi_api_articles_raw.json",
        output_file="temp.json"
    )

    processor = ArticleProcessor(config)
    processor.run()