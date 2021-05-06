from typing import Union
from fastapi.testclient import TestClient
from fastapi import FastAPI

from readme_tool import figshare

app = FastAPI()
app.include_router(figshare.router)
client = TestClient(app)

# Production test (published)
article_id = 12966581
curation_id = 540005

# Stage test (published)
stage_article_id = 6941778
stage_curation_id = 453842

# Stage test (under review)
stage_article_underreview_id = 7048856
stage_curation_underreview_id = 492094

value_400 = [-1, 0]


def test_figshare_get(figshare_api_key, figshare_stage_api_key):
    def _client_get(article_id0: Union[int, str] = '',
                    curation_id0: Union[int] = None,
                    stage: bool = False,
                    allow_approved: bool = True):
        # allow_approved set to ensure that it works with published data
        params = {
            'curation_id': curation_id0,
            'stage': stage,
            'allow_approved': allow_approved
        }
        return client.get(f'/figshare/{article_id0}', params=params)

    figshare.api_key = figshare_api_key
    figshare.stage_api_key = figshare_stage_api_key

    # Production
    ############
    response = _client_get(article_id, curation_id0=curation_id)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert response.json()['article_id'] == article_id
    assert response.json()['id'] == curation_id

    # Check when curation_id is not specified
    response = _client_get(article_id)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

    # This is published, so no pending expected
    for approved, s_code in zip([False, True], [404, 200]):
        response = _client_get(article_id, allow_approved=approved)
        assert response.status_code == s_code  # This is from FastAPI
        assert isinstance(response.json(), dict)

    # Check for incorrect entries with prod endpoint
    response = _client_get(stage_article_id)
    assert response.status_code == 404  # This is from figshare

    for i in value_400:
        response = _client_get(i, curation_id0=i)
        assert response.status_code == 400  # This is from figshare

        response = _client_get(i)
        # Figshare API gives wrong responses, 404 is returned when 200 with empty json
        assert response.status_code == (400 if i == -1 else 404)  # figshare=400, FastAPI=404

    response = _client_get()
    assert response.status_code == 404  # This is from FastAPI

    # Stage
    #######
    response = _client_get(stage_article_id, curation_id0=stage_curation_id,
                           stage=True)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert response.json()['article_id'] == stage_article_id
    assert response.json()['id'] == stage_curation_id

    # Check for pending deposit on stage
    response = _client_get(stage_article_underreview_id,
                           curation_id0=stage_curation_underreview_id,
                           stage=True, allow_approved=False)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert response.json()['article_id'] == stage_article_underreview_id
    assert response.json()['id'] == stage_curation_underreview_id

    # Check for incorrect entries with stage endpoint
    response = _client_get(article_id, curation_id0=curation_id, stage=True)
    assert response.status_code == 404  # This is from figshare

    for i in value_400:
        response = _client_get(i, curation_id0=i, stage=True)
        assert response.status_code == 400  # This is from figshare

        response = _client_get(i)
        # Figshare API gives wrong responses, 404 is returned when 200 with empty json
        assert response.status_code == (400 if i == -1 else 404)  # figshare=400, FastAPI=404

    response = _client_get(stage=True)
    assert response.status_code == 404  # This is from FastAPI


def test_metadata_get(figshare_api_key, figshare_stage_api_key):
    def _client_get(article_id0: Union[int, str] = '',
                    curation_id0: Union[int, str] = None,
                    stage: bool = False,
                    allow_approved: bool = True):
        params = {
            'curation_id': curation_id0,
            'stage': stage,
            'allow_approved': allow_approved
        }
        return client.get(f'/metadata/{article_id0}', params=params)

    figshare.api_key = figshare_api_key
    figshare.stage_api_key = figshare_stage_api_key

    # Production
    ############
    response = _client_get(article_id, curation_id0=curation_id)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert response.json()['article_id'] == article_id

    # Check for incorrect entries with prod endpoint
    response = _client_get(stage_article_id)
    assert response.status_code == 404

    for i in value_400:
        response = _client_get(i, curation_id0=i)
        assert response.status_code == 400

    response = _client_get()
    assert response.status_code == 404

    # Stage
    #######
    response = _client_get(stage_article_id, curation_id0=stage_curation_id,
                           stage=True)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert response.json()['article_id'] == stage_article_id

    # Check for incorrect entries with stage endpoint
    response = _client_get(article_id, curation_id0=curation_id,
                           stage=True)
    assert response.status_code == 404

    for i in value_400:
        response = _client_get(i, curation_id0=i, stage=True)
        assert response.status_code == 400

    response = _client_get(stage=True)
    assert response.status_code == 404
