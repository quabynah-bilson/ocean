from enum import StrEnum


class ObjectKind(StrEnum):
    PROJECT = "project"
    REPOSITORY = "repository"
    PULL_REQUEST = "pull-request"
    COMPONENT = "component"
