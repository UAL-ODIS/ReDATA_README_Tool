from typing import Union, Optional
import requests

from fastapi import APIRouter, HTTPException

router = APIRouter()

api_key: Optional[str] = None
stage_api_key: Optional[str] = None


def figshare_metadata_readme(figshare_dict: dict) -> dict:
    """
    Function to provide shortened dict for README metadata

    :param figshare_dict: Figshare API response

    :return: README metadata based on Figshare response
    """

    readme_dict = {}

    if 'item' in figshare_dict:
        print("figshare_metadata_readme: Using curation responses")
        readme_dict['article_id'] = figshare_dict['item']['id']
        readme_dict['curation_id'] = figshare_dict['id']
        figshare_dict = figshare_dict['item']
    else:
        readme_dict['article_id'] = figshare_dict['id']

    single_str_citation = figshare_dict['citation']

    # Handle period in author list.  Assume no period in dataset title
    author_list = ([single_str_citation.split('):')[0] + ').'])
    author_list += [str_row + '.' for str_row in
                    single_str_citation.split('): ')[1].split('. ')]

    readme_dict.update({
        'title': figshare_dict['title'],
        'description': figshare_dict['description'],
        'doi': f"https://doi.org/{figshare_dict['doi']}",
        'preferred_citation': author_list,
        'license': figshare_dict['license'],
        'summary': figshare_dict['description'],
        'references': figshare_dict['references'],
    })
    return readme_dict


@router.get('/figshare/{article_id}/')
def get_figshare(article_id: int, curation_id: Optional[int] = None,
                 stage: bool = False,
                 allow_approved: bool = False) -> Union[dict, HTTPException]:
    """
    API call to retrieve Figshare metadata

    \f
    :param article_id: Figshare article ID
    :param curation_id: Figshare curation ID
    :param stage: Figshare stage or production API.
                  Stage is available for Figshare institutions
    :param allow_approved: Return 200 responses even if curation is not pending
    :return: Figshare API response
    """

    if not stage:
        base_url = "https://api.figshare.com"
    else:
        base_url = "https://api.figsh.com"

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'token {api_key if not stage else stage_api_key}'
    }

    curation_url = f"{base_url}/v2/account/institution/review"

    if curation_id is None:
        url = f"{base_url}/v2/account/institution/reviews"
        params = {
            'offset': 0,
            'limit': 1000,
            'article_id': article_id
        }

        if not allow_approved:
            params['status'] = 'pending'

        curation_response = requests.get(url, headers=headers, params=params)
        if curation_response.status_code != 200:
            raise HTTPException(
                status_code=curation_response.status_code,
                detail=curation_response.json(),
            )
        else:
            curation_json = curation_response.json()
            if len(curation_json) != 0:
                print(f"Retrieved pending curation_id for {article_id}: "
                      f"{curation_json[0]['id']}")
                curation_id = curation_json[0]['id']
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f'No valid {"pending" if allow_approved else ""} review for {article_id}'
                )

    if curation_id is not None:
        url = f"{curation_url}/{curation_id}"

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json(),
            )
        else:
            r_json = response.json()
            if not allow_approved:
                if r_json['status'] == 'pending':
                    return r_json
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f'No valid pending review for {article_id}'
                    )
            else:
                return r_json


@router.get('/metadata/{article_id}/')
async def get_readme_metadata(article_id: int,
                              curation_id: Optional[int] = None,
                              stage: bool = False,
                              allow_approved: bool = False) -> dict:
    """
    API call for README metadata based on Figshare response

    \f
    :param article_id: Figshare article ID
    :param curation_id: Figshare curation ID
    :param stage: Figshare stage or production API.
                  Stage is available for Figshare institutions
    :param allow_approved: Return 200 responses even if curation is not pending

    :return: README metadata API response
    """

    try:
        figshare_dict = get_figshare(article_id, curation_id=curation_id,
                                     stage=stage,
                                     allow_approved=allow_approved)
        readme_dict = figshare_metadata_readme(figshare_dict)
        return readme_dict
    except HTTPException as e:
        raise e
