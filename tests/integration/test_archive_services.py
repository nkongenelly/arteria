import copy

from arteria import __version__
from tests.fixtures.integration_fixtures import *
from arteria.models.config import Config
@pytest.fixture()
def config():
    """
    Setup a temporary directory to be monitored by the service.
    """
    with tempfile.TemporaryDirectory(delete=False) as monitored_dir:
        config_dict = {
            "monitored_directories": [monitored_dir],
            "port": 8080,
            "completed_marker_grace_minutes": 0,
            "logger_config_file": "tests/resources/config/logger.config"
        }
        # TODO: Update the schema name for archive services
        yield Config.new(config_dict, exist_ok=False, schema="")
        del Config._instance


@pytest.fixture()
def archive_db_post_data():
    yield {
        "description": "e44f32b4-c8d1-46de-a487-4a5d577c8820",
        "host": "mm-xart002.medsci.uu.se",
        "path": "/data/mm-xart002/runfolders/20231108_LH00179_0011_BFCTEST1_archive",
        "timestamp": "2024-01-23T14:59:41.898710"
    }


@pytest.fixture()
def archive_db_response(request):
    status = request.param.get("status", "")
    step = request.param.get("step", "_step")
    yield {
        "status": status,
        f"{step}":
            {
              "id": 79,
              "timestamp": "2024-01-23T14:59:41.898710",
              "description": "e44f32b4-c8d1-46de-a487-4a5d577c8820",
              "path": "/data/mm-xart002/runfolders/20231108_LH00179_0011_BFCTEST1_archive",
              "host": "mm-xart002.medsci.uu.se"
            }
        }


@pytest.fixture()
def archive_upload_response():
    yield {
        "job_id": 16,
        "service_version": "1.1.1",
        "link": "http://mm-xart002:10600/api/1.0/status/16",
        "state": "started",
        "dsmc_log_dir": "/var/log/arteria/archive-upload/dsmc_20231108_LH00179_0011_BFCTEST1_archive",
        "archive_path": "/data/mm-xart002/runfolders/20231108_LH00179_0011_BFCTEST1_archive",
        "archive_description": "e44f32b4-c8d1-46de-a487-4a5d577c8820",
        "archive_host": "mm-xart002.medsci.uu.se"
    }


@pytest.fixture()
def archive_verify_response(request):
    action = request.param.get("action", "")
    yield {
        "status":  "done",
        "job_id": 16,
        "link": "http://mm-xart002:10600/api/1.0/verify/16",
        "path": "/data/mm-xart002/runfolders/20231108_LH00179_0011_BFCTEST1_archive",
        "action": action # "verify" or "download"
    }
async def test_version(client, caplog):
    async with client.request("GET", "/version") as resp:
        assert resp.status == 200
        content = await resp.json()

    assert content == {"version": __version__}
    # Test logger is initialized and used
    assert 'INFO' in caplog.text
    assert 'GET /version' in caplog.text


@pytest.mark.parametrize("archive_db_response", [{"status": "created", "step": "upload"}], indirect=True)
async def test_upload_archive_db(client, archive_db_post_data, archive_db_response):
    async with client.request(
            "POST",
            "/upload",
            data=archive_db_post_data
    ) as resp:
        assert resp.status == 200
        content = await resp.json()

        assert content == archive_db_response


@pytest.mark.parametrize("archive_db_response", [{"status": "created", "step": "verification"}], indirect=True)
async def test_verification_archive_db(client, archive_db_post_data, archive_db_response):
    async with client.request(
            "POST",
            "/verification",
            data=archive_db_post_data
    ) as resp:
        assert resp.status == 200
        content = await resp.json()

        assert content == archive_db_response


@pytest.mark.parametrize("archive_db_response", [{"status": "unverified", "step": "archive"}], indirect=True)
async def test_randomarchive_archive_db(client, archive_db_post_data, archive_db_response: object):
    async with client.request(
            "POST",
            "/randomarchive",
            data={
                "safety_margin": "3",
                "age": "7",
                "host": "biotank",
                "today": "2024-01-23T14:59:41.898710"
            }
    ) as resp:
        assert resp.status == 200
        content = await resp.json()

        response = copy.deepcopy(archive_db_response)
        response['archive'] = "20231108_LH00179_0011_BFCTEST1_archive"
        response['host'] = "biotank-staging"
        assert content == response

@pytest.mark.parametrize("archive_db_response", [{"status": "scheduled", "step": "removal"}], indirect=True)
async def test_removal_archive_db(client, archive_db_post_data, archive_db_response: object):
    async with client.request(
            "POST",
            "/removal",
            data={
                "description": "e44f32b4-c8d1-46de-a487-4a5d577c8820",
                "action": "set_removable" # or "set_removed"
            }
    ) as resp:
        assert resp.status == 200
        content = await resp.json()

        response = copy.deepcopy(archive_db_response)
        response['done'] = False,  # False = archive has been scheduled for removal; True = archive has been removed.
        assert content == response

