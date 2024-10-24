import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
from typing import List, Dict, Any
import time
import re


class T5TextSummarizer:
    def __init__(self,
                 model_name: str = "t5-base",
                 target_summary_words: int = 150,
                 max_chunk_size: int = 1024):
        """
        Initialize the text summarizer with T5 model
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        self.tokenizer = T5Tokenizer.from_pretrained(model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name).to(self.device)
        self.target_summary_words = target_summary_words
        self.max_chunk_size = max_chunk_size

    def clean_text(self, text: str) -> str:
        """Clean and prepare text for summarization"""
        # Remove multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        # Remove any non-ASCII characters
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        # Remove any markdown or special characters
        text = re.sub(r'[#*_~`]', '', text)
        return text.strip()

    def count_words(self, text: str) -> int:
        """Count the number of words in a text"""
        return len(text.split())

    def format_summary(self, summary: str) -> str:
        """Format and clean the generated summary"""
        # Clean any artifacts or corruption
        summary = self.clean_text(summary)

        # Ensure proper sentence capitalization
        sentences = re.split(r'([.!?]+)', summary)
        formatted_sentences = []

        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i].strip()
            if sentence:
                # Capitalize first letter of sentence
                sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                formatted_sentences.append(sentence + sentences[i + 1])

        # Handle last sentence if it exists without punctuation
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            last_sentence = sentences[-1].strip()
            last_sentence = last_sentence[0].upper() + last_sentence[1:] if len(
                last_sentence) > 1 else last_sentence.upper()
            formatted_sentences.append(last_sentence + '.')

        return ' '.join(formatted_sentences)

    def summarize(self, text: str) -> Dict[str, Any]:
        """
        Main method to summarize text
        """
        # Clean input text
        text = self.clean_text(text)

        # Prepare input text
        input_text = f"summarize: {text}"

        # Calculate target length in tokens
        target_length = int(self.target_summary_words * 1.5)
        min_length = int(self.target_summary_words * 0.9)

        try:
            # Encode input text
            inputs = self.tokenizer.encode(
                input_text,
                return_tensors="pt",
                max_length=self.max_chunk_size,
                truncation=True
            ).to(self.device)

            # Generate summary with carefully tuned parameters
            summary_ids = self.model.generate(
                inputs,
                max_length=target_length,
                min_length=min_length,
                num_beams=5,  # Increased beam search
                length_penalty=2.0,  # Encourage longer summaries
                no_repeat_ngram_size=3,
                early_stopping=False,
                do_sample=True,
                top_k=50,  # Limit vocabulary choices
                top_p=0.95,  # Nuclear sampling
                temperature=0.7,  # Moderate randomness
                repetition_penalty=2.5,  # Strongly discourage repetition
                bad_words_ids=[[self.tokenizer.pad_token_id]]  # Prevent padding tokens
            )

            # Decode summary
            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)

            # Format and clean the summary
            summary = self.format_summary(summary)

            # Control final length
            words = summary.split()
            if len(words) > self.target_summary_words:
                # Find the last complete sentence within word limit
                current_length = 0
                sentences = re.split(r'([.!?]+\s*)', summary)
                final_sentences = []

                for i in range(0, len(sentences) - 1, 2):
                    sentence = sentences[i] + sentences[i + 1]
                    sentence_length = len(sentence.split())
                    if current_length + sentence_length <= self.target_summary_words:
                        final_sentences.append(sentence)
                        current_length += sentence_length
                    else:
                        break

                summary = ''.join(final_sentences).strip()

            result = {
                "final_summary": summary,
                "summary_word_count": self.count_words(summary),
                "original_word_count": self.count_words(text),
                "compression_ratio": round(self.count_words(summary) / self.count_words(text), 2)
            }

            return result

        except Exception as e:
            print(f"Error during summarization: {str(e)}")
            return {
                "final_summary": "Error generating summary",
                "summary_word_count": 0,
                "original_word_count": self.count_words(text),
                "compression_ratio": 0,
                "error": str(e)
            }

if __name__ == "__main__":
    summarizer = T5TextSummarizer(target_summary_words=150)

    test_text = """Forward-looking: Fusion energy is often regarded as the holy grail of power generation because it harnesses the same atomic process that powers the sun. The concept involves forcing atomic nuclei to fuse together, unleashing immense energy. If scientists can crack the code using lasers, it could lead to a virtually limitless supply of safe, sustainable energy without any carbon emissions.

        This month, construction crews are breaking ground on an ambitious new laser research facility at Colorado State University, which aims to be a nexus for developing laser-driven nuclear fusion as a viable clean energy source. The facility will cost a whopping $150 million and is expected to open in 2026.

        The Advanced Technology Lasers for Applications and Science (ATLAS) Facility is the product of over 40 years of laser research at CSU, partly funded by the Department of Energy, which has invested $28 million. The lab's development also stems from a strategic partnership with the private sector – Marvel Fusion, a German startup, is contributing major funding and providing two cutting-edge lasers.

        Upon completion, the facility will combine these Marvel lasers with an upgraded version of an existing ultra-intense laser developed at CSU. Together, the three laser systems will be able to simultaneously unleash nearly 7 petawatts of power – more than 5,000 times the total electrical generation capacity of the United States – in pulses lasting just 100 quadrillionths of a second. That's an immense amount of energy concentrated into an area about the width of a human hair.

        With this kind of focused energy, one of the main goals is to advance laser-driven nuclear fusion as a future clean energy source.

        The facility will support other interdisciplinary research, too. The medical field is cited as one area that could benefit, with similar laser technology being used for tumor treatments by concentrating the energy in precise tiny areas. Another potential application is ultra-high-resolution imaging, such as capturing incredibly detailed X-rays of turbine engines.

        "As a top institution recognized both for research and for sustainability, CSU is a fitting home for this facility," said university president Amy Parsons at the ceremony. "We have been a leader in laser research for decades, and our faculty are advancing critical technologies. This new facility will house one of the most powerful lasers in the world and establishes CSU as a nexus for laser fusion research."

        The new ATLAS building will be part of CSU's larger Advanced Laser for Extreme Photonics (ALEPH) Center. It's an ambitious venture that could pay huge dividends if its potential can be effectively harnessed."""

    print("\nProcessing text...")
    start_time = time.time()
    result = summarizer.summarize(test_text)

    print(f"\nTime taken: {time.time() - start_time:.2f} seconds")
    print(f"Original word count: {result['original_word_count']}")
    print(f"Summary word count: {result['summary_word_count']}")
    print(f"Compression ratio: {result['compression_ratio']}")
    print("\nFinal summary:")
    print(result['final_summary'])