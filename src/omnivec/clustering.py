"""Convert reciprocal nearest-neighbor hits into connected clusters."""

from __future__ import annotations

from collections import defaultdict, deque

from omnivec.schemas import AssetKind, SearchHit, SimilarityCluster, SimilarityEdge


def build_reciprocal_clusters(
    kind: AssetKind,
    search_results: dict[str, list[SearchHit]],
) -> list[SimilarityCluster]:
    top_hits: dict[str, dict[str, float]] = {}
    for source, hits in search_results.items():
        top_hits[source] = {hit.path: hit.distance for hit in hits if hit.path != source}

    adjacency: dict[str, set[str]] = defaultdict(set)
    edges: list[SimilarityEdge] = []
    seen_pairs: set[tuple[str, str]] = set()

    for source, neighbors in top_hits.items():
        for target, distance in neighbors.items():
            reverse = top_hits.get(target, {})
            if source not in reverse:
                continue

            pair: tuple[str, str]
            if source <= target:
                pair = (source, target)
            else:
                pair = (target, source)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            adjacency[source].add(target)
            adjacency[target].add(source)
            edges.append(
                SimilarityEdge(
                    source=pair[0],
                    target=pair[1],
                    distance=min(distance, reverse[source]),
                )
            )

    components: list[list[str]] = []
    visited: set[str] = set()
    for node in sorted(adjacency):
        if node in visited:
            continue

        queue = deque([node])
        component: list[str] = []
        visited.add(node)
        while queue:
            current = queue.popleft()
            component.append(current)
            for neighbor in sorted(adjacency[current]):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                queue.append(neighbor)

        if len(component) > 1:
            components.append(sorted(component))

    clusters: list[SimilarityCluster] = []
    for index, members in enumerate(components, start=1):
        member_set = set(members)
        cluster_edges = [
            edge for edge in edges if edge.source in member_set and edge.target in member_set
        ]
        cluster_edges.sort(key=lambda edge: (edge.distance, edge.source, edge.target))
        clusters.append(
            SimilarityCluster(
                cluster_id=f"{kind}-{index}",
                kind=kind,
                members=members,
                edges=cluster_edges,
            )
        )

    return clusters
