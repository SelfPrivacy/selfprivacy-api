def assert_ok(response, request):
    data = assert_data(response)
    data[request]["success"] is True
    data[request]["message"] is not None
    data[request]["code"] == 200


def assert_errorcode(response, request, code):
    data = assert_data(response)
    data[request]["success"] is False
    data[request]["message"] is not None
    data[request]["code"] == code


def assert_empty(response):
    assert response.status_code == 200
    assert response.json().get("data") is None


def assert_data(response):
    assert response.status_code == 200
    data = response.json().get("data")
    assert data is not None
    return data
