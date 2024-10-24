import torch
from transformers import BartTokenizer, BartForConditionalGeneration
from typing import List, Dict, Any
import time

class TextSummarizer:
    def __init__(self, model_name: str = "facebook/bart-large-cnn",
                 max_chunk_size: int = 1024,
                 target_summary_words: int = 150,
                 min_chunk_size: int = 512):
        """
        Initialize the text summarizer with BART model
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = BartTokenizer.from_pretrained(model_name)
        self.model = BartForConditionalGeneration.from_pretrained(model_name).to(self.device)
        self.max_chunk_size = max_chunk_size
        self.target_summary_words = target_summary_words
        self.min_chunk_size = min_chunk_size

    def count_words(self, text: str) -> int:
        """Count the number of words in a text"""
        return len(text.split())

    def summarize_text(self, text: str) -> str:
        """
        Summarize text with controlled output length
        """
        # Calculate target length in tokens (approximate)
        target_length = int(self.target_summary_words * 1.5)  # Increased factor for token-to-word ratio
        min_length = int(self.target_summary_words * 0.9)  # Set minimum length to 90% of target

        # Encode the text - this returns the tensor directly
        inputs = self.tokenizer.encode(
            text,
            return_tensors="pt",
            max_length=self.max_chunk_size,
            truncation=True
        ).to(self.device)

        # Generate summary with more aggressive length control
        summary_ids = self.model.generate(
            inputs,  # Use the tensor directly
            num_beams=4,
            max_length=target_length,
            min_length=min_length,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=0.4,
            early_stopping=True
        )

        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)

        # Ensure we don't go too far over target word count
        words = summary.split()
        if len(words) > self.target_summary_words * 1.1:  # Allow 10% overflow
            summary = ' '.join(words[:self.target_summary_words])
            if not summary.endswith('.'):
                summary += '.'

        return summary

    def summarize(self, text: str) -> Dict[str, Any]:
        """
        Main method to summarize text
        """
        # Clean the input text
        text = text.replace('\n', ' ').strip()

        # Get summary
        summary = self.summarize_text(text)

        # Prepare result
        result = {
            "final_summary": summary,
            "summary_word_count": self.count_words(summary),
            "original_word_count": self.count_words(text)
        }

        return result


if __name__ == "__main__":
    summarizer = TextSummarizer()

    test_text = """
        CHANGSHA, Oct. 20 (Xinhua) -- \"Three-Body,\" the live-action television adaptation of the science fiction novel \"The Three-Body Problem,\" claimed the best TV drama as China's national TV arts award unveiled on Sunday. The drama's director Yang Lei received the honor of the best TV drama director of the China TV Golden Eagle Award, which was unveiled in Changsha, central China's Hunan Province. In his acceptance speech, Yang said that Chinese science fiction faces challenges. He said whenever science fiction is mentioned, audiences tend to immediately think of Western sci-fi stories and movies. \"When I was creating 'Three-Body,' I wanted to take a different path. I hoped it would be a Chinese sci-fi story, one that has a sense of Chinese identity,\" he said, adding that he approached the filming with a realist perspective. He went on to say that the rapid advancement of China's technology has provided fertile ground for science fiction to grow. He calls on all Chinese sci-fi creators to make full use of Chinese elements in their work to bring the dream of science fiction into reality and to let the universe shine for Chinese science fiction. Since its release in January 2023, the 30-episode drama has received critical acclaim. It was rated 8.7 out of 10 by over 480,000 viewers on China's popular review platform Douban as of Sunday. It is the live-action television adaptation of the Hugo Award-winning science fiction novel \"The Three-Body Problem\" by Liu Cixin. \"The Three-Body Problem\" is the first book of a sci-fi trilogy that revolves around physicist Ye Wenjie's contact with the Trisolaran civilization existing in a three-sun system and the centuries-long clashes that follow between earthlings and the aliens. Fans of \"Three-Body\" expressed their excitement after the series received the award. \"I'm so excited! A uniquely Chinese path for science fiction has been explored,\" said a Chinese fan named Wang Jingyi. \"When I first read the book, I was blown away. I always wondered how it could be brought to life on screen until I watched Yang Lei's incredible adaptation,\" said Artur Furdey, a British viewer. Liu Cixin, the author of the novel, expressed his satisfaction with the adaptation of his work that has been well-received by the audiences. \"It will take time for Chinese science fiction to take root in the hearts of the public. I hope we can work together to create more and better works,\" Liu said.
        """

    print("\nProcessing text...")
    start_time = time.time()
    result = summarizer.summarize(test_text)
    print(f"Time taken: {time.time() - start_time:.2f} seconds")
    print(f"Original word count: {result['original_word_count']}")
    print(f"Summary word count: {result['summary_word_count']}")
    print("\nFinal summary:")
    print(result['final_summary'])