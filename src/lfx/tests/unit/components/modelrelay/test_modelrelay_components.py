from lfx.components.modelrelay.task_query import ModelRelayTaskQueryComponent
from lfx.components.modelrelay.task_submit import ModelRelayTaskSubmitComponent
from lfx.schema.data import Data
from lfx.schema.message import Message


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


def test_model_relay_submit_task_accepts_agent_message_prompt(monkeypatch):
    captured = {}

    def fake_post_task_submit(api_key, payload):
        captured["api_key"] = api_key
        captured["payload"] = payload
        return {"data": {"task_uid": "task_from_agent"}}

    monkeypatch.setattr("lfx.components.modelrelay.task_submit.post_task_submit", fake_post_task_submit)

    component = ModelRelayTaskSubmitComponent(
        api_key="sk-test",  # pragma: allowlist secret
        task_type="image",
        model_code="image-model",
        prompt=Message(text="A cinematic robot painting a sunrise"),
    )

    result = component.submit_task()

    assert captured == {
        "api_key": "sk-test",  # pragma: allowlist secret
        "payload": {
            "task_type": "image",
            "model_code": "image-model",
            "prompt": "A cinematic robot painting a sunrise",
        },
    }
    assert result.data["task_uid"] == "task_from_agent"


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


def test_model_relay_query_task_polls_until_terminal_status(monkeypatch):
    statuses = [0, 1, 2]
    captured = {"calls": 0}

    def fake_get_task_query(_api_key, task_uid):
        status = statuses.pop(0)
        captured["calls"] += 1
        return {
            "data": {
                "task": {
                    "task_uid": task_uid,
                    "status": status,
                    "detail": {"result": {"image": "https://cdn.example.com/image.png"} if status == 2 else None},
                }
            }
        }

    monkeypatch.setattr("lfx.components.modelrelay.task_query.get_task_query", fake_get_task_query)

    component = ModelRelayTaskQueryComponent(
        api_key="sk-test",  # pragma: allowlist secret
        task_uid="task_123",
        poll_until_complete=True,
        max_attempts=5,
        poll_interval_seconds=0,
    )

    result = component.query_task()

    assert captured["calls"] == 3
    assert result.data["task"]["status"] == 2
    assert result.data["result"] == {"image": "https://cdn.example.com/image.png"}
    assert result.data["attempts"] == 3
    assert result.data["completed"] is True


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


def test_model_relay_query_task_media_output_extracts_video(monkeypatch):
    captured = {"calls": 0}

    def fake_get_task_query(_api_key, task_uid):
        captured["calls"] += 1
        return {
            "data": {
                "task": {
                    "task_uid": task_uid,
                    "task_type": "video",
                    "status": 2,
                    "detail": {
                        "result": {
                            "provider_task_id": "provider_123",
                            "video": "https://cdn.example.com/video.mp4",
                            "last_frame_url": "https://cdn.example.com/last.jpg",
                        }
                    },
                }
            }
        }

    monkeypatch.setattr("lfx.components.modelrelay.task_query.get_task_query", fake_get_task_query)

    component = ModelRelayTaskQueryComponent(
        api_key="sk-test",  # pragma: allowlist secret
        task_uid="task_video",
    )

    data_result = component.query_task()
    media_result = component.query_task_media()

    assert captured["calls"] == 1
    assert data_result.data["result"]["video"] == "https://cdn.example.com/video.mp4"
    assert media_result.text == ""
    assert media_result.content_blocks[0].title == "Model Relay Media"
    assert len(media_result.content_blocks[0].contents) == 1
    media_content = media_result.content_blocks[0].contents[0]
    assert media_content.type == "media"
    assert media_content.urls == ["https://cdn.example.com/video.mp4"]


def test_model_relay_query_task_media_output_extracts_images(monkeypatch):
    def fake_get_task_query(_api_key, task_uid):
        return {
            "data": {
                "task": {
                    "task_uid": task_uid,
                    "task_type": "image",
                    "status": 2,
                    "detail": {
                        "result": {
                            "images": [
                                "https://cdn.example.com/image-1.png",
                                "https://cdn.example.com/image-2.png",
                            ],
                        }
                    },
                }
            }
        }

    monkeypatch.setattr("lfx.components.modelrelay.task_query.get_task_query", fake_get_task_query)

    component = ModelRelayTaskQueryComponent(
        api_key="sk-test",  # pragma: allowlist secret
        task_uid="task_image",
    )

    media_result = component.query_task_media()

    assert media_result.text == ""
    media_content = media_result.content_blocks[0].contents[0]
    assert media_content.urls == [
        "https://cdn.example.com/image-1.png",
        "https://cdn.example.com/image-2.png",
    ]
