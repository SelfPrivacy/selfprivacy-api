import pytest
from typing import Generator

from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.utils.block_devices import BlockDevices

from selfprivacy_api.graphql.mutations.services_mutations import ServicesMutations
import selfprivacy_api.services as service_module
from selfprivacy_api.services import get_service_by_id
from selfprivacy_api.services.service import Service, ServiceStatus
from selfprivacy_api.services.test_service import DummyService

import tests.test_graphql.test_api_backup
from tests.test_common import raw_dummy_service, dummy_service
from tests.common import generate_service_query
from tests.test_graphql.test_api_backup import assert_ok, get_data


@pytest.fixture()
def only_dummy_service(dummy_service) -> Generator[DummyService, None, None]:
    # because queries to services that are not really there error out
    back_copy = service_module.services.copy()
    service_module.services.clear()
    service_module.services.append(dummy_service)
    yield dummy_service
    service_module.services.clear()
    service_module.services.extend(back_copy)


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
    mutation_response = api_start(client, dummy_service)

    assert mutation_response.status_code == 200
    assert mutation_response.json().get("data") is None


def test_restart_unauthorized(client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_restart(client, dummy_service)

    assert mutation_response.status_code == 200
    assert mutation_response.json().get("data") is None


def test_stop_unauthorized(client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_stop(client, dummy_service)

    assert mutation_response.status_code == 200
    assert mutation_response.json().get("data") is None


def test_enable_unauthorized(client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_enable(client, dummy_service)

    assert mutation_response.status_code == 200
    assert mutation_response.json().get("data") is None


def test_disable_unauthorized(client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_disable(client, dummy_service)

    assert mutation_response.status_code == 200
    assert mutation_response.json().get("data") is None


def test_move_nonexistent(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_move_by_name(authorized_client, "bogus_service", "sda1")
    data = get_data(mutation_response)["services"]["moveService"]
    assert_notfound(data)

    assert data["service"] is None
    assert data["job"] is None


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


def test_move_immovable(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    dummy_service.set_movable(False)
    mutation_response = api_move(authorized_client, dummy_service, "sda1")
    data = get_data(mutation_response)["services"]["moveService"]
    assert_errorcode(data, 400)

    # is there a meaning in returning the service in this?
    assert data["service"] is not None
    assert data["job"] is None


def test_move_no_such_volume(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_move(authorized_client, dummy_service, "bogus_volume")
    data = get_data(mutation_response)["services"]["moveService"]
    assert_notfound(data)

    # is there a meaning in returning the service in this?
    assert data["service"] is not None
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
    assert data["job"] is not None


def test_mailservice_cannot_enable_disable(authorized_client):
    mailservice = get_service_by_id("email")

    mutation_response = api_enable(authorized_client, mailservice)
    data = get_data(mutation_response)["services"]["enableService"]
    assert_errorcode(data, 400)
    # TODO?: we cannot convert mailservice to graphql Service without /var/domain yet
    # assert data["service"] is not None

    mutation_response = api_disable(authorized_client, mailservice)
    data = get_data(mutation_response)["services"]["disableService"]
    assert_errorcode(data, 400)
    # assert data["service"] is not None


def enabling_disabling_reads_json(dummy_service: DummyService):
    with WriteUserData() as data:
        data[dummy_service.get_id()]["enabled"] = False
    assert dummy_service.is_enabled() is False
    with WriteUserData() as data:
        data[dummy_service.get_id()]["enabled"] = True
    assert dummy_service.is_enabled() is True
