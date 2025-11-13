from locust import HttpUser, task, between
import uuid
import random

class StressUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        self.session_id = str(uuid.uuid4())

    def _get_headers(self):
        return {
            "x-session-id": self.session_id,
            "Content-Type": "application/json"
        }

    @task(3)
    def chat_stream(self):
        payload = {
            "message": random.choice([
                "Hello", 
                "What’s the weather like?", 
                "Tell me a joke", 
                "Explain AI in simple terms"
            ]),
            "language": "en",
            "role": "user"
        }
        self.client.post("/chat_stream", json=payload, headers=self._get_headers(), timeout=10)

    @task(1)
    def get_conversation(self):
        self.client.get(f"/conversation?session_id={self.session_id}", timeout=100)

    