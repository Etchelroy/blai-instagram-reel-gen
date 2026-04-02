import pytest
from unittest.mock import patch, MagicMock

import poster


def test_publish_reel_dry_run():
    result = poster.publish_reel("reel.mp4", "Test caption", dry_run=True)
    assert result["dry_run"] is True
    assert result["payload"]["mode"] == "dry_run"
    assert result["payload"]["video_path"] == "reel.mp4"


def test_upload_to_s3(tmp_path):
    f = tmp_path / "reel.mp4"
    f.write_bytes(b"fake")

    with patch("poster.boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        with patch("poster.config.S3_BUCKET_NAME", "mybucket"), \
             patch("poster.config.AWS_REGION", "us-east-1"):
            url = poster.upload_to_s3(str(f))

    mock_s3.upload_file.assert_called_once()
    assert "mybucket" in url
    assert "reel.mp4" in url


def test_publish_reel_live(tmp_path):
    f = tmp_path / "reel.mp4"
    f.write_bytes(b"fake")

    with patch("poster.upload_to_s3", return_value="https://s3.example.com/reel.mp4"), \
         patch("poster._create_media_container", return_value="container_123"), \
         patch("poster._wait_for_container"), \
         patch("poster._publish_container", return_value="media_456"):
        result = poster.publish_reel(str(f), "caption", dry_run=False)

    assert result["media_id"] == "media_456"
    assert result["s3_url"] == "https://s3.example.com/reel.mp4"


def test_wait_for_container_timeout():
    with patch("poster.requests.get") as mock_get, \
         patch("poster.time.sleep"), \
         patch("poster.config.INSTAGRAM_ACCESS_TOKEN", "tok"):
        mock_get.return_value.json.return_value = {"status_code": "IN_PROGRESS"}
        mock_get.return_value.raise_for_status = MagicMock()
        with pytest.raises(TimeoutError):
            poster._wait_for_container("cid_123", max_wait=10)


def test_wait_for_container_error():
    with patch("poster.requests.get") as mock_get, \
         patch("poster.config.INSTAGRAM_ACCESS_TOKEN", "tok"):
        mock_get.return_value.json.return_value = {"status_code": "ERROR"}
        mock_get.return_value.raise_for_status = MagicMock()
        with pytest.raises(RuntimeError):
            poster._wait_for_container("cid_123", max_wait=60)