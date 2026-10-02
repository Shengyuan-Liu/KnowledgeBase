"""Expose assembled application resources to HTTP routes."""

from typing import Annotated

from fastapi import Depends, Request

from knowledgebase.bootstrap import AppResources


def get_resources(request: Request) -> AppResources:
    return request.app.state.resources


Resources = Annotated[AppResources, Depends(get_resources)]
