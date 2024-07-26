import pytest
import shutil

from typing import Generator
from os import mkdir

from selfprivacy_api.utils.block_devices import BlockDevices

import selfprivacy_api.services as service_module
from selfprivacy_api.services import ServiceManager
from selfprivacy_api.services.service import Service, ServiceStatus
from selfprivacy_api.services.test_service import DummyService

from tests.common import generate_service_query
from tests.test_graphql.common import assert_empty, assert_ok, get_data
from tests.test_graphql.test_system_nixos_tasks import prepare_nixos_rebuild_calls

from tests.test_dkim import dkim_file

LSBLK_BLOCKDEVICES_DICTS = [
    {
        "name": "sda1",
        "path": "/dev/sda1",
        "fsavail": "4614107136",
        "fssize": "19814920192",
        "fstype": "ext4",
        "fsused": "14345314304",
        "mountpoints": ["/nix/store", "/"],
        "label": None,
        "uuid": "ec80c004-baec-4a2c-851d-0e1807135511",
        "size": 20210236928,
        "model": None,
        "serial": None,
        "type": "part",
    },
    {
        "name": "sda2",
        "path": "/dev/sda2",
        "fsavail": "4614107136",
        "fssize": "19814920192",
        "fstype": "ext4",
        "fsused": "14345314304",
        "mountpoints": ["/home"],
        "label": None,
        "uuid": "deadbeef-baec-4a2c-851d-0e1807135511",
        "size": 20210236928,
        "model": None,
        "serial": None,
        "type": "part",
    },
]


@pytest.fixture()
def mock_lsblk_devices(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.block_devices.BlockDevices.lsblk_device_dicts",
        autospec=True,
        return_value=LSBLK_BLOCKDEVICES_DICTS,
    )
    BlockDevices().update()
    assert BlockDevices().lsblk_device_dicts() == LSBLK_BLOCKDEVICES_DICTS
    devices = BlockDevices().get_block_devices()

    assert len(devices) == 2

    names = [device.name for device in devices]
    assert "sda1" in names
    assert "sda2" in names
    return mock


@pytest.fixture()
def dummy_service_with_binds(dummy_service, mock_lsblk_devices, volume_folders):
    binds = dummy_service.binds()
    for bind in binds:
        path = bind.binding_path
        shutil.move(bind.binding_path, bind.location_at_volume())
        mkdir(bind.binding_path)

        bind.ensure_ownership()
        bind.validate()

        bind.bind()
    return dummy_service


@pytest.fixture()
def only_dummy_service(dummy_service) -> Generator[DummyService, None, None]:
    # because queries to services that are not really there error out
    back_copy = service_module.services.copy()
    service_module.services.clear()
    service_module.services.append(dummy_service)
    yield dummy_service
    service_module.services.clear()
    service_module.services.extend(back_copy)


@pytest.fixture
def only_dummy_service_and_api(
    only_dummy_service, generic_userdata, dkim_file
) -> Generator[DummyService, None, None]:
    service_module.services.append(ServiceManager())
    return only_dummy_service


@pytest.fixture()
def mock_check_volume(mocker):
    mock = mocker.patch(
        "selfprivacy_api.services.service.check_volume",
        autospec=True,
        return_value=None,
    )
    return mock


API_START_MUTATION = """
mutation TestStartService($service_id: String!) {
    services {
        startService(serviceId: $service_id) {
            success
            message
            code
            service {
                id
                status
            }
        }
    }
}
"""

API_RESTART_MUTATION = """
mutation TestRestartService($service_id: String!) {
    services {
        restartService(serviceId: $service_id) {
            success
            message
            code
            service {
                id
                status
            }
        }
    }
}
"""

API_ENABLE_MUTATION = """
mutation TestStartService($service_id: String!) {
    services {
        enableService(serviceId: $service_id) {
            success
            message
            code
            service {
                id
                isEnabled
            }
        }
    }
}
"""
API_DISABLE_MUTATION = """
mutation TestStartService($service_id: String!) {
    services {
        disableService(serviceId: $service_id) {
            success
            message
            code
            service {
                id
                isEnabled
            }
        }
    }
}
"""

