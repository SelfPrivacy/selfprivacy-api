# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import json
import pytest
from selfprivacy_api.restic_controller import ResticStates


def read_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


MOCKED_SNAPSHOTS = [
    {
        "time": "2021-12-06T09:05:04.224685677+03:00",
        "tree": "b76152d1e716d86d420407ead05d9911f2b6d971fe1589c12b63e4de65b14d4e",
        "paths": ["/var"],
        "hostname": "test-host",
        "username": "root",
        "id": "f96b428f1ca1252089ea3e25cd8ee33e63fb24615f1cc07559ba907d990d81c5",
        "short_id": "f96b428f",
    },
    {
        "time": "2021-12-08T07:42:06.998894055+03:00",
        "parent": "f96b428f1ca1252089ea3e25cd8ee33e63fb24615f1cc07559ba907d990d81c5",
        "tree": "8379b4fdc9ee3e9bb7c322f632a7bed9fc334b0258abbf4e7134f8fe5b3d61b0",
        "paths": ["/var"],
        "hostname": "test-host",
        "username": "root",
        "id": "db96b36efec97e5ba385099b43f9062d214c7312c20138aee7b8bd2c6cd8995a",
        "short_id": "db96b36e",
    },
]


class ResticControllerMock:
    snapshot_list = MOCKED_SNAPSHOTS
    state = ResticStates.INITIALIZED
    progress = 0
    error_message = None


@pytest.fixture
def mock_restic_controller(mocker):
    mock = mocker.patch(
        "selfprivacy_api.resources.services.restic.ResticController",
        autospec=True,
        return_value=ResticControllerMock,
    )
    return mock


class ResticControllerMockNoKey:
    snapshot_list = []
    state = ResticStates.NO_KEY
    progress = 0
    error_message = None


@pytest.fixture
def mock_restic_controller_no_key(mocker):
    mock = mocker.patch(
        "selfprivacy_api.resources.services.restic.ResticController",
        autospec=True,
        return_value=ResticControllerMockNoKey,
    )
    return mock


class ResticControllerNotInitialized:
    snapshot_list = []
    state = ResticStates.NOT_INITIALIZED
    progress = 0
    error_message = None


@pytest.fixture
def mock_restic_controller_not_initialized(mocker):
    mock = mocker.patch(
        "selfprivacy_api.resources.services.restic.ResticController",
        autospec=True,
        return_value=ResticControllerNotInitialized,
    )
    return mock


class ResticControllerInitializing:
    snapshot_list = []
    state = ResticStates.INITIALIZING
    progress = 0
    error_message = None


@pytest.fixture
def mock_restic_controller_initializing(mocker):
    mock = mocker.patch(
        "selfprivacy_api.resources.services.restic.ResticController",
        autospec=True,
        return_value=ResticControllerInitializing,
    )
    return mock


class ResticControllerBackingUp:
    snapshot_list = MOCKED_SNAPSHOTS
    state = ResticStates.BACKING_UP
    progress = 0.42
    error_message = None


@pytest.fixture
def mock_restic_controller_backing_up(mocker):
    mock = mocker.patch(
        "selfprivacy_api.resources.services.restic.ResticController",
        autospec=True,
        return_value=ResticControllerBackingUp,
    )
    return mock


class ResticControllerError:
    snapshot_list = MOCKED_SNAPSHOTS
    state = ResticStates.ERROR
    progress = 0
    error_message = "Error message"


@pytest.fixture
def mock_restic_controller_error(mocker):
    mock = mocker.patch(
        "selfprivacy_api.resources.services.restic.ResticController",
        autospec=True,
        return_value=ResticControllerError,
    )
    return mock


class ResticControllerRestoring:
    snapshot_list = MOCKED_SNAPSHOTS
    state = ResticStates.RESTORING
    progress = 0
    error_message = None


@pytest.fixture
def mock_restic_controller_restoring(mocker):
    mock = mocker.patch(
        "selfprivacy_api.resources.services.restic.ResticController",
        autospec=True,
        return_value=ResticControllerRestoring,
    )
    return mock


@pytest.fixture
def mock_restic_tasks(mocker):
    mock = mocker.patch(
        "selfprivacy_api.resources.services.restic.restic_tasks", autospec=True
    )
    return mock


@pytest.fixture
def undefined_settings(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "undefined.json")
    assert "backblaze" not in read_json(datadir / "undefined.json")
    return datadir


@pytest.fixture
def some_settings(mocker, datadir):
    mocker.patch(
        "selfprivacy_api.utils.USERDATA_FILE", new=datadir / "some_values.json"
    )
    assert "backblaze" in read_json(datadir / "some_values.json")
    assert read_json(datadir / "some_values.json")["backblaze"]["accountId"] == "ID"
    assert read_json(datadir / "some_values.json")["backblaze"]["accountKey"] == "KEY"
    assert read_json(datadir / "some_values.json")["backblaze"]["bucket"] == "BUCKET"
    return datadir


