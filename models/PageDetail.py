from dataclasses import dataclass

namespace = "DocsIngestionApp.Models"

@dataclass
class PageDetail:
    Index: int
    Offset: int
    Text: str