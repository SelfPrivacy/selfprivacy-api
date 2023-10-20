import json
import pytest


def read_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


###############################################################################


@pytest.fixture
def bitwarden_off(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "turned_off.json")
    assert read_json(datadir / "turned_off.json")["bitwarden"]["enable"] == False
    return datadir


@pytest.fixture
def bitwarden_on(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "turned_on.json")
    assert read_json(datadir / "turned_on.json")["bitwarden"]["enable"] == True
    return datadir


@pytest.fixture
def bitwarden_enable_undefined(mocker, datadir):
    mocker.patch(
        "selfprivacy_api.utils.USERDATA_FILE", new=datadir / "enable_undefined.json"
    )
    assert "enable" not in read_json(datadir / "enable_undefined.json")["bitwarden"]
    return datadir


@pytest.fixture
def bitwarden_undefined(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "undefined.json")
    assert "bitwarden" not in read_json(datadir / "undefined.json")
    return datadir


###############################################################################


@pytest.mark.parametrize(
    "endpoint,target_file",
    [("enable", "turned_on.json"), ("disable", "turned_off.json")],
)
def test_on_attribute_deleted(
    authorized_client, bitwarden_enable_undefined, endpoint, target_file
):
    response = authorized_client.post(f"/services/bitwarden/{endpoint}")
    assert response.status_code == 200
    assert read_json(bitwarden_enable_undefined / "enable_undefined.json") == read_json(
        bitwarden_enable_undefined / target_file
    )


@pytest.mark.parametrize(
    "endpoint,target_file",
    [("enable", "turned_on.json"), ("disable", "turned_off.json")],
)
def test_on_bitwarden_undefined(
    authorized_client, bitwarden_undefined, endpoint, target_file
):
    response = authorized_client.post(f"/services/bitwarden/{endpoint}")
    assert response.status_code == 200
    assert read_json(bitwarden_undefined / "undefined.json") == read_json(
        bitwarden_undefined / target_file
    )