API_STOP_MUTATION = """
mutation TestStopService($service_id: String!) {
    services {
        stopService(serviceId: $service_id) {
            success
            message
            code
            service {
                id
                status
            }
        }
    }
}

"""
API_SERVICES_QUERY = """
allServices {
    id
    status
    isEnabled
    url
}
"""

API_MOVE_MUTATION = """
mutation TestMoveService($input: MoveServiceInput!) {
    services {
        moveService(input: $input) {
            success
            message
            code
            job {
                uid
                status
            }
            service {
                id
                status
            }
        }
    }
}
"""


def assert_notfound(data):
    assert_errorcode(data, 404)


def assert_errorcode(data, errorcode):
    assert data["code"] == errorcode
    assert data["success"] is False
    assert data["message"] is not None


def api_enable(client, service: Service) -> dict:
    return api_enable_by_name(client, service.get_id())


def api_enable_by_name(client, service_id: str) -> dict:
    response = client.post(
        "/graphql",
        json={
            "query": API_ENABLE_MUTATION,
            "variables": {"service_id": service_id},
        },
    )
    return response


def api_disable(client, service: Service) -> dict:
    return api_disable_by_name(client, service.get_id())


def api_disable_by_name(client, service_id: str) -> dict:
    response = client.post(
        "/graphql",
        json={
            "query": API_DISABLE_MUTATION,
            "variables": {"service_id": service_id},
        },
    )
    return response


def api_start(client, service: Service) -> dict:
    return api_start_by_name(client, service.get_id())


def api_start_by_name(client, service_id: str) -> dict:
    response = client.post(
        "/graphql",
        json={
            "query": API_START_MUTATION,
            "variables": {"service_id": service_id},
        },
    )
    return response


def api_move(client, service: Service, location: str) -> dict:
    return api_move_by_name(client, service.get_id(), location)


def api_move_by_name(client, service_id: str, location: str) -> dict:
    response = client.post(
        "/graphql",
        json={
            "query": API_MOVE_MUTATION,
            "variables": {
                "input": {
                    "serviceId": service_id,
                    "location": location,
                }
            },
        },
    )
    return response


def api_restart(client, service: Service) -> dict:
    return api_restart_by_name(client, service.get_id())


def api_restart_by_name(client, service_id: str) -> dict:
    response = client.post(
        "/graphql",
        json={
            "query": API_RESTART_MUTATION,
            "variables": {"service_id": service_id},
        },
    )
    return response


def api_stop(client, service: Service) -> dict:
    return api_stop_by_name(client, service.get_id())


def api_stop_by_name(client, service_id: str) -> dict:
    response = client.post(
        "/graphql",
        json={
            "query": API_STOP_MUTATION,
            "variables": {"service_id": service_id},
        },
    )
    return response


def api_all_services(authorized_client):
    response = api_all_services_raw(authorized_client)
    data = get_data(response)
    result = data["services"]["allServices"]
    assert result is not None
    return result


def api_all_services_raw(client):
    return client.post(
        "/graphql",
        json={"query": generate_service_query([API_SERVICES_QUERY])},
    )


def api_service(authorized_client, service: Service):
    id = service.get_id()
    for _service in api_all_services(authorized_client):
        if _service["id"] == id:
            return _service


def test_get_services(authorized_client, only_dummy_service):
    services = api_all_services(authorized_client)
    assert len(services) == 1

    api_dummy_service = services[0]
    assert api_dummy_service["id"] == "testservice"
    assert api_dummy_service["status"] == ServiceStatus.ACTIVE.value
    assert api_dummy_service["isEnabled"] is True
    assert api_dummy_service["url"] == "https://test.test-domain.tld"


