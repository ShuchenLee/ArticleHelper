import json

from app.services.qwen_client import QwenClient


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_qwen_client_chat_completion_posts_openai_compatible_payload():
    captured = {}

    def fake_opener(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["authorization"] = request.headers["Authorization"]
        return FakeResponse({"choices": [{"message": {"content": "回答"}}]})

    client = QwenClient(
        api_key="secret",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        llm_model="qwen-test",
        opener=fake_opener,
    )

    answer = client.chat_completion(messages=[{"role": "user", "content": "你好"}])

    assert answer == "回答"
    assert captured["url"].endswith("/chat/completions")
    assert captured["payload"]["model"] == "qwen-test"
    assert captured["authorization"] == "Bearer secret"


def test_qwen_client_embed_texts_posts_embedding_model():
    captured = {}

    def fake_opener(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse({"data": [{"embedding": [0.1, 0.2]}]})

    client = QwenClient(
        api_key="secret",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        embedding_model="embedding-test",
        opener=fake_opener,
    )

    embeddings = client.embed_texts(["paper text"])

    assert embeddings == [[0.1, 0.2]]
    assert captured["payload"]["model"] == "embedding-test"
    assert captured["payload"]["input"] == ["paper text"]
