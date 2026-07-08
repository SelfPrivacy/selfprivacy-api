from selfprivacy_api.jobs import Jobs
from selfprivacy_api.utils.localization import TranslateSystemMessage as t
from tests.common import generate_jobs_query
from tests.test_graphql.common import get_data
from tests.test_jobs import jobs  # noqa: F401  fixture

API_JOBS_QUERY = """
getJobs {
    uid
    name
    description
}
"""


def test_translate_ru_returns_msgstr_not_msgid():
    translated = t.translate(text="Rebuild system", locale="ru")
    assert translated == "Пересборка системы"


def test_graphql_jobs_query_honors_accept_language_ru(
    authorized_client,
    jobs,  # noqa: F811
):
    Jobs.add(
        name="Rebuild system",
        type_id="test.rebuild",
        description=(
            "Applying the new system configuration by "
            "building the new NixOS generation."
        ),
    )

    response = authorized_client.post(
        "/graphql",
        json={"query": generate_jobs_query([API_JOBS_QUERY])},
        headers={"Accept-Language": "ru"},
    )
    data = get_data(response)
    result = data["jobs"]["getJobs"]

    assert len(result) == 1
    assert result[0]["name"] == "Пересборка системы"
    assert result[0]["description"] == (
        "Применение новой конфигурации системы путём сборки новой генерации NixOS."
    )
