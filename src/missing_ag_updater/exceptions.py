"""Custom exceptions raised by missing-ag-updater."""

from typing import Sequence


class ReleaseEndpointError(RuntimeError):
    """Raised when every configured release metadata endpoint fails.

    Carries the attempted URLs and their errors so the CLI can show a clear,
    actionable message instead of a bare HTTP traceback.
    """

    def __init__(self, component: str, attempts: Sequence[tuple[str, str]]) -> None:
        self.component = component
        self.attempts = list(attempts)
        details = "\n".join(f"  - {url}: {error}" for url, error in self.attempts) or "  - no endpoints configured"
        super().__init__(
            f"Could not fetch {component.upper()} release metadata from any endpoint.\n"
            f"{details}\n"
            "  These endpoints are unofficial and reverse-engineered, so they may have moved.\n"
            f"  Override them with ANTIGRAVITY_{component.upper()}_RELEASES_URL "
            "(or the matching AG_* alias); comma-separate multiple URLs for fallbacks."
        )
