import json
import pytest

def read_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

###############################################################################

@pytest.fixture
def ocserv_off(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "turned_off.json")
    assert read_json(datadir / "turned_off.json")["ocserv"]["enable"] == False
    return datadir

@pytest.fixture
def ocserv_on(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "turned_on.json")
    assert read_json(datadir / "turned_on.json")["ocserv"]["enable"] == True
    return datadir

@pytest.fixture
def ocserv_enable_undefined(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "enable_undefined.json")
    assert "enable" not in read_json(datadir / "enable_undefined.json")["ocserv"]
    return datadir

@pytest.fixture
def ocserv_undefined(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "undefined.json")
    assert "ocserv" not in read_json(datadir / "undefined.json")
    return datadir

###############################################################################

@pytest.mark.parametrize("endpoint", ["enable", "disable"])
def test_unauthorized(client, ocserv_off, endpoint):
    response = client.post(f"/services/ocserv/{endpoint}")
    assert response.status_code == 401

@pytest.mark.parametrize("endpoint", ["enable", "disable"])
def test_illegal_methods(authorized_client, ocserv_off, endpoint):
    response = authorized_client.get(f"/services/ocserv/{endpoint}")
    assert response.status_code == 405
    response = authorized_client.put(f"/services/ocserv/{endpoint}")
    assert response.status_code == 405
    response = authorized_client.delete(f"/services/ocserv/{endpoint}")
    assert response.status_code == 405

@pytest.mark.parametrize("endpoint,target_file", [("enable", "turned_on.json"), ("disable", "turned_off.json")])
def test_switch_from_off(authorized_client, ocserv_off, endpoint, target_file):
    response = authorized_client.post(f"/services/ocserv/{endpoint}")
    assert response.status_code == 200
    assert read_json(ocserv_off / "turned_off.json") == read_json(ocserv_off / target_file)

@pytest.mark.parametrize("endpoint,target_file", [("enable", "turned_on.json"), ("disable", "turned_off.json")])
def test_switch_from_on(authorized_client, ocserv_on, endpoint, target_file):
    response = authorized_client.post(f"/services/ocserv/{endpoint}")
    assert response.status_code == 200
    assert read_json(ocserv_on / "turned_on.json") == read_json(ocserv_on / target_file)

@pytest.mark.parametrize("endpoint,target_file", [("enable", "turned_on.json"), ("disable", "turned_off.json")])
def test_switch_twice(authorized_client, ocserv_off, endpoint, target_file):
    response = authorized_client.post(f"/services/ocserv/{endpoint}")
    assert response.status_code == 200
    response = authorized_client.post(f"/services/ocserv/{endpoint}")
    assert response.status_code == 200
    assert read_json(ocserv_off / "turned_off.json") == read_json(ocserv_off / target_file)

@pytest.mark.parametrize("endpoint,target_file", [("enable", "turned_on.json"), ("disable", "turned_off.json")])
def test_on_attribute_deleted(authorized_client, ocserv_enable_undefined, endpoint, target_file):
    response = authorized_client.post(f"/services/ocserv/{endpoint}")
    assert response.status_code == 200
    assert read_json(ocserv_enable_undefined / "enable_undefined.json") == read_json(ocserv_enable_undefined / target_file)

@pytest.mark.parametrize("endpoint,target_file", [("enable", "turned_on.json"), ("disable", "turned_off.json")])
def test_on_ocserv_undefined(authorized_client, ocserv_undefined, endpoint, target_file):
    response = authorized_client.post(f"/services/ocserv/{endpoint}")
    assert response.status_code == 200
    assert read_json(ocserv_undefined / "undefined.json") == read_json(ocserv_undefined / target_file)
