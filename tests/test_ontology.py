from helix_bio.ontology import OntologyGrounder


def test_resolve_known_symbol():
    g = OntologyGrounder()
    ids = g.resolve("KRAS")
    canonicals = {i.canonical() for i in ids}
    assert "UniProt:P01116" in canonicals
    assert "HGNC:6407" in canonicals


def test_resolve_case_insensitive():
    g = OntologyGrounder()
    assert g.resolve("kras") == g.resolve("KRAS")


def test_parse_canonical_ids_from_text():
    g = OntologyGrounder()
    text = "The structure UniProt:P04637 shown in PDB:2OCJ has MeSH:D016158 associated."
    ids = g.parse_canonical(text)
    canonicals = {i.canonical() for i in ids}
    assert canonicals == {"UniProt:P04637", "PDB:2OCJ", "MeSH:D016158"}


def test_ground_combines_canonical_and_symbol():
    g = OntologyGrounder()
    ids = g.ground("Study KRAS and UniProt:P04637 in pancreatic cancer.")
    canonicals = {i.canonical() for i in ids}
    assert "UniProt:P01116" in canonicals   # resolved from "KRAS"
    assert "UniProt:P04637" in canonicals   # parsed canonical
    assert "MeSH:D010190" in canonicals     # resolved from "pancreatic cancer"


def test_register_new_entity():
    g = OntologyGrounder()
    from helix_bio.models import OntologyID
    g.register("foxp3", [OntologyID(namespace="UniProt", value="Q9BZS1")])
    assert g.resolve("FOXP3")[0].canonical() == "UniProt:Q9BZS1"
