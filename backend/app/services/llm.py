"""
LLM Provider Abstraction Layer.
Supports Anthropic Claude, OpenAI, and an offline Mock provider.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from backend.app.config import settings

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract interface for LLM provider implementations."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'anthropic', 'openai', 'mock')."""
        pass

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        history: List[Dict[str, str]],
        system_prompt: str
    ) -> str:
        """
        Generate an assistant response given the user prompt,
        historical context messages, and system prompt.

        :param prompt: Current user input.
        :param history: List of historical message dicts: [{'role': 'user'|'assistant', 'content': '...'}]
        :param system_prompt: Persona / system instructions.
        :return: Generated response string.
        """
        pass


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude integration using the official anthropic SDK."""

    def __init__(self, api_key: str, model: str):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model
        except ImportError as e:
            logger.error("Failed to import anthropic library. Please run pip install anthropic.")
            raise e

    @property
    def provider_name(self) -> str:
        return f"anthropic ({self.model})"

    def generate_response(
        self,
        prompt: str,
        history: List[Dict[str, str]],
        system_prompt: str
    ) -> str:
        # Build Anthropic message payload
        # Anthropic messages must alternate and contain only 'user' and 'assistant'
        formatted_messages: List[Dict[str, str]] = []

        raw_messages = list(history) + [{"role": "user", "content": prompt}]

        # Filter and sanitize messages for Claude
        for msg in raw_messages:
            role = "user" if msg["role"] == "user" else "assistant"
            content = msg["content"].strip()
            if not content:
                continue

            # Merge consecutive messages with the same role if any
            if formatted_messages and formatted_messages[-1]["role"] == role:
                formatted_messages[-1]["content"] += f"\n\n{content}"
            else:
                formatted_messages.append({"role": role, "content": content})

        # Ensure first message is from 'user'
        if formatted_messages and formatted_messages[0]["role"] != "user":
            formatted_messages.insert(0, {"role": "user", "content": "Hello Jarvis."})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=formatted_messages
        )

        # Extract text from response blocks
        reply_parts = []
        for block in response.content:
            if getattr(block, "type", "") == "text":
                reply_parts.append(block.text)
        return "".join(reply_parts).strip()


class OpenAIProvider(BaseLLMProvider):
    """OpenAI integration using the official openai SDK."""

    def __init__(self, api_key: str, model: str):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model
        except ImportError as e:
            logger.error("Failed to import openai library. Please run pip install openai.")
            raise e

    @property
    def provider_name(self) -> str:
        return f"openai ({self.model})"

    def generate_response(
        self,
        prompt: str,
        history: List[Dict[str, str]],
        system_prompt: str
    ) -> str:
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1024
        )
        return response.choices[0].message.content.strip()


class GeminiProvider(BaseLLMProvider):
    """Google Gemini integration using the google-genai SDK."""

    def __init__(self, api_key: str, model: str):
        try:
            from google import genai
            from google.genai import types
            self._genai = genai
            self._types = types
            self.client = genai.Client(api_key=api_key)
            self.model = model
        except ImportError as e:
            logger.error("Failed to import google-genai library. Please run pip install google-genai.")
            raise e

    @property
    def provider_name(self) -> str:
        return f"gemini ({self.model})"

    def generate_response(
        self,
        prompt: str,
        history: List[Dict[str, str]],
        system_prompt: str
    ) -> str:
        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                self._types.Content(
                    role=role,
                    parts=[self._types.Part.from_text(text=msg["content"])]
                )
            )
        contents.append(
            self._types.Content(
                role="user",
                parts=[self._types.Part.from_text(text=prompt)]
            )
        )

        config = self._types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=1024,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config
        )
        return (response.text or "").strip()


class MockProvider(BaseLLMProvider):
    """
    Deterministic offline mock provider for local verification without API keys.
    Demonstrates persona adherence and conversational memory context awareness.
    """

    @property
    def provider_name(self) -> str:
        return "mock-jarvis (offline test mode)"

    def generate_response(
        self,
        prompt: str,
        history: List[Dict[str, str]],
        system_prompt: str
    ) -> str:
        prompt_lower = prompt.lower().strip()

        # Check if user is asking about prior context (e.g., their name or identity)
        if any(keyword in prompt_lower for keyword in ["who am i", "what is my name", "what's my name", "my name"]):
            for msg in reversed(history):
                if msg["role"] == "user":
                    content_lower = msg["content"].lower()
                    if "my name is" in content_lower:
                        parts = msg["content"].split("my name is", 1)
                        if len(parts) > 1:
                            name = parts[1].strip().split()[0].strip(".,!?:")
                            return f"Your name is {name}, sir. I remember our earlier conversation."
                    if "i am" in content_lower:
                        parts = msg["content"].split("i am", 1)
                        if len(parts) > 1:
                            name = parts[1].strip().split()[0].strip(".,!?:")
                            return f"You mentioned you are {name}, sir."
            return "You have not mentioned your name yet, sir. How should I address you?"

        if any(keyword in prompt_lower for keyword in ["hi", "hello", "hey"]):
            return "Good day, sir. Jarvis systems nominal and ready. What can I do for you?"

        if "status" in prompt_lower:
            return f"All local subsystems operating within normal parameters. Memory buffer holding {len(history)} recent message(s)."

        # Default Jarvis-style response
        history_note = f" (Referencing {len(history)} previous turn(s) of context)" if history else ""
        return f"Acknowledged, sir. I have processed your request: '{prompt}'.{history_note}"


def get_llm_service() -> BaseLLMProvider:
    """Factory creating and returning the active LLM provider based on settings."""
    provider_choice = settings.LLM_PROVIDER.lower()

    if provider_choice == "gemini":
        if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_"):
            logger.info("Using Gemini provider with model %s", settings.LLM_MODEL)
            return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.LLM_MODEL)
        else:
            logger.warning(
                "GEMINI_API_KEY not configured or placeholder detected. Falling back to MockProvider."
            )
            return MockProvider()

    elif provider_choice == "anthropic":
        if settings.ANTHROPIC_API_KEY and not settings.ANTHROPIC_API_KEY.startswith("your_"):
            logger.info("Using Anthropic Claude provider with model %s", settings.LLM_MODEL)
            return AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY, model=settings.LLM_MODEL)
        else:
            logger.warning(
                "ANTHROPIC_API_KEY not configured or placeholder detected. Falling back to MockProvider."
            )
            return MockProvider()

    elif provider_choice == "openai":
        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("your_"):
            logger.info("Using OpenAI provider with model %s", settings.LLM_MODEL)
            return OpenAIProvider(api_key=settings.OPENAI_API_KEY, model=settings.LLM_MODEL)
        else:
            logger.warning(
                "OPENAI_API_KEY not configured or placeholder detected. Falling back to MockProvider."
            )
            return MockProvider()

    else:
        logger.info("Using offline MockProvider for testing.")
        return MockProvider()