@pytest.fixture
def no_values(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "no_values.json")
    assert "backblaze" in read_json(datadir / "no_values.json")
    assert "accountId" not in read_json(datadir / "no_values.json")["backblaze"]
    assert "accountKey" not in read_json(datadir / "no_values.json")["backblaze"]
    assert "bucket" not in read_json(datadir / "no_values.json")["backblaze"]
    return datadir


def test_get_snapshots_unauthorized(client, mock_restic_controller, mock_restic_tasks):
    response = client.get("/services/restic/backup/list")
    assert response.status_code == 401


def test_get_snapshots(authorized_client, mock_restic_controller, mock_restic_tasks):
    response = authorized_client.get("/services/restic/backup/list")
    assert response.status_code == 200
    assert response.get_json() == MOCKED_SNAPSHOTS


def test_create_backup_unauthorized(client, mock_restic_controller, mock_restic_tasks):
    response = client.put("/services/restic/backup/create")
    assert response.status_code == 401


def test_create_backup(authorized_client, mock_restic_controller, mock_restic_tasks):
    response = authorized_client.put("/services/restic/backup/create")
    assert response.status_code == 200
    assert mock_restic_tasks.start_backup.call_count == 1


def test_create_backup_without_key(
    authorized_client, mock_restic_controller_no_key, mock_restic_tasks
):
    response = authorized_client.put("/services/restic/backup/create")
    assert response.status_code == 400
    assert mock_restic_tasks.start_backup.call_count == 0


def test_create_backup_initializing(
    authorized_client, mock_restic_controller_initializing, mock_restic_tasks
):
    response = authorized_client.put("/services/restic/backup/create")
    assert response.status_code == 400
    assert mock_restic_tasks.start_backup.call_count == 0


def test_create_backup_backing_up(
    authorized_client, mock_restic_controller_backing_up, mock_restic_tasks
):
    response = authorized_client.put("/services/restic/backup/create")
    assert response.status_code == 409
    assert mock_restic_tasks.start_backup.call_count == 0


def test_check_backup_status_unauthorized(
    client, mock_restic_controller, mock_restic_tasks
):
    response = client.get("/services/restic/backup/status")
    assert response.status_code == 401


def test_check_backup_status(
    authorized_client, mock_restic_controller, mock_restic_tasks
):
    response = authorized_client.get("/services/restic/backup/status")
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "INITIALIZED",
        "progress": 0,
        "error_message": None,
    }


def test_check_backup_status_no_key(
    authorized_client, mock_restic_controller_no_key, mock_restic_tasks
):
    response = authorized_client.get("/services/restic/backup/status")
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "NO_KEY",
        "progress": 0,
        "error_message": None,
    }


def test_check_backup_status_not_initialized(
    authorized_client, mock_restic_controller_not_initialized, mock_restic_tasks
):
    response = authorized_client.get("/services/restic/backup/status")
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "NOT_INITIALIZED",
        "progress": 0,
        "error_message": None,
    }


def test_check_backup_status_initializing(
    authorized_client, mock_restic_controller_initializing, mock_restic_tasks
):
    response = authorized_client.get("/services/restic/backup/status")
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "INITIALIZING",
        "progress": 0,
        "error_message": None,
    }


def test_check_backup_status_backing_up(
    authorized_client, mock_restic_controller_backing_up
):
    response = authorized_client.get("/services/restic/backup/status")
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "BACKING_UP",
        "progress": 0.42,
        "error_message": None,
    }


def test_check_backup_status_error(
    authorized_client, mock_restic_controller_error, mock_restic_tasks
):
    response = authorized_client.get("/services/restic/backup/status")
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ERROR",
        "progress": 0,
        "error_message": "Error message",
    }


def test_check_backup_status_restoring(
    authorized_client, mock_restic_controller_restoring, mock_restic_tasks
):
    response = authorized_client.get("/services/restic/backup/status")
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "RESTORING",
        "progress": 0,
        "error_message": None,
    }


def test_reload_unauthenticated(client, mock_restic_controller, mock_restic_tasks):
    response = client.get("/services/restic/backup/reload")
    assert response.status_code == 401


def test_backup_reload(authorized_client, mock_restic_controller, mock_restic_tasks):
    response = authorized_client.get("/services/restic/backup/reload")
    assert response.status_code == 200
    assert mock_restic_tasks.load_snapshots.call_count == 1


def test_backup_restore_unauthorized(client, mock_restic_controller, mock_restic_tasks):
    response = client.put("/services/restic/backup/restore")
    assert response.status_code == 401


def test_backup_restore_without_backup_id(
    authorized_client, mock_restic_controller, mock_restic_tasks
):
    response = authorized_client.put("/services/restic/backup/restore", json={})
    assert response.status_code == 400
    assert mock_restic_tasks.restore_from_backup.call_count == 0


def test_backup_restore_with_nonexistent_backup_id(
    authorized_client, mock_restic_controller, mock_restic_tasks
):
    response = authorized_client.put(
        "/services/restic/backup/restore", json={"backupId": "nonexistent"}
    )
    assert response.status_code == 404
    assert mock_restic_tasks.restore_from_backup.call_count == 0


