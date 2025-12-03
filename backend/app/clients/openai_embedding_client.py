"""OpenAI implementation of the EmbeddingClient."""

from openai import AsyncOpenAI

from app.clients.embedding_client import EmbeddingClient


class OpenAIEmbeddingClient(EmbeddingClient):
    """OpenAI implementation for text embeddings using text-embedding-3-small."""

    # Model dimensions - text-embedding-3-small produces 1536-dimensional embeddings
    EMBEDDING_DIMENSION = 1536

    def __init__(self, api_key: str):
        """
        Initialise the OpenAI embedding client.

        Args:
            api_key: OpenAI API key.
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"

    async def get_embedding(self, text: str) -> list[float]:
        """
        Convert text string into a vector embedding.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the vector embedding.
        """
        # Strip newlines to improve embedding performance as recommended by OpenAI
        clean_text = text.replace("\n", " ")

        response = await self.client.embeddings.create(input=[clean_text], model=self.model)

        return response.data[0].embedding

    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Convert multiple text strings into vector embeddings.

        Args:
            texts: A list of texts to embed.

        Returns:
            A list of embeddings, where each embedding is a list of floats.
        """
        # Strip newlines from all texts
        clean_texts = [text.replace("\n", " ") for text in texts]

        response = await self.client.embeddings.create(input=clean_texts, model=self.model)

        # Return embeddings in the same order as input texts
        return [item.embedding for item in response.data]
