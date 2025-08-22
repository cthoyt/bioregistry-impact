"""
This script adds annotations to Wikidata entries for OBO Foundry
ontologies that are using the Ontology Development Kit.
"""

from pathlib import Path

import bioregistry
import click
import pandas as pd
import wikidata_client
import yaml
from quickstatements_client import EntityLine
from tabulate import tabulate
from tqdm import tqdm

HERE = Path(__file__).parent.resolve()
DEV = Path.home().joinpath("dev")
ODK_REPOS_PATH = DEV.joinpath("obo-community-health", "data", "odk_repos.yaml")

DATA = HERE.joinpath("data")
DATA.mkdir(exist_ok=True)

PATH = DATA.joinpath("prefix.tsv")

#: Query for ontologies in OBO Foundry and if they have already been
#: tagged as using the ODK (P2283) or depending on ODK (P1547)
SPARQL = """\
    SELECT ?oboPrefix ?item ?usesODK
    WHERE {
      ?item wdt:P361 wd:Q4117183 .
      OPTIONAL { ?item wdt:P1813 ?oboPrefix . }
      OPTIONAL {
        ?item wdt:P1547|wdt:P2283 wd:Q112336713
        BIND(true AS ?usesODK)
      }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en". }
    }
"""


# TODO output prefix to wikidata map


def main():
    prefix_to_odk = {
        prefix: version
        for record in yaml.safe_load(ODK_REPOS_PATH.read_text())
        if (prefix := record.get("prefix")) and (version := record["version"])
    }

    obo_prefix_to_qid = {}
    obo_prefix_annotated_with_odk = set()
    for record in wikidata_client.query(SPARQL):
        obo_prefix = record["oboPrefix"].lower()
        if record.get("usesODK"):
            obo_prefix_annotated_with_odk.add(obo_prefix.casefold())
        obo_prefix_to_qid[obo_prefix] = record["item"]

    rows = []
    lines = []
    for resource in bioregistry.resources():
        if resource.is_deprecated():
            continue

        obo_prefix = resource.get_obofoundry_prefix()
        if not obo_prefix or obo_prefix.casefold() in obo_prefix_annotated_with_odk:
            continue

        qid = obo_prefix_to_qid.get(obo_prefix.lower())
        if not qid:
            tqdm.write(f"No QID found for {obo_prefix} ({resource.get_name()})")
            continue

        odk_version = prefix_to_odk.get(resource.prefix)
        if not odk_version:
            continue

        line = EntityLine(
            subject=qid,
            predicate="P1547",  # depends on software
            target="Q112336713",  # ODK entity page
        )
        lines.append(line)
        rows.append((resource.prefix, qid, odk_version))

    # quickstatements_client.lines_to_new_tab(lines)
    click.echo(tabulate(rows))
    df = pd.DataFrame(rows, columns=["prefix", "wikidata", "odk"])
    df.to_csv(PATH, sep="\t", index=False)


if __name__ == "__main__":
    main()
