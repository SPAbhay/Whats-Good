from typing import Dict, List, Optional
import re


class ResponseFormatter:
    """
    Formats responses with platform-specific styling and structure
    """

    PLATFORM_STYLES = {
        "LinkedIn": {
            "max_length": 3000,
            "paragraph_spacing": 2,
            "emphasis_style": "**",
            "list_style": "• ",
            "cta_position": "end",
            "hashtag_limit": 5
        },
        "Twitter": {
            "max_length": 280,
            "paragraph_spacing": 1,
            "emphasis_style": "*",
            "list_style": "- ",
            "cta_position": "end",
            "hashtag_limit": 3
        },
        "Instagram": {
            "max_length": 2200,
            "paragraph_spacing": 2,
            "emphasis_style": "✨",
            "list_style": "◽️ ",
            "cta_position": "middle",
            "hashtag_limit": 30
        },
        "Facebook": {
            "max_length": 63206,
            "paragraph_spacing": 2,
            "emphasis_style": "**",
            "list_style": "• ",
            "cta_position": "end",
            "hashtag_limit": 3
        },
        "TikTok": {
            "max_length": 2200,
            "paragraph_spacing": 1,
            "emphasis_style": "✨",
            "list_style": "→ ",
            "cta_position": "start",
            "hashtag_limit": 5
        },
        "YouTube": {
            "max_length": 5000,
            "paragraph_spacing": 2,
            "emphasis_style": "**",
            "list_style": "• ",
            "cta_position": "both",
            "hashtag_limit": 15
        },
        "General": {
            "max_length": 5000,
            "paragraph_spacing": 2,
            "emphasis_style": "*",
            "list_style": "• ",
            "cta_position": "end",
            "hashtag_limit": 5
        }
    }

    def format_response(
            self,
            content: str,
            platform: str,
            include_persona: bool = True,
            style_override: Optional[Dict] = None
    ) -> str:
        """Format response according to platform guidelines"""
        style = self.PLATFORM_STYLES.get(platform, self.PLATFORM_STYLES["General"])
        if style_override:
            style.update(style_override)

        # Clean up the content
        formatted_content = self._clean_content(content)

        # Apply platform-specific formatting
        formatted_content = self._apply_platform_formatting(
            formatted_content,
            platform,
            style
        )

        # Add appropriate spacing
        formatted_content = self._apply_spacing(
            formatted_content,
            style["paragraph_spacing"]
        )

        # Truncate if needed
        formatted_content = self._truncate_content(
            formatted_content,
            style["max_length"]
        )

        return formatted_content

    def _clean_content(self, content: str) -> str:
        """Clean up content formatting"""
        # Remove multiple spaces
        content = re.sub(r'\s+', ' ', content)

        # Fix list formatting
        content = re.sub(r'\n\s*[-•]\s*', '\n• ', content)

        # Fix emphasis formatting
        content = re.sub(r'[\*_]{2,}(.+?)[\*_]{2,}', r'**\1**', content)

        # Clean up newlines
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content.strip()

    def _apply_platform_formatting(
            self,
            content: str,
            platform: str,
            style: Dict
    ) -> str:
        """Apply platform-specific formatting"""
        # Format lists
        if '•' in content:
            content = self._format_lists(content, style["list_style"])

        # Format emphasis
        content = self._format_emphasis(content, style["emphasis_style"])

        # Format hashtags
        content = self._format_hashtags(content, style["hashtag_limit"])

        # Format CTAs
        content = self._format_cta(content, style["cta_position"])

        return content

    def _format_lists(self, content: str, list_style: str) -> str:
        """Format list items with platform-specific style"""
        lines = content.split('\n')
        formatted_lines = []

        for line in lines:
            if line.strip().startswith('•'):
                formatted_lines.append(
                    line.replace('•', list_style, 1)
                )
            else:
                formatted_lines.append(line)

        return '\n'.join(formatted_lines)

    def _format_emphasis(self, content: str, emphasis_style: str) -> str:
        """Format emphasis markers"""
        # Replace standard emphasis with platform-specific style
        content = re.sub(
            r'[\*_]{1,2}(.+?)[\*_]{1,2}',
            f'{emphasis_style}\\1{emphasis_style}',
            content
        )
        return content

    def _format_hashtags(self, content: str, limit: int) -> str:
        """Format and limit hashtags"""
        # Extract existing hashtags
        hashtags = re.findall(r'#\w+', content)

        if len(hashtags) > limit:
            # Remove excess hashtags
            for hashtag in hashtags[limit:]:
                content = content.replace(hashtag, '')

        return content.strip()

    def _format_cta(self, content: str, position: str) -> str:
        """Format call-to-action placement"""
        # Identify CTA phrases
        cta_patterns = [
            r'(?i)(follow|like|share|comment|subscribe).+',
            r'(?i)(check out|learn more|click|visit).+',
            r'(?i)(what do you think|let me know).+'
        ]

        for pattern in cta_patterns:
            match = re.search(pattern, content)
            if match:
                cta_text = match.group(0)
                content = content.replace(cta_text, '')

                if position == "start":
                    content = f"{cta_text}\n\n{content}"
                elif position == "middle":
                    paragraphs = content.split('\n\n')
                    mid_point = len(paragraphs) // 2
                    paragraphs.insert(mid_point, cta_text)
                    content = '\n\n'.join(paragraphs)
                elif position == "both":
                    content = f"{cta_text}\n\n{content}\n\n{cta_text}"
                else:  # "end" or default
                    content = f"{content}\n\n{cta_text}"

                break

        return content.strip()

    def _apply_spacing(self, content: str, spacing: int) -> str:
        """Apply paragraph spacing"""
        # Split into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        # Join with appropriate spacing
        return ('\n' * spacing).join(paragraphs)

    def _truncate_content(self, content: str, max_length: int) -> str:
        """Truncate content if it exceeds max length"""
        if len(content) <= max_length:
            return content

        # Try to truncate at sentence boundary
        truncated = content[:max_length]
        last_sentence = truncated.rfind('.')

        if last_sentence > max_length * 0.8:  # If we can keep most of the content
            return content[:last_sentence + 1]

        # Otherwise truncate at word boundary
        last_space = truncated.rfind(' ')
        return content[:last_space] + '...'

    def format_error_response(self, error: str) -> str:
        """Format error responses"""
        return (
            "I apologize, but I encountered an issue while processing your request. "
            f"Error: {error}\n\n"
            "Could you please try rephrasing your request or providing more details?"
        )

    def format_clarification_request(
            self,
            missing_info: List[str],
            platform: str = "General"
    ) -> str:
        """Format requests for clarification"""
        style = self.PLATFORM_STYLES.get(platform, self.PLATFORM_STYLES["General"])

        response = (
                "I'd be happy to help! To provide the best response, "
                "I just need a few more details:\n\n"
                + '\n'.join(f"{style['list_style']}{info}" for info in missing_info)
                + "\n\nCould you help me with these details?"
        )

        return self._apply_spacing(response, style["paragraph_spacing"])