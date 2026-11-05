"""Validated data contracts for ReelBrief extraction."""

from typing import Literal

from pydantic import BaseModel, Field

Category = Literal[
    "coding",
    "ai_tools",
    "music",
    "career",
    "productivity",
    "finance",
    "fitness",
    "food",
    "travel",
    "education",
    "other",
]
Confidence = Literal["high", "medium", "low"]
YouTubeType = Literal["video", "playlist", "channel"]
ReelStatus = Literal["pending", "quick_ready", "processing", "processed", "partial", "failed"]


class Tool(BaseModel):
    name: str
    what_it_does: str


class GitHubRepo(BaseModel):
    name_or_url: str
    note: str


class Website(BaseModel):
    url_or_name: str
    note: str


class Song(BaseModel):
    title: str
    artist: str
    confidence: Confidence


class YouTubeResource(BaseModel):
    title_or_channel: str
    type: YouTubeType
    note: str


class BookOrCourse(BaseModel):
    title: str
    author_or_platform: str


class Extraction(BaseModel):
    short_summary: str
    detailed_summary: str
    category: Category
    tools: list[Tool] = Field(default_factory=list)
    github_repos: list[GitHubRepo] = Field(default_factory=list)
    websites: list[Website] = Field(default_factory=list)
    songs: list[Song] = Field(default_factory=list)
    youtube_resources: list[YouTubeResource] = Field(default_factory=list)
    books_or_courses: list[BookOrCourse] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list, max_length=6)
    worth_watching: bool
    worth_watching_reason: str


class PipelineResult(BaseModel):
    shortcode: str
    url: str
    status: ReelStatus = "processed"
    caption: str = ""
    uploader: str | None = None
    transcript: str = ""
    ocr_text: str = ""
    language: str | None = None
    extraction: Extraction | None = None
    errors: list[str] = Field(default_factory=list)
