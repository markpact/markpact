"""Publish data models — PublishConfig and PublishResult."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PublishConfig:
    """Configuration for publishing"""
    registry: str  # pypi, npm, docker, github
    name: str
    version: str
    description: str = ""
    author: str = ""
    license: str = "MIT"
    repository: str = ""
    keywords: list[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass
class PublishResult:
    """Result of a publish operation"""
    success: bool
    registry: str
    message: str
    version: str = ""
    url: str = ""