@pytest.mark.parametrize("archive_db_response", [{"step": "archives"}], indirect=True)
async def test_get_view_archive_db(client, archive_db_response: object):
    async with client.request("GET", "/view/79") as resp:
        assert resp.status == 200
        content = await resp.json()

        response = copy.deepcopy(archive_db_response)
        del response['id']
        response['uploaded'] = response['timesstamp']
        del response['timesstamp']
        response['verified'] = None
        response['removed'] = None
        assert content == response


async def test_upload_archive_upload(client, archive_upload_response):
    async with client.request(
            "POST",
            "/upload/20231108_LH00179_0011_BFCTEST1_archive"
    ) as resp:
        assert resp.status == 200
        content = await resp.json()

        assert content == archive_upload_response


async def test_upload_archive_upload_no_file(client):
    async with client.request(
            "POST",
            "/upload/NO_FILE_TO_UPLOAD_archive"
    ) as resp:
        assert resp.status == 200
        content = await resp.json()

        response = {
                      "service_version": "1.1.1",
                      "state": "error",
                      "dsmc_log_dir": "/var/log/arteria/archive-upload/dsmc_20231108_LH00179_0011_BFCTEST1_archive",
                    }
        assert content == response


async def test_get_status_archive(client):
    async with client.request("POST", "/status/16") as resp:
        assert resp.status == 200
        content = await resp.json()

        response = {
            "state": "started",
            "job_id": 1
        }
        assert content == response


async def test_reupload_archive_upload(client, archive_upload_response):
    async with client.request(
            "POST",
            "/reupload/20231108_LH00179_0011_BFCTEST1_archive",
    ) as resp:
        assert resp.status == 200
        content = await resp.json()

        assert content == archive_upload_response


async def test_reupload_archive_upload_no_file(client):
    async with client.request(
            "POST",
            "/reupload/NO_FILE_TO_UPLOAD_archive"
    ) as resp:
        assert resp.status == 200
        content = await resp.json()

        response = {
                      "service_version": "1.1.1",
                      "state": "error",
                      "dsmc_log_dir": "/var/log/arteria/archive-upload/dsmc_20231108_LH00179_0011_BFCTEST1_archive",
                    }
        assert content == response


async def test_createdir_archive_upload(client, archive_upload_response):
    async with client.request(
            "POST",
            "/create_dir/20231108_LH00179_0011_BFCTEST1_archive",
            data={
                "exclude_dirs": ["Thumbnail_Images"],
                "required_dirs": ["Data/Intensities"],
                "remove": False,
            }
    ) as resp:
        assert resp.status == 200
        content = await resp.json()

        response = copy.deepcopy(archive_upload_response)
        [response.pop(k, None) for k in ('dsmc_log_dir', 'archive_path', 'archive_description', 'archive_host')]
        assert content == response


async def test_gen_checksums_archive_upload(client, archive_upload_response):
    async with client.request(
            "POST",
            "/gen_checksums/20231108_LH00179_0011_BFCTEST1_archive"
    ) as resp:
        assert resp.status == 200
        content = await resp.json()

        response = copy.deepcopy(archive_upload_response)
        [response.pop(k, None) for k in ('dsmc_log_dir', 'archive_path', 'archive_description', 'archive_host')]
        assert content == response


async def test_compress_archive_archive_upload(client, archive_upload_response):
    async with client.request(
            "POST",
            "/compress_archive/20231108_LH00179_0011_BFCTEST1_archive"
    ) as resp:
        assert resp.status == 200
        content = await resp.json()

        response = copy.deepcopy(archive_upload_response)
        [response.pop(k, None) for k in ('dsmc_log_dir', 'archive_path', 'archive_description', 'archive_host')]
        assert content == response


@pytest.mark.parametrize("archive_verify_response", [{"action": "verify"}], indirect=True)
async def test_verify_archive_verify(client, archive_verify_response):
    verify_data = {
              "archive": "180718_M04499_0151_000000000-BWFHW_archive",
              "description": "5b7bb3e6-c982-4cac-a8b2-a3f903801eac",
              "host": "mm-xart002.medsci.uu.se",
              "path": "/data/mm-xart002/runfolders/180718_M04499_0151_000000000-BWFHW_archive"
            }
    async with client.request(
            "POST",
            "/verify",
            data=verify_data
    ) as resp:
        assert resp.status == 200
        content = await resp.json()

        assert content == archive_verify_response


@pytest.mark.parametrize("archive_verify_response", [{"action": "download"}], indirect=True)
async def test_download_archive_verify(client, archive_verify_response):
    verify_data = {
              "archive": "180718_M04499_0151_000000000-BWFHW_archive",
              "description": "5b7bb3e6-c982-4cac-a8b2-a3f903801eac",
              "host": "mm-xart002.medsci.uu.se",
              "path": "/data/mm-xart002/runfolders/180718_M04499_0151_000000000-BWFHW_archive"
            }
    async with client.request(
            "POST",
            "/download",
            data=verify_data
    ) as resp:
        assert resp.status == 200
        content = await resp.json()

        assert content == archive_verify_response


async def test_get_status_archive_verify(client):
    async with client.request("GET", "/status/16") as resp:
        assert resp.status == 200
        content = await resp.json()

        response = {
              "status":  "done",
              "msg": "Job {job_id} has returned with result: {job_result['msg']}",
            }
        assert content == response

