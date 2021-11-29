import json
import pytest

def read_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

###############################################################################

@pytest.fixture
def gitea_off(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "turned_off.json")
    assert read_json(datadir / "turned_off.json")["gitea"]["enable"] == False
    return datadir

@pytest.fixture
def gitea_on(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "turned_on.json")
    assert read_json(datadir / "turned_on.json")["gitea"]["enable"] == True
    return datadir

@pytest.fixture
def gitea_enable_undefined(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "enable_undefined.json")
    assert "enable" not in read_json(datadir / "enable_undefined.json")["gitea"]
    return datadir

@pytest.fixture
def gitea_undefined(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "undefined.json")
    assert "gitea" not in read_json(datadir / "undefined.json")
    return datadir

###############################################################################

@pytest.mark.parametrize("endpoint", ["enable", "disable"])
def test_unauthorized(client, gitea_off, endpoint):
    response = client.post(f"/services/gitea/{endpoint}")
    assert response.status_code == 401

@pytest.mark.parametrize("endpoint", ["enable", "disable"])
def test_illegal_methods(authorized_client, gitea_off, endpoint):
    response = authorized_client.get(f"/services/gitea/{endpoint}")
    assert response.status_code == 405
    response = authorized_client.put(f"/services/gitea/{endpoint}")
    assert response.status_code == 405
    response = authorized_client.delete(f"/services/gitea/{endpoint}")
    assert response.status_code == 405

@pytest.mark.parametrize("endpoint,target_file", [("enable", "turned_on.json"), ("disable", "turned_off.json")])
def test_switch_from_off(authorized_client, gitea_off, endpoint, target_file):
    response = authorized_client.post(f"/services/gitea/{endpoint}")
    assert response.status_code == 200
    assert read_json(gitea_off / "turned_off.json") == read_json(gitea_off / target_file)

@pytest.mark.parametrize("endpoint,target_file", [("enable", "turned_on.json"), ("disable", "turned_off.json")])
def test_switch_from_on(authorized_client, gitea_on, endpoint, target_file):
    response = authorized_client.post(f"/services/gitea/{endpoint}")
    assert response.status_code == 200
    assert read_json(gitea_on / "turned_on.json") == read_json(gitea_on / target_file)

@pytest.mark.parametrize("endpoint,target_file", [("enable", "turned_on.json"), ("disable", "turned_off.json")])
def test_switch_twice(authorized_client, gitea_off, endpoint, target_file):
    response = authorized_client.post(f"/services/gitea/{endpoint}")
    assert response.status_code == 200
    response = authorized_client.post(f"/services/gitea/{endpoint}")
    assert response.status_code == 200
    assert read_json(gitea_off / "turned_off.json") == read_json(gitea_off / target_file)

@pytest.mark.parametrize("endpoint,target_file", [("enable", "turned_on.json"), ("disable", "turned_off.json")])
def test_on_attribute_deleted(authorized_client, gitea_enable_undefined, endpoint, target_file):
    response = authorized_client.post(f"/services/gitea/{endpoint}")
    assert response.status_code == 200
    assert read_json(gitea_enable_undefined / "enable_undefined.json") == read_json(gitea_enable_undefined / target_file)

@pytest.mark.parametrize("endpoint,target_file", [("enable", "turned_on.json"), ("disable", "turned_off.json")])
def test_on_gitea_undefined(authorized_client, gitea_undefined, endpoint, target_file):
    response = authorized_client.post(f"/services/gitea/{endpoint}")
    assert response.status_code == 200
    assert read_json(gitea_undefined / "undefined.json") == read_json(gitea_undefined / target_file)
