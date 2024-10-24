import json
import time
from content_summarizer_bart import TextSummarizer
from typing import Dict, Any, List
from pathlib import Path
import concurrent.futures
from tqdm import tqdm
import logging
from datetime import datetime


class OptimizedJsonProcessor:
    def __init__(self, max_workers: int = None):
        """
        Initialize the processor with TextSummarizer
        Args:
            max_workers: Maximum number of threads to use. If None, will use default ThreadPoolExecutor value
        """
        self.summarizer = TextSummarizer()
        self.max_workers = max_workers

        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        logging.basicConfig(
            filename=f'summarization_{timestamp}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def process_single_article(self, article: Dict) -> Dict:
        """
        Process a single article and add summary
        """
        try:
            # Extract content from cleaned or original
            content = article.get('cleaned', {}).get('content', '')
            if not content:
                content = article.get('original', {}).get('content', '')

            if not content:
                raise ValueError("No content found to summarize")

            # Generate summary
            summary_result = self.summarizer.summarize(content)

            # Add summary to article
            article['summarized'] = {
                "content": summary_result["final_summary"],
                "metadata": {
                    "original_word_count": summary_result["original_word_count"],
                    "summary_word_count": summary_result["summary_word_count"]
                }
            }

            return article

        except Exception as e:
            error_msg = f"Error processing article: {str(e)}"
            logging.error(error_msg)
            article['summarized'] = {
                "error": str(e),
                "processing_timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            return article

    def process_batch(self, input_file: str, output_file: str) -> None:
        """
        Process multiple articles concurrently using ThreadPoolExecutor
        """
        try:
            # Read input JSON
            start_time = time.time()
            logging.info(f"Starting processing of {input_file}")
            print(f"\nReading input file: {input_file}")

            with open(input_file, 'r', encoding='utf-8') as f:
                articles = json.load(f)

            if not isinstance(articles, list):
                articles = [articles]  # Convert single article to list

            total_articles = len(articles)
            print(f"Found {total_articles} articles to process")
            logging.info(f"Processing {total_articles} articles")

            # Process articles concurrently
            processed_articles = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all articles for processing
                future_to_article = {
                    executor.submit(self.process_single_article, article): i
                    for i, article in enumerate(articles)
                }

                # Process completed futures with progress bar
                with tqdm(total=total_articles, desc="Processing articles") as pbar:
                    for future in concurrent.futures.as_completed(future_to_article):
                        article_index = future_to_article[future]
                        try:
                            processed_article = future.result()
                            processed_articles.append(processed_article)
                            pbar.update(1)
                        except Exception as e:
                            error_msg = f"Error processing article {article_index}: {str(e)}"
                            logging.error(error_msg)
                            articles[article_index]['summarized'] = {
                                "error": str(e),
                                "processing_timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ')
                            }
                            processed_articles.append(articles[article_index])
                            pbar.update(1)

            # Sort processed articles back to original order
            processed_articles.sort(
                key=lambda x: future_to_article[next(
                    k for k, v in future_to_article.items()
                    if v == articles.index(x)
                )]
            )

            # Save processed articles
            print("\nSaving processed articles...")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_articles, f, indent=4, ensure_ascii=False)

            end_time = time.time()
            processing_time = end_time - start_time
            articles_per_second = total_articles / processing_time

            summary_msg = (
                f"\nProcessing complete:"
                f"\n- Total articles: {total_articles}"
                f"\n- Processing time: {processing_time:.2f} seconds"
                f"\n- Articles per second: {articles_per_second:.2f}"
                f"\n- Output saved to: {output_file}"
            )
            print(summary_msg)
            logging.info(summary_msg)

        except Exception as e:
            error_msg = f"Error in batch processing: {str(e)}"
            print(error_msg)
            logging.error(error_msg)
            raise


def main():
    # Example usage
    input_file = "../../data/temp2.json"
    output_file = "../../data/temp3.json"

    # Initialize processor with number of workers
    # You can adjust max_workers based on your system capabilities
    processor = OptimizedJsonProcessor(max_workers=4)

    try:
        processor.process_batch(input_file, output_file)
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        logging.error(f"Error in main execution: {str(e)}")


if __name__ == "__main__":
    main()