def test_enable_return_value(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_enable(authorized_client, dummy_service)
    data = get_data(mutation_response)["services"]["enableService"]
    assert_ok(data)
    service = data["service"]
    assert service["id"] == dummy_service.get_id()
    assert service["isEnabled"] == True


def test_disable_return_value(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_disable(authorized_client, dummy_service)
    data = get_data(mutation_response)["services"]["disableService"]
    assert_ok(data)
    service = data["service"]
    assert service["id"] == dummy_service.get_id()
    assert service["isEnabled"] == False


def test_start_return_value(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_start(authorized_client, dummy_service)
    data = get_data(mutation_response)["services"]["startService"]
    assert_ok(data)
    service = data["service"]
    assert service["id"] == dummy_service.get_id()
    assert service["status"] == ServiceStatus.ACTIVE.value


def test_restart(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    dummy_service.set_delay(0.3)
    mutation_response = api_restart(authorized_client, dummy_service)
    data = get_data(mutation_response)["services"]["restartService"]
    assert_ok(data)
    service = data["service"]
    assert service["id"] == dummy_service.get_id()
    assert service["status"] == ServiceStatus.RELOADING.value


def test_stop_return_value(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_stop(authorized_client, dummy_service)
    data = get_data(mutation_response)["services"]["stopService"]
    assert_ok(data)
    service = data["service"]
    assert service["id"] == dummy_service.get_id()
    assert service["status"] == ServiceStatus.INACTIVE.value


def test_allservices_unauthorized(client, only_dummy_service):
    dummy_service = only_dummy_service
    response = api_all_services_raw(client)

    assert response.status_code == 200
    assert response.json().get("data") is None


def test_start_unauthorized(client, only_dummy_service):
    dummy_service = only_dummy_service
    response = api_start(client, dummy_service)
    assert_empty(response)


def test_restart_unauthorized(client, only_dummy_service):
    dummy_service = only_dummy_service
    response = api_restart(client, dummy_service)
    assert_empty(response)


def test_stop_unauthorized(client, only_dummy_service):
    dummy_service = only_dummy_service
    response = api_stop(client, dummy_service)
    assert_empty(response)


def test_enable_unauthorized(client, only_dummy_service):
    dummy_service = only_dummy_service
    response = api_enable(client, dummy_service)
    assert_empty(response)


def test_disable_unauthorized(client, only_dummy_service):
    dummy_service = only_dummy_service
    response = api_disable(client, dummy_service)
    assert_empty(response)


def test_move_unauthorized(client, only_dummy_service):
    dummy_service = only_dummy_service
    response = api_move(client, dummy_service, "sda1")
    assert_empty(response)


def test_start_nonexistent(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_start_by_name(authorized_client, "bogus_service")
    data = get_data(mutation_response)["services"]["startService"]
    assert_notfound(data)

    assert data["service"] is None


def test_restart_nonexistent(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_restart_by_name(authorized_client, "bogus_service")
    data = get_data(mutation_response)["services"]["restartService"]
    assert_notfound(data)

    assert data["service"] is None


def test_stop_nonexistent(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_stop_by_name(authorized_client, "bogus_service")
    data = get_data(mutation_response)["services"]["stopService"]
    assert_notfound(data)

    assert data["service"] is None


def test_enable_nonexistent(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_enable_by_name(authorized_client, "bogus_service")
    data = get_data(mutation_response)["services"]["enableService"]
    assert_notfound(data)

    assert data["service"] is None


def test_disable_nonexistent(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_disable_by_name(authorized_client, "bogus_service")
    data = get_data(mutation_response)["services"]["disableService"]
    assert_notfound(data)

    assert data["service"] is None


def test_stop_start(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service

    api_dummy_service = api_all_services(authorized_client)[0]
    assert api_dummy_service["status"] == ServiceStatus.ACTIVE.value

    # attempting to start an already started service
    api_start(authorized_client, dummy_service)
    api_dummy_service = api_all_services(authorized_client)[0]
    assert api_dummy_service["status"] == ServiceStatus.ACTIVE.value

    api_stop(authorized_client, dummy_service)
    api_dummy_service = api_all_services(authorized_client)[0]
    assert api_dummy_service["status"] == ServiceStatus.INACTIVE.value

    # attempting to stop an already stopped service
    api_stop(authorized_client, dummy_service)
    api_dummy_service = api_all_services(authorized_client)[0]
    assert api_dummy_service["status"] == ServiceStatus.INACTIVE.value

    api_start(authorized_client, dummy_service)
    api_dummy_service = api_all_services(authorized_client)[0]
    assert api_dummy_service["status"] == ServiceStatus.ACTIVE.value


def test_disable_enable(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service

    api_dummy_service = api_all_services(authorized_client)[0]
    assert api_dummy_service["isEnabled"] is True

    # attempting to enable an already enableed service
    api_enable(authorized_client, dummy_service)
    api_dummy_service = api_all_services(authorized_client)[0]
    assert api_dummy_service["isEnabled"] is True
    assert api_dummy_service["status"] == ServiceStatus.ACTIVE.value

    api_disable(authorized_client, dummy_service)
    api_dummy_service = api_all_services(authorized_client)[0]
    assert api_dummy_service["isEnabled"] is False
    assert api_dummy_service["status"] == ServiceStatus.ACTIVE.value

    # attempting to disable an already disableped service
    api_disable(authorized_client, dummy_service)
    api_dummy_service = api_all_services(authorized_client)[0]
    assert api_dummy_service["isEnabled"] is False
    assert api_dummy_service["status"] == ServiceStatus.ACTIVE.value

    api_enable(authorized_client, dummy_service)
    api_dummy_service = api_all_services(authorized_client)[0]
    assert api_dummy_service["isEnabled"] is True
    assert api_dummy_service["status"] == ServiceStatus.ACTIVE.value


def test_move_immovable(authorized_client, dummy_service_with_binds):
    dummy_service = dummy_service_with_binds
    dummy_service.set_movable(False)
    root = BlockDevices().get_root_block_device()
    mutation_response = api_move(authorized_client, dummy_service, root.name)
    data = get_data(mutation_response)["services"]["moveService"]
    assert_errorcode(data, 400)
    try:
        assert "not movable" in data["message"]
    except AssertionError:
        raise ValueError("wrong type of error?: ", data["message"])

    # is there a meaning in returning the service in this?
    assert data["service"] is not None
    assert data["job"] is None


def test_move_no_such_service(authorized_client, only_dummy_service):
    mutation_response = api_move_by_name(authorized_client, "bogus_service", "sda1")
    data = get_data(mutation_response)["services"]["moveService"]
    assert_errorcode(data, 404)

    assert data["service"] is None
    assert data["job"] is None


def test_move_no_such_volume(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_move(authorized_client, dummy_service, "bogus_volume")
    data = get_data(mutation_response)["services"]["moveService"]
    assert_notfound(data)

    assert data["service"] is None
    assert data["job"] is None


def test_move_same_volume(authorized_client, dummy_service):
    # dummy_service = only_dummy_service

    # we need a drive that actually exists
    root_volume = BlockDevices().get_root_block_device()
    dummy_service.set_simulated_moves(False)
    dummy_service.set_drive(root_volume.name)

    mutation_response = api_move(authorized_client, dummy_service, root_volume.name)
    data = get_data(mutation_response)["services"]["moveService"]
    assert_errorcode(data, 400)

    # is there a meaning in returning the service in this?
    assert data["service"] is not None
    # We do not create a job if task is not created
    assert data["job"] is None


def test_graphql_move_service_without_folders_on_old_volume(
    authorized_client,
    generic_userdata,
    mock_lsblk_devices,
    dummy_service: DummyService,
):
    """
    Situation when you have folders in the filetree but they are not mounted
    but just folders
    """

    target = "sda1"
    BlockDevices().update()
    assert BlockDevices().get_block_device(target) is not None

    dummy_service.set_simulated_moves(False)
    dummy_service.set_drive("sda2")
    mutation_response = api_move(authorized_client, dummy_service, target)

    data = get_data(mutation_response)["services"]["moveService"]
    assert_errorcode(data, 400)
    assert "sda2/test_service is not found" in data["message"]


def test_move_empty(
    authorized_client, generic_userdata, mock_check_volume, dummy_service, fp
):
    """
    A reregister of uninitialized service with no data.
    No binds in place yet, and no rebuilds should happen.
    """

    origin = "sda1"
    target = "sda2"
    assert BlockDevices().get_block_device(target) is not None
    assert BlockDevices().get_block_device(origin) is not None

    dummy_service.set_drive(origin)
    dummy_service.set_simulated_moves(False)
    dummy_service.disable()

    unit_name = "sp-nixos-rebuild.service"
    rebuild_command = ["systemctl", "start", unit_name]
    prepare_nixos_rebuild_calls(fp, unit_name)

    # We will NOT be mounting and remounting folders
    mount_command = ["mount", fp.any()]
    unmount_command = ["umount", fp.any()]
    fp.pass_command(mount_command, 2)
    fp.pass_command(unmount_command, 2)

    # We will NOT be changing ownership
    chown_command = ["chown", fp.any()]
    fp.pass_command(chown_command, 2)

    # We have virtual binds encapsulating our understanding where this should go.
    assert len(dummy_service.binds()) == 2

    # Remove all folders
    for folder in dummy_service.get_folders():
        shutil.rmtree(folder)

    # They are virtual and unaffected by folder removal
    assert len(dummy_service.binds()) == 2

    mutation_response = api_move(authorized_client, dummy_service, target)

    data = get_data(mutation_response)["services"]["moveService"]
    assert_ok(data)
    assert data["service"] is not None

    assert fp.call_count(rebuild_command) == 0
    assert fp.call_count(mount_command) == 0
    assert fp.call_count(unmount_command) == 0
    assert fp.call_count(chown_command) == 0


def test_graphql_move_service(
    authorized_client, generic_userdata, mock_check_volume, dummy_service_with_binds, fp
):
    dummy_service = dummy_service_with_binds

    origin = "sda1"
    target = "sda2"
    assert BlockDevices().get_block_device(target) is not None
    assert BlockDevices().get_block_device(origin) is not None

    dummy_service.set_drive(origin)
    dummy_service.set_simulated_moves(False)

    unit_name = "sp-nixos-rebuild.service"
    rebuild_command = ["systemctl", "start", unit_name]
    prepare_nixos_rebuild_calls(fp, unit_name)

    # We will be mounting and remounting folders
    mount_command = ["mount", fp.any()]
    unmount_command = ["umount", fp.any()]
    fp.pass_command(mount_command, 2)
    fp.pass_command(unmount_command, 2)

    # We will be changing ownership
    chown_command = ["chown", fp.any()]
    fp.pass_command(chown_command, 2)

    mutation_response = api_move(authorized_client, dummy_service, target)

    data = get_data(mutation_response)["services"]["moveService"]
    assert_ok(data)
    assert data["service"] is not None

    assert fp.call_count(rebuild_command) == 1
    assert fp.call_count(mount_command) == 2
    assert fp.call_count(unmount_command) == 2
    assert fp.call_count(chown_command) == 2


def test_mailservice_cannot_enable_disable(authorized_client):
    mailservice = ServiceManager.get_service_by_id("simple-nixos-mailserver")

    mutation_response = api_enable(authorized_client, mailservice)
    data = get_data(mutation_response)["services"]["enableService"]
    assert_errorcode(data, 400)
    # TODO?: we cannot convert mailservice to graphql Service without /var/domain yet
    # assert data["service"] is not None

    mutation_response = api_disable(authorized_client, mailservice)
    data = get_data(mutation_response)["services"]["disableService"]
    assert_errorcode(data, 400)
    # assert data["service"] is not None
