from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings


def get_embedding_model():
    embedding = OllamaEmbedding(model_name="mxbai-embed-large", embed_batch_size=2)
    Settings.embed_model = embedding
    Settings.chunk_size = 512
    Settings.chunk_overlap = 4
    return embedding
