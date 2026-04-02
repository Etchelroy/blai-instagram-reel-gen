import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path


def get_test_cfg():
    return {
        "INSTAGRAM_ACCOUNT_ID": "123456789",
        "INSTAGRAM_ACCESS_TOKEN": "test_token",
        "AWS_ACCESS_KEY_ID": "test_key",
        "AWS_SECRET_ACCESS_KEY": "test_secret",
        "AWS_S3_BUCKET": "test-bucket",
        "AWS_REGION": "us-east-1",
    }


def test_dry_run_returns_payload(tmp_path, capsys):
    video_path = str(tmp_path / "reel.mp4")
    Path(video_path).write_bytes(b"fake")
    cfg = get_test_cfg()

    from poster import post_reel
    result = post_reel(video_path, "Is AI conscious?", cfg, dry_run=True)

    assert result["dry_run"] is True
    assert "instagram_step1_container" in result
    assert "instagram_step2_publish" in result
    assert "s3_upload_payload" in result
    assert "Is AI conscious?" in result["caption"]


def test_dry_run_payload_structure(tmp_path):
    video_path = str(tmp_path / "reel.mp4")
    Path(video_path).write_bytes(b"fake")
    cfg = get_test_cfg()

    from poster import post_reel
    result = post_reel(video_path, "Test prompt", cfg, dry_run=True)

    container = result["instagram_step1_container"]
    assert container["method"] == "POST"
    assert "media" in container["endpoint"]
    assert container["body"]["media_type"] == "REELS"

    publish = result["instagram_step2_publish"]
    assert publish["method"] == "POST"
    assert "media_publish" in publish["endpoint"]


def test_live_mode_missing_vars_raises(tmp_path):
    video_path = str(tmp_path / "reel.mp4")
    Path(video_path).write_bytes(b"fake")
    cfg = {}  # empty config

    from poster import post_reel
    with pytest.raises(EnvironmentError, match="Missing required env vars"):
        post_reel(video_path, "test", cfg, dry_run=False)


def test_upload_to_s3(tmp_path):
    video_path = str(tmp_path / "reel.mp4")
    Path(video_path).write_bytes(b"fake video")
    cfg = get_test_cfg()

    mock_s3 = MagicMock()
    mock_boto3 = MagicMock()
    mock_boto3.client.return_value = mock_s3

    with patch("poster.boto3", mock_boto3):
        from poster import upload_to_s3
        url = upload_to_s3(video_path, cfg)
        assert "test-bucket" in url
        assert "reel.mp4" in url
        mock_s3.upload_file.assert_called_once()


def test_publish_instagram_reel():
    cfg = get_test_cfg()

    mock_responses = []

    # Step 1: container creation
    r1 = MagicMock()
    r1.json.return_value = {"id": "container_123"}
    r1.raise_for_status = MagicMock()

    # Step 2: status check (FINISHED)
    r2 = MagicMock()
    r2.json.return_value = {"status_code": "FINISHED"}
    r2.raise_for_status = MagicMock()

    # Step 3: publish
    r3 = MagicMock()
    r3.json.return_value = {"id": "reel_456"}
    r3.raise_for_status = MagicMock()

    with patch("poster.requests.post", side_effect=[r1, r3