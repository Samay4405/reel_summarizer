"""Typed exception hierarchy for the ReelBrief pipeline."""


class ReelBriefError(Exception):
    """Base exception for all ReelBrief pipeline errors."""


class LoginRequired(ReelBriefError):
    """Raised when Instagram requires login/cookies to view or download a reel."""


class RateLimited(ReelBriefError):
    """Raised when Instagram or an upstream service responds with HTTP 429 or rate limits."""


class PrivateOrDeleted(ReelBriefError):
    """Raised when a reel is private, deleted, or cannot be found (HTTP 404)."""


class MediaUnavailable(ReelBriefError):
    """Raised when the media stream cannot be retrieved or downloaded."""


class FfmpegMissing(ReelBriefError):
    """Raised when ffmpeg is not available on PATH."""
