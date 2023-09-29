import pytest

from selfprivacy_api.graphql.mutations.services_mutations import ServicesMutations
import selfprivacy_api.services as service_module
from selfprivacy_api.services.service import Service, ServiceStatus

import tests.test_graphql.test_api_backup
from tests.test_common import raw_dummy_service, dummy_service
from tests.common import generate_service_query
from tests.test_graphql.common import assert_ok, get_data


@pytest.fixture()
def only_dummy_service(dummy_service):
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
    response = authorized_client.post(
        "/graphql",
        json={"query": generate_service_query([API_SERVICES_QUERY])},
    )
    data = get_data(response)
    result = data["services"]["allServices"]
    assert result is not None
    return result


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


def test_stop_return_value(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_stop(authorized_client, dummy_service)
    data = get_data(mutation_response)["services"]["stopService"]
    assert_ok(data)
    service = data["service"]
    assert service["id"] == dummy_service.get_id()
    assert service["status"] == ServiceStatus.INACTIVE.value


def test_start_nonexistent(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_start_by_name(authorized_client, "bogus_service")
    data = get_data(mutation_response)["services"]["startService"]
    assert_notfound(data)

    assert data["service"] is None


def test_stop_nonexistent(authorized_client, only_dummy_service):
    dummy_service = only_dummy_service
    mutation_response = api_stop_by_name(authorized_client, "bogus_service")
    data = get_data(mutation_response)["services"]["stopService"]
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
