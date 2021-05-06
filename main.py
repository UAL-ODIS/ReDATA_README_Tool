#!/usr/bin/env python
import json
from os import getenv
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from readme_tool import figshare, intake_form

app = FastAPI()


def configure():
    app.mount("/templates", StaticFiles(directory="templates"), name="templates")
    configure_routing()
    configure_api()


def configure_routing():
    app.include_router(figshare.router)
    app.include_router(intake_form.router)


def configure_api():
    figshare_api_key = getenv('FIGSHARE_API_KEY')
    figshare_stage_api_key = getenv('FIGSHARE_STAGE_API_KEY')

    if not figshare_api_key or not figshare_stage_api_key:
        settings_file = 'settings.json'
        file = Path(settings_file).absolute()
        if not file.exists():
            err_msg = "file not found; please see settings_template.json"
            print(f"WARNING: {file} {err_msg}")
            raise Exception(f"{settings_file} {err_msg}")

        with open(file) as fin:
            settings = json.load(fin)

    if not figshare_api_key:
        print("WARNING: FIGSHARE_API_KEY not set as ENV variable. "
              "Obtaining from settings.json")

        figshare_api_key = settings.get('figshare_api_key')
    else:
        print("FIGSHARE_API_KEY set as ENV variable.")

    if not figshare_stage_api_key:
        print("WARNING: FIGSHARE_STAGE_API_KEY not set as ENV variable. "
              "Obtaining from settings.json")

        figshare_stage_api_key = settings.get('figshare_stage_api_key')
    else:
        print("FIGSHARE_API_KEY set as ENV variable")

    figshare.api_key = figshare_api_key
    figshare.stage_api_key = figshare_stage_api_key


if __name__ == "__main__":
    configure()
    uvicorn.run('main:app', port=8000, reload=True)
else:
    configure()
