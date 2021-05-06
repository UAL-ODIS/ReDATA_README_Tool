from shutil import copy
import ast
from starlette.staticfiles import StaticFiles

from fastapi.testclient import TestClient
from fastapi import FastAPI

from readme_tool import intake_form
from readme_tool import figshare

app = FastAPI()
app.mount("/templates", StaticFiles(directory="templates"), name="templates")
app.include_router(intake_form.router)
client = TestClient(app)

# Production test (published)
article_id = 12966581
curation_id = 540005

doc_id = 1
new_article_id = 87654321
new_article_id2 = 12026436  # This is for addition testing
new_curation_id2 = 478617

article_id_404 = 12345678
curation_id_404 = 123456

value_400 = [-1, 0]

test_file = 'tests_data/tinydb.json'
test_dup_file = 'tests_data/tinydb_dup.json'  # This is a copy for editing. Won't save
copy(test_file, test_dup_file)


def test_get_version():
    response = client.get(f'/version/')
    assert response.status_code == 200
    json_content = response.json()
    assert isinstance(json_content, dict)
    for key in intake_form.VersionModel().dict():
        assert isinstance(json_content[key], str)


def test_get_db():
    url = f'/database/?db_file={test_dup_file}'
    response = client.get(url)
    assert response.status_code == 200
    assert isinstance(response.content, bytes)


def test_get_data():
    url = f'/database/read'

    # Check for default data
    response = client.get(
        f'{url}/{article_id}?db_file={test_dup_file}'
    )
    assert response.status_code == 200
    content = response.content
    assert isinstance(content, bytes)
    assert isinstance(ast.literal_eval(content.decode('UTF-8')), dict)

    # Check that index is returned
    response = client.get(
        f'{url}/{article_id}?db_file={test_dup_file}&index=True'
    )
    assert response.status_code == 200
    content = response.content
    assert isinstance(content, bytes)
    assert isinstance(ast.literal_eval(content.decode('UTF-8')), int)

    # Check for not available data
    response = client.get(
        f'{url}/{new_article_id}?db_file={test_dup_file}'
    )
    assert response.status_code == 404
    content = ast.literal_eval(response.content.decode())
    assert isinstance(content, dict)
    assert content['detail'] == "Record not found"


def test_add_data():
    url = f'/database/create?db_file={test_dup_file}'
    post_data = {
        'article_id': 87654321,
        'citation': 'Preferred citation data for add',
        'summary': 'Summary data for add',
        'files': 'Files data for add',
        'materials': 'Materials data for add',
        'contributors': 'Contributor roles for add',
        'notes': 'Additional notes for add',
    }

    response = client.post(url, json=post_data)
    assert response.status_code == 200
    # assert isinstance(content, bytes)
    # assert isinstance(ast.literal_eval(content.decode('UTF-8')), dict)


def test_update_data():
    url = f'/database/update/{doc_id}?db_file={test_dup_file}'
    post_data = {
        'article_id': article_id,
        'citation': 'Preferred citation data for add',
        'summary': 'Summary data for add',
        'files': 'Files data for add',
        'materials': 'Materials data for add',
        'contributors': 'Contributor roles for add',
        'notes': 'Additional notes for add',
    }
    response = client.post(url, json=post_data)
    assert response.status_code == 200


def test_read_form(figshare_api_key, figshare_stage_api_key):
    # Test for existing data (article_id), non-existing data (new_article_id2)

    figshare.api_key = figshare_api_key
    figshare.stage_api_key = figshare_stage_api_key

    a_list = [article_id, new_article_id2]
    c_list = [curation_id, new_curation_id2]

    for a_id, c_id in zip(a_list, c_list):
        params = {
            'curation_id': c_id,
            'allow_approved': True,
            'db_file': test_dup_file
        }
        url = f'/form/{a_id}/'
        response = client.get(url, params=params)
        assert response.status_code == 200
        content = response.content
        assert isinstance(content, bytes)
        assert isinstance(content.decode(), str)
        assert 'html' in content.decode()

    # 404 check
    params = {
        'curation_id': curation_id_404,
        'allow_approved': True,
        'db_file': test_dup_file
    }
    url = f'/form/{article_id_404}/'
    response = client.get(url, params=params)
    content = response.content
    assert '404' in content.decode()  # From FastAPI


def test_intake_post(figshare_api_key, figshare_stage_api_key):

    figshare.api_key = figshare_api_key
    figshare.stage_api_key = figshare_stage_api_key

    a_list = [article_id, new_article_id2]
    c_list = [curation_id, new_curation_id2]

    post_data = {
        'summary': 'Summary data for add (extended)',
        'citation': 'Preferred citation data for add (extended)',
        'files': 'Files data for add (extended)',
        'materials': 'Materials data for add (extended)',
        'contributors': 'Contributor roles for add (extended)',
        'notes': 'Additional notes for add (extended)',
    }

    for a_id, c_id in zip(a_list, c_list):
        params = {
            'curation_id': c_id,
            'allow_approved': True,
            'db_file': test_dup_file
        }
        url = f'/form/{a_id}/'

        response = client.post(url, data=post_data, params=params)  # Use data for Form data
        assert response.status_code == 200
        content = response.content
        assert isinstance(content, bytes)
        assert isinstance(content.decode(), str)
        assert 'html' in content.decode()

    # 404 check
    params = {
        'curation_id': curation_id_404,
        'allow_approved': True,
        'db_file': test_dup_file
    }
    url = f'/form/{article_id_404}/'
    response = client.post(url, data=post_data, params=params)
    content = response.content
    assert '404' in content.decode()  # From FastAPI
