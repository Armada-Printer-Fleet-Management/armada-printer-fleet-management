from dataclasses import dataclass


@dataclass(frozen=True)
class PageSizes:
    """One list endpoint's page sizes: what a caller gets when they ask for none, and the most
    they may ask for. Each domain declares its own."""

    default: int
    maximum: int

    def size(self, requested: int) -> int:
        return min(requested, self.maximum) if requested > 0 else self.default
