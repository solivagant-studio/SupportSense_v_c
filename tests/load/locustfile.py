# PLAN TASK: 9 | STUDENT TASK PACK: Day 15 | EVIDENCE: TD-08
# WHERE: Locust load profiles for clean and seeded-behaviour comparison
# DO: start with `make load`, or run a profile with `-u 10`, `-u 50` or `-u 100`.
from locust import HttpUser, between, task

PAYLOAD = {
    "text": "My parcel never arrived and support ignored me",
    "channel": "email",
    "customer_tier": "standard",
    "locale": "en-ZA",
}

PROFILES = {
    "smoke": {"users": 10, "spawn_rate": 2, "duration": "10s"},
    "calibration": {"users": 50, "spawn_rate": 5, "duration": "5m"},
    "stress": {"users": 100, "spawn_rate": 10, "duration": "5m"},
}


class SupportSenseUser(HttpUser):
    wait_time = between(0.05, 0.15)

    @task(8)
    def classify(self):
        self.client.post("/v1/classify", json=PAYLOAD)

    @task(1)
    def health(self):
        self.client.get("/v1/health")
