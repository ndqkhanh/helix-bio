"""Ontology grounding: map entity mentions to canonical IDs (UniProt / HGNC / MeSH / ...).

For the MVP this is a rule-based lookup with a small curated seed set; production
swaps in a real ontology service (HGNC REST, UniProt mapping API, MeSH SPARQL).
"""
from __future__ import annotations

import re
from typing import Optional

from .models import OntologyID

_SEED_ENTITIES: dict[str, list[OntologyID]] = {
    # Symbol / common name → one or more canonical IDs
    "kras": [
        OntologyID(namespace="UniProt", value="P01116"),
        OntologyID(namespace="HGNC", value="6407"),
        OntologyID(namespace="Ensembl", value="ENSG00000133703"),
    ],
    "kras-g12d": [
        OntologyID(namespace="UniProt", value="P01116"),
        OntologyID(namespace="HGNC", value="6407"),
    ],
    "tp53": [
        OntologyID(namespace="UniProt", value="P04637"),
        OntologyID(namespace="HGNC", value="11998"),
        OntologyID(namespace="Ensembl", value="ENSG00000141510"),
    ],
    "p53": [
        OntologyID(namespace="UniProt", value="P04637"),
        OntologyID(namespace="HGNC", value="11998"),
    ],
    "egfr": [
        OntologyID(namespace="UniProt", value="P00533"),
        OntologyID(namespace="HGNC", value="3236"),
    ],
    "pancreatic cancer": [
        OntologyID(namespace="MeSH", value="D010190"),
    ],
    "imatinib": [
        OntologyID(namespace="ChEMBL", value="CHEMBL941"),
    ],
    "metformin": [
        OntologyID(namespace="ChEMBL", value="CHEMBL1431"),
    ],
}


_CANONICAL_PATTERNS = {
    "UniProt": re.compile(r"\bUniProt[:_]([A-Z][0-9][A-Z0-9]{3}[0-9](?:[A-Z0-9]{4})?)\b", re.IGNORECASE),
    "HGNC":    re.compile(r"\bHGNC[:_](\d+)\b", re.IGNORECASE),
    "MeSH":    re.compile(r"\bMeSH[:_](D\d+)\b", re.IGNORECASE),
    "ChEMBL":  re.compile(r"\bChEMBL[:_](CHEMBL\d+)\b", re.IGNORECASE),
    "Ensembl": re.compile(r"\bEnsembl[:_](ENS[A-Z]+\d+)\b", re.IGNORECASE),
    "PDB":     re.compile(r"\bPDB[:_]([0-9][A-Z0-9]{3})\b", re.IGNORECASE),
}


class OntologyGrounder:
    """Resolves entity mentions to canonical ontology IDs.

    - ``ground(text)``: scan text, return list of resolved IDs.
    - ``resolve(name)``: resolve a single symbol / name.
    - ``parse_canonical(text)``: pull out already-canonical mentions (UniProt:P01116).
    """

    def __init__(self, seed: Optional[dict[str, list[OntologyID]]] = None) -> None:
        self._seed = dict(seed or _SEED_ENTITIES)

    def resolve(self, name: str) -> list[OntologyID]:
        key = name.strip().lower()
        return list(self._seed.get(key, []))

    def parse_canonical(self, text: str) -> list[OntologyID]:
        """Extract already-canonical IDs (e.g., 'UniProt:P01116') from free text."""
        out: list[OntologyID] = []
        for ns, rx in _CANONICAL_PATTERNS.items():
            for m in rx.finditer(text):
                out.append(OntologyID(namespace=ns, value=m.group(1)))
        return _dedup(out)

    def ground(self, text: str) -> list[OntologyID]:
        """Combine canonical-ID parsing with symbol lookup from the seed set."""
        ids: list[OntologyID] = self.parse_canonical(text)
        # Single-word tokens (letters/digits/hyphens only — punctuation stripped)
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9\-]+", text)
        for tok in tokens:
            ids.extend(self.resolve(tok))
        # Bigrams over the normalized tokens (not raw whitespace split) so
        # trailing punctuation doesn't break multi-word seed matches.
        lowered = [t.lower() for t in tokens]
        for i in range(len(lowered) - 1):
            bigram = f"{lowered[i]} {lowered[i+1]}"
            ids.extend(self.resolve(bigram))
        return _dedup(ids)

    def register(self, name: str, ids: list[OntologyID]) -> None:
        self._seed[name.strip().lower()] = list(ids)


def _dedup(ids: list[OntologyID]) -> list[OntologyID]:
    seen: set[str] = set()
    out: list[OntologyID] = []
    for i in ids:
        key = i.canonical()
        if key in seen:
            continue
        seen.add(key)
        out.append(i)
    return out
