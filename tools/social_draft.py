"""Social media content drafting tool."""

from typing import Dict, Any, Optional
from loguru import logger

from data.schemas import SocialDraft, GuardianReport
from services.gemini_service import gemini_service
from config.prompts import SCRIBE_SYSTEM_PROMPT


def draft_social_content(
    topic: str = None,
    mood: str = None,
    platform: str = "linkedin",
    raw_text: str = None,
    guardian_findings: Optional[GuardianReport] = None
) -> Dict[str, Any]:
    """
    Draft social media content from a topic and mood, or directly from raw text.
    
    Args:
        topic: Main topic/insight to share (optional if raw_text provided)
        mood: Emotional tone (e.g., "resilient", "reflective", "hopeful") (optional if raw_text provided)
        platform: "linkedin" or "twitter"
        raw_text: Raw thoughts to transform directly (takes precedence over topic/mood)
        guardian_findings: Guardian report with sensitive info findings (optional)
        
    Returns:
        Dictionary with content, hashtags, and metadata
    """
    try:
        if raw_text:
            logger.info(f"[draft_social_content] Starting rewrite with raw_text (length: {len(raw_text)})")
            # Build Guardian context if available
            guardian_context = ""
            if guardian_findings:
                concerns_list = guardian_findings.concerns if guardian_findings.concerns else []
                logger.info(f"[draft_social_content] Guardian findings: {len(concerns_list)} concerns")
                if concerns_list:
                    guardian_context = f"\n\nIMPORTANT - The Guardian has identified these sensitive items that MUST be removed:\n" + "\n".join([f"- {c}" for c in concerns_list])
                    guardian_context += "\n\nEnsure these items are completely removed and the content is rewritten professionally."
            
            # Direct transformation from raw text with Guardian guidance
            logger.info(f"[draft_social_content] Building prompt for Gemini API call")
            prompt = f"""You are The Scribe, a professional ghostwriter. Your task is to COMPLETELY REWRITE raw research thoughts into a professional {platform} post.

Raw Thoughts:
{raw_text}{guardian_context}

CRITICAL REQUIREMENTS:
1. COMPLETELY REWRITE - This is NOT a simple find-and-replace. You must transform the entire narrative.
2. Professional LinkedIn tone - This should read like a thoughtful, inspiring post from a researcher, not a vent.
3. Transform structure - Don't keep the same sentence structure. Rewrite it entirely.
4. Transform complaints into insights - Turn frustrations into lessons learned and resilience stories.
5. Remove ALL sensitive information identified by Guardian (names, institutions, proprietary details).
6. Length: 300-600 characters - be concise and impactful.
7. Start directly with content - NO introductory phrases like "Here is...", "Of course...", etc.
8. Include 3-5 relevant academic hashtags at the end.
9. Write in first person.
10. Make it inspiring and relatable to other researchers.

Example of GOOD transformation:
Raw: "I've spent three months labeling the dataset and still can't get stable validation accuracy. The automated tool keeps erasing half my annotations. Honestly, if Professor Thompson tells me to 'try harder' one more time, I might scream."
Professional: "Three months of iterative refinement taught me that data quality isn't just about the tool—it's about the process. Every annotation challenge became a lesson in methodology. Research demands patience, but it also builds the precision we need. The journey from frustration to understanding is where real growth happens. #MachineLearning #DataScience #ResearchJourney"

Example of BAD transformation (DO NOT DO THIS):
Raw: "I've spent three months labeling the dataset and still can't get stable validation accuracy. The automated tool keeps erasing half my annotations. Honestly, if my advisor tells me to 'try harder' one more time, I might scream."
This is just replacing names - NOT acceptable. You must completely rewrite.

Output ONLY the rewritten professional post content. No explanations, no introductions, just the post text."""
            
            logger.info(f"[draft_social_content] Calling Gemini API to generate professional post")
            response = gemini_service.generate_text(
                prompt=prompt,
                model_type="pro",
                system_instruction=SCRIBE_SYSTEM_PROMPT,
                temperature=0.8
            )
            logger.info(f"[draft_social_content] Gemini API returned response (length: {len(response)})")
            logger.info(f"[draft_social_content] Response preview: {response[:200]}...")
        else:
            # Original topic/mood approach
            prompt = f"""Transform this research insight into a professional {platform} post.

Topic: {topic}
Mood: {mood}
Platform: {platform}

Requirements:
- Start directly with the content - DO NOT use phrases like "Here is...", "Of course...", "I'll help you...", or any introductory text
- Be succinct and direct - get to the point immediately
- Professional but authentic tone
- Focus on lessons learned and resilience
- Remove any specific data, names, or proprietary information
- Include 3-5 relevant academic hashtags at the end
- Length: {'280 characters' if platform == 'twitter' else '300-600 characters'} - keep it concise
- Write in first person when appropriate
- Left-align text, no special formatting

Output ONLY the post content, nothing else. No introductions, no explanations, just the post text."""

        response = gemini_service.generate_text(
            prompt=prompt,
            model_type="pro",
            system_instruction=SCRIBE_SYSTEM_PROMPT,
            temperature=0.8
        )
        
        # Clean up response
        content = response.strip()
        
        # Validation: Check if output is too similar to input (indicates poor rewrite)
        if raw_text:
            # Simple similarity check - if too many words overlap, it's likely not rewritten
            raw_words = set(raw_text.lower().split())
            output_words = set(content.lower().split())
            
            # Remove common words
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'i', 'my', 'me', 'we', 'our', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'can', 'could', 'should', 'may', 'might', 'must', 'this', 'that', 'these', 'those'}
            raw_words = raw_words - common_words
            output_words = output_words - common_words
            
            if raw_words and output_words:
                overlap = len(raw_words & output_words)
                similarity_ratio = overlap / len(raw_words) if raw_words else 0
                
                # If more than 40% of unique words overlap, it's likely not properly rewritten
                if similarity_ratio > 0.4:
                    logger.warning(f"Output may not be properly rewritten (similarity: {similarity_ratio:.2f}). Regenerating...")
                    # Try once more with stronger emphasis
                    retry_prompt = prompt + "\n\nREMINDER: You MUST completely rewrite this. The output is too similar to the input. Transform it into a completely different narrative structure."
                    content = gemini_service.generate_text(
                        prompt=retry_prompt,
                        model_type="pro",
                        system_instruction=SCRIBE_SYSTEM_PROMPT,
                        temperature=0.9  # Higher temperature for more variation
                    ).strip()
        
        # Extract hashtags (simple extraction)
        hashtags = []
        words = content.split()
        for word in words:
            if word.startswith("#"):
                hashtags.append(word)
        
        draft = SocialDraft(
            content=content,
            platform=platform,
            hashtags=hashtags,
            sanitized=True,
            risk_level="LOW"
        )
        
        return {
            "content": draft.content,
            "platform": draft.platform,
            "hashtags": draft.hashtags,
            "sanitized": draft.sanitized
        }
        
    except Exception as e:
        logger.error(f"Error drafting social content: {str(e)}", exc_info=True)
        # Return a meaningful fallback based on what we have
        if raw_text:
            # Try to create a basic professional version from raw text
            fallback_content = "Reflecting on the challenges and lessons learned in research. Every iteration teaches us something valuable about methodology, persistence, and resilience. #PhDlife #ResearchJourney #AcademicResilience"
        elif topic:
            fallback_content = f"Reflecting on {topic} - resilience in research is key. #PhDlife #ResearchJourney"
        else:
            fallback_content = "Reflecting on the research journey - resilience and persistence are key. #PhDlife #ResearchJourney"
        
        return {
            "content": fallback_content,
            "platform": platform,
            "hashtags": ["#PhDlife", "#ResearchJourney"],
            "sanitized": True
        }

