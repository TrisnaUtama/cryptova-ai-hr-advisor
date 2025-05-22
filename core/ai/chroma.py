from chromadb import HttpClient
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import os
from django.conf import settings
chroma = HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)

openai_ef = OpenAIEmbeddingFunction(
    model_name="text-embedding-3-large",
    api_key=os.getenv("OPENAI_API_KEY"),
)