def test_backup_restore_when_no_key(
    authorized_client, mock_restic_controller_no_key, mock_restic_tasks
):
    response = authorized_client.put(
        "/services/restic/backup/restore", json={"backupId": "f96b428f"}
    )
    assert response.status_code == 400
    assert mock_restic_tasks.restore_from_backup.call_count == 0


def test_backup_restore_when_not_initialized(
    authorized_client, mock_restic_controller_not_initialized, mock_restic_tasks
):
    response = authorized_client.put(
        "/services/restic/backup/restore", json={"backupId": "f96b428f"}
    )
    assert response.status_code == 400
    assert mock_restic_tasks.restore_from_backup.call_count == 0


def test_backup_restore_when_initializing(
    authorized_client, mock_restic_controller_initializing, mock_restic_tasks
):
    response = authorized_client.put(
        "/services/restic/backup/restore", json={"backupId": "f96b428f"}
    )
    assert response.status_code == 400
    assert mock_restic_tasks.restore_from_backup.call_count == 0


def test_backup_restore_when_backing_up(
    authorized_client, mock_restic_controller_backing_up, mock_restic_tasks
):
    response = authorized_client.put(
        "/services/restic/backup/restore", json={"backupId": "f96b428f"}
    )
    assert response.status_code == 409
    assert mock_restic_tasks.restore_from_backup.call_count == 0


def test_backup_restore_when_restoring(
    authorized_client, mock_restic_controller_restoring, mock_restic_tasks
):
    response = authorized_client.put(
        "/services/restic/backup/restore", json={"backupId": "f96b428f"}
    )
    assert response.status_code == 409
    assert mock_restic_tasks.restore_from_backup.call_count == 0


def test_backup_restore_when_error(
    authorized_client, mock_restic_controller_error, mock_restic_tasks
):
    response = authorized_client.put(
        "/services/restic/backup/restore", json={"backupId": "f96b428f"}
    )
    assert response.status_code == 200
    assert mock_restic_tasks.restore_from_backup.call_count == 1


def test_backup_restore(authorized_client, mock_restic_controller, mock_restic_tasks):
    response = authorized_client.put(
        "/services/restic/backup/restore", json={"backupId": "f96b428f"}
    )
    assert response.status_code == 200
    assert mock_restic_tasks.restore_from_backup.call_count == 1


def test_set_backblaze_config_unauthorized(
    client, mock_restic_controller, mock_restic_tasks, some_settings
):
    response = client.put("/services/restic/backblaze/config")
    assert response.status_code == 401
    assert mock_restic_tasks.update_keys_from_userdata.call_count == 0


def test_set_backblaze_config_without_arguments(
    authorized_client, mock_restic_controller, mock_restic_tasks, some_settings
):
    response = authorized_client.put("/services/restic/backblaze/config")
    assert response.status_code == 400
    assert mock_restic_tasks.update_keys_from_userdata.call_count == 0


def test_set_backblaze_config_without_all_values(
    authorized_client, mock_restic_controller, mock_restic_tasks, some_settings
):
    response = authorized_client.put(
        "/services/restic/backblaze/config",
        json={"accountId": "123", "applicationKey": "456"},
    )
    assert response.status_code == 400
    assert mock_restic_tasks.update_keys_from_userdata.call_count == 0


def test_set_backblaze_config(
    authorized_client, mock_restic_controller, mock_restic_tasks, some_settings
):
    response = authorized_client.put(
        "/services/restic/backblaze/config",
        json={"accountId": "123", "accountKey": "456", "bucket": "789"},
    )
    assert response.status_code == 200
    assert mock_restic_tasks.update_keys_from_userdata.call_count == 1
    assert read_json(some_settings / "some_values.json")["backblaze"] == {
        "accountId": "123",
        "accountKey": "456",
        "bucket": "789",
    }


def test_set_backblaze_config_on_undefined(
    authorized_client, mock_restic_controller, mock_restic_tasks, undefined_settings
):
    response = authorized_client.put(
        "/services/restic/backblaze/config",
        json={"accountId": "123", "accountKey": "456", "bucket": "789"},
    )
    assert response.status_code == 200
    assert mock_restic_tasks.update_keys_from_userdata.call_count == 1
    assert read_json(undefined_settings / "undefined.json")["backblaze"] == {
        "accountId": "123",
        "accountKey": "456",
        "bucket": "789",
    }


def test_set_backblaze_config_on_no_values(
    authorized_client, mock_restic_controller, mock_restic_tasks, no_values
):
    response = authorized_client.put(
        "/services/restic/backblaze/config",
        json={"accountId": "123", "accountKey": "456", "bucket": "789"},
    )
    assert response.status_code == 200
    assert mock_restic_tasks.update_keys_from_userdata.call_count == 1
    assert read_json(no_values / "no_values.json")["backblaze"] == {
        "accountId": "123",
        "accountKey": "456",
        "bucket": "789",
    }
