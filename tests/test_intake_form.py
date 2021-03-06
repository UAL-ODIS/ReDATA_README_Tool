from shutil import copy
import ast
from starlette.staticfiles import StaticFiles

from fastapi.testclient import TestClient
from fastapi import FastAPI

from readme_tool.intake_form import VersionModel, router

app = FastAPI()
app.mount("/templates", StaticFiles(directory="templates"), name="templates")
app.include_router(router)
client = TestClient(app)

article_id = 12966581
doc_id = 1
new_article_id = 87654321
new_article_id2 = 12026436  # This is for addition testing

article_id_404 = 12345678

value_400 = [-1, 0]

test_file = 'tests_data/tinydb.json'
test_dup_file = 'tests_data/tinydb_dup.json'  # This is a copy for editing. Won't save
copy(test_file, test_dup_file)


def test_get_version():
    response = client.get(f'/version/')
    assert response.status_code == 200
    json_content = response.json()
    assert isinstance(json_content, dict)
    for key in VersionModel().dict():
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


def test_read_form():
    # Test for existing data (article_id), non-existing data (new_article_id2)
    for a_id in [article_id, new_article_id2]:
        url = f'/form/{a_id}?db_file={test_dup_file}'
        response = client.get(url)
        assert response.status_code == 200
        content = response.content
        assert isinstance(content, bytes)
        assert isinstance(content.decode(), str)
        assert 'html' in content.decode()

    # 404 check
    url = f'/form/{article_id_404}?db_file={test_dup_file}'
    response = client.get(url)
    content = response.content
    assert '404' in content.decode()


def test_intake_post():
    post_data = {
        'summary': 'Summary data for add (extended)',
        'citation': 'Preferred citation data for add (extended)',
        'files': 'Files data for add (extended)',
        'materials': 'Materials data for add (extended)',
        'contributors': 'Contributor roles for add (extended)',
        'notes': 'Additional notes for add (extended)',
    }

    for a_id in [article_id, new_article_id2]:
        url = f'/form/{a_id}?db_file={test_dup_file}'

        response = client.post(url, data=post_data)  # Use data for Form data
        assert response.status_code == 200
        content = response.content
        assert isinstance(content, bytes)
        assert isinstance(content.decode(), str)
        assert 'html' in content.decode()

    # 404 check
    url = f'/form/{article_id_404}?db_file={test_dup_file}'
    response = client.post(url, data=post_data)
    content = response.content
    assert '404' in content.decode()
