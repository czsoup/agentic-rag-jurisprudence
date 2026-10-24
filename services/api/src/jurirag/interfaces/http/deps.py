"""Dépendances injectées dans les routes (remplaçables dans les tests)."""

from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request

from jurirag.bootstrap import IndexBundle
from jurirag.interfaces.http.container import Container


def get_container(request: Request) -> Container:
    return cast(Container, request.app.state.container)


ContainerDep = Annotated[Container, Depends(get_container)]


def require_index(container: Container) -> IndexBundle:
    if container.index is None:
        raise HTTPException(503, container.index_error or "Index indisponible")
    return container.index
