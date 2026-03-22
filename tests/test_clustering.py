from __future__ import annotations

from omnivec.clustering import build_reciprocal_clusters
from omnivec.schemas import SearchHit


def test_build_reciprocal_clusters_uses_connected_components() -> None:
    clusters = build_reciprocal_clusters(
        "document",
        {
            "a.md": [SearchHit(path="b.md", distance=0.1)],
            "b.md": [
                SearchHit(path="a.md", distance=0.1),
                SearchHit(path="c.md", distance=0.2),
            ],
            "c.md": [SearchHit(path="b.md", distance=0.2)],
            "solo.md": [SearchHit(path="a.md", distance=0.9)],
        },
    )

    assert len(clusters) == 1
    assert clusters[0].members == ["a.md", "b.md", "c.md"]
    assert [(edge.source, edge.target) for edge in clusters[0].edges] == [
        ("a.md", "b.md"),
        ("b.md", "c.md"),
    ]
