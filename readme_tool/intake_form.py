from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel
from typing import Union, Optional

from tinydb import TinyDB, Query

from . import __version__ as rem_version
from . import figshare

api_version = "v1.0.0"
tinydb_file = 'intake.json'

router = APIRouter()
templates = Jinja2Templates(directory='templates/')

q = Query()  # For TinyDB query


class IntakeData(BaseModel):
    article_id: int
    curation_id: int = None
    citation: str = ''
    summary: str = ''
    files: str = ''
    materials: str = ''
    contributors: str = ''
    notes: str = ''


class VersionModel(BaseModel):
    rem_api_version: str = rem_version
    rem_web_api_version: str = api_version


@router.get('/version/')
async def get_version() -> VersionModel:
    """Retrieve version metadata"""
    return VersionModel()


@router.get('/database/')
async def get_db(db_file: str = tinydb_file) -> TinyDB:
    """Retrieve TinyDB README database

    \f
    :param db_file: JSON filename for TinyDB database

    :return: README database
    """
    db = TinyDB(db_file)
    return db


@router.get('/database/read/{article_id}')
async def get_data(article_id: int, index: bool = False,
                   db_file: str = tinydb_file) -> Union[dict, int]:
    """Retrieve record from TinyDB README database

    \f
    :param article_id: Figshare article ID
    :param index: Indicate whether to return ``doc_id`` (True) or record (False).
    :param db_file: JSON filename for TinyDB database

    :return: TinyDB record or ``doc_id``
    """
    db0 = await get_db(db_file=db_file)
    article_query = q['article_id'] == article_id
    match = db0.search(article_query)
    if len(match) == 0:
        raise HTTPException(
            status_code=404,
            detail="Record not found",
        )

    if not index:
        return match[0]
    else:
        return db0.get(article_query).doc_id


@router.post('/database/create')
async def add_data(response: IntakeData, db_file: str = tinydb_file):
    """
    Add record to TinyDB README database

    \f
    :param response: Record to include
    :param db_file: JSON filename for TinyDB database
    """
    db0 = await get_db(db_file)
    db0.insert(response.dict())


@router.post('/database/update/{doc_id}')
async def update_data(doc_id: int, response: IntakeData,
                      db_file: str = tinydb_file):
    """
    Update record in TinyDB README database

    \f
    :param doc_id: ``doc_id`` identifier from ``get_data`` to update
    :param response: Record to use for update
    :param db_file: JSON filename for TinyDB database

    :return: README database
    """
    db0 = await get_db(db_file)
    db0.update(response.dict(), doc_ids=[doc_id])
    return db0


@router.get('/form/{article_id}/')
async def get_form(article_id: int, request: Request,
                   curation_id: Optional[int] = None,
                   stage: bool = False,
                   allow_approved: bool = False,
                   db_file: str = tinydb_file) \
        -> templates.TemplateResponse:
    """
    Return README form with Figshare metadata and README metadata if available

    \f
    :param article_id: Figshare ``article_id``
    :param curation_id: Figshare ``curation_id``
    :param request: HTTP request for template
    :param stage: Figshare stage or production API.
                  Stage is only available for Figshare institutions
    :param allow_approved: Return 200 responses even if curation is not pending
    :param db_file: JSON filename for TinyDB database

    :return: HTML content through ``jinja2`` template
    """
    try:
        fs_metadata = await \
            figshare.get_readme_metadata(article_id, curation_id=curation_id,
                                         stage=stage,
                                         allow_approved=allow_approved)
    except HTTPException:
        return templates.TemplateResponse('404.html',
                                          context={'request': request})

    try:
        submit_dict = await get_data(article_id, db_file=db_file)
    except HTTPException:
        submit_dict = dict.fromkeys(
            ['citation', 'summary', 'files', 'materials', 'contributors', 'notes'], ''
        )

    return templates.TemplateResponse('intake.html',
                                      context={'request': request,
                                               'submit_dict': submit_dict,
                                               'fs': fs_metadata})


@router.post('/form/{article_id}/')
async def post_form(article_id: int, request: Request,
                    curation_id: Optional[int],
                    citation: Optional[str] = Form(''),
                    summary: Optional[str] = Form(''),
                    files: Optional[str] = Form(''),
                    materials: Optional[str] = Form(''),
                    contributors: Optional[str] = Form(''),
                    notes: Optional[str] = Form(''),
                    stage: bool = False,
                    allow_approved: bool = False,
                    db_file: str = tinydb_file) \
        -> templates.TemplateResponse:
    """
    Submit data to incorporate in TinyDB database

    \f
    :param article_id: Figshare `article_id`
    :param curation_id: Figshare ``curation_id``
    :param request: HTTP request
    :param citation: Form response for preferred citation data
    :param summary: Form response for summary data
    :param files: Form response for files data
    :param materials: Form response for materials and method data
    :param contributors: Form response for contributor roles data
    :param notes: Form response for additional notes data
    :param stage: Figshare stage or production API.
                  Stage is only available for Figshare institutions
    :param allow_approved: Return 200 responses even if curation is not pending
    :param db_file: JSON filename for TinyDB database
    :return: HTML content through ``jinja2`` template
    """

    try:
        fs_metadata = await \
            figshare.get_readme_metadata(article_id, curation_id=curation_id,
                                         stage=stage,
                                         allow_approved=allow_approved)
    except HTTPException:
        return templates.TemplateResponse('404.html',
                                          context={'request': request})

    result = {
        'citation': citation,
        'summary': summary,
        'files': files,
        'materials': materials,
        'contributors': contributors,
        'notes': notes,
    }

    fields = {
        'citation': 'Preferred Citation',
        'summary': 'Summary',
        'files': 'Files and Folders',
        'materials': 'Materials and Methods',
        'contributors': 'Contributor Roles',
        'notes': 'Notes',
    }

    post_data = {
        'article_id': fs_metadata['article_id'],
        'curation_id': fs_metadata['curation_id'],
        **result}

    try:
        doc_id = await get_data(article_id, index=True, db_file=db_file)
        await update_data(doc_id, IntakeData(**post_data), db_file=db_file)
    except HTTPException:
        await add_data(IntakeData(**post_data), db_file=db_file)

    return templates.TemplateResponse('receive.html',
                                      context={'request': request,
                                               'result': result,
                                               'fields': fields,
                                               'fs_metadata': fs_metadata,
                                               }
                                      )
