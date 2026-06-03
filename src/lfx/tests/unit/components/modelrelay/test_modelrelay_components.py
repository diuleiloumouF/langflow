from lfx.components.modelrelay.task_query import ModelRelayTaskQueryComponent
from lfx.components.modelrelay.task_submit import ModelRelayTaskSubmitComponent
from lfx.schema.data import Data


def test_model_relay_submit_task_flattens_response(monkeypatch):
    captured = {"calls": 0}

    def fake_post_task_submit(api_key, payload):  # pragma: allowlist secret
        captured["calls"] += 1
        captured["api_key"] = api_key
        captured["payload"] = payload
        return {
            "code": 0,
            "msg": "",
            "data": {
                "task_uid": "task_123",
                "estimated_amount": 1.5,
                "account_uid": "account_1",
                "key_uid": "key_1",
            },
        }

    monkeypatch.setattr("lfx.components.modelrelay.task_submit.post_task_submit", fake_post_task_submit)

    component = ModelRelayTaskSubmitComponent(
        api_key="sk-test",  # pragma: allowlist secret
        task_type="video",
        model_code="zhizhen-20",
        prompt="A cat running on a beach",
        video_duration=5,
        video_resolution="720p",
        video_ratio="16:9",
        parameters={"video_mode": "text_to_video"},
    )

    result = component.submit_task()
    task_uid = component.submit_task_uid()

    assert captured["calls"] == 1
    assert captured["api_key"] == "sk-test"  # pragma: allowlist secret
    assert captured["payload"] == {
        "task_type": "video",
        "model_code": "zhizhen-20",
        "prompt": "A cat running on a beach",
        "video_duration": 5,
        "video_resolution": "720p",
        "video_ratio": "16:9",
        "parameters": {"video_mode": "text_to_video"},
    }
    assert task_uid.text == "task_123"
    assert result.data["task_uid"] == "task_123"
    assert result.data["estimated_amount"] == 1.5
    assert result.data["response"]["code"] == 0


def test_model_relay_query_task_extracts_task_uid_from_submit_data(monkeypatch):
    captured = {}

    def fake_get_task_query(api_key, task_uid):
        captured["api_key"] = api_key
        captured["task_uid"] = task_uid
        return {
            "code": 0,
            "msg": "",
            "data": {
                "task": {
                    "task_uid": task_uid,
                    "task_type": "video",
                    "status": 2,
                    "detail": {"result": {"video": "https://cdn.example.com/video.mp4"}},
                }
            },
        }

    monkeypatch.setattr("lfx.components.modelrelay.task_query.get_task_query", fake_get_task_query)

    component = ModelRelayTaskQueryComponent(
        api_key="sk-test",  # pragma: allowlist secret
        task=Data(data={"task_uid": "task_123"}),
    )

    result = component.query_task()

    assert captured == {"api_key": "sk-test", "task_uid": "task_123"}  # pragma: allowlist secret
    assert result.data["task"]["task_uid"] == "task_123"
    assert result.data["result"] == {"video": "https://cdn.example.com/video.mp4"}
    assert result.data["response"]["code"] == 0


def test_model_relay_query_task_extracts_task_uid_from_submit_message(monkeypatch):
    captured = {}

    def fake_get_task_query(api_key, task_uid):
        captured["api_key"] = api_key
        captured["task_uid"] = task_uid
        return {"data": {"task": {"task_uid": task_uid}}}

    monkeypatch.setattr("lfx.components.modelrelay.task_query.get_task_query", fake_get_task_query)

    submit_component = ModelRelayTaskSubmitComponent(api_key="sk-test")  # pragma: allowlist secret
    submit_component._submission_result = Data(data={"task_uid": "task_from_output"})

    component = ModelRelayTaskQueryComponent(
        api_key="sk-test",  # pragma: allowlist secret
        task_uid=submit_component.submit_task_uid(),
    )

    result = component.query_task()

    assert captured == {"api_key": "sk-test", "task_uid": "task_from_output"}  # pragma: allowlist secret
    assert result.data["task"]["task_uid"] == "task_from_output"


def test_model_relay_query_task_prefers_direct_task_uid(monkeypatch):
    captured = {}

    def fake_get_task_query(_api_key, task_uid):
        captured["task_uid"] = task_uid
        return {"data": {"task": {"task_uid": task_uid}}}

    monkeypatch.setattr("lfx.components.modelrelay.task_query.get_task_query", fake_get_task_query)

    component = ModelRelayTaskQueryComponent(
        api_key="sk-test",  # pragma: allowlist secret
        task_uid="task_direct",
        task=Data(data={"task_uid": "task_from_data"}),
    )

    result = component.query_task()

    assert captured["task_uid"] == "task_direct"
    assert result.data["task"]["task_uid"] == "task_direct"
