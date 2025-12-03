"""Abstract base class for embedding providers."""

from abc import ABC, abstractmethod


class EmbeddingClient(ABC):
    """Abstract base class for text embedding providers."""

    @abstractmethod
    async def get_embedding(self, text: str) -> list[float]:
        """
        Convert text string into a vector embedding.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the vector embedding.
        """
        pass

    @abstractmethod
    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Convert multiple text strings into vector embeddings.

        Args:
            texts: A list of texts to embed.

        Returns:
            A list of embeddings, where each embedding is a list of floats.
        """
        pass
