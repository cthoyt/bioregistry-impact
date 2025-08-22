# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "bioregistry",
#     "click",
#     "pandas",
#     "pubmed-downloader",
#     "pystow",
#     "tqdm",
# ]
# ///

"""
Construct search queries for ontologies listed in Bioregistry, and get relative citations.

Some ideas:
Method 1:

1. Create grounder for OBO Foundry ontologies
2. Run annotation pipeline on all pubmed via pubmed_downloader

Method 2 (faster)

1. For each ontology name, search pubmed and report number of articles
"""

import bioregistry
import pubmed_downloader
from pathlib import Path
import pandas as pd
import click
from tqdm import tqdm
from pystow.utils import safe_open_reader

HERE = Path(__file__).parent.resolve()
DATA = HERE.joinpath("data")
DATA.mkdir(exist_ok=True)
PATH = DATA.joinpath("literature_frequencies.tsv")

USE_PP = {
    "doid",
}


@click.command()
@click.option("--refresh", is_flag=True)
def main(refresh: bool) -> None:
    rows = []

    # load up existing results, if they exist already
    if PATH.is_file() and not refresh:
        with safe_open_reader(PATH) as reader:
            rows.extend(reader)

    resources = bioregistry.resources()

    for i, resource in enumerate(tqdm(resources, unit="resource")):
        query = resource_to_pubmed_query(resource)
        try:
            count = pubmed_downloader.count_search_results(query, retmax=10)
        except Exception:
            tqdm.write(f"failed on {resource.prefix}")
            continue
        else:
            rows.append(
                (
                    resource.prefix,
                    resource.get_wikidata_entity(),
                    resource.get_name() or "",
                    query,
                    count,
                )
            )

        if i % 20 == 0:
            _write(rows)

    _write(rows)


def _write(rows: list[tuple[str, str, str, str]]) -> None:
    df = pd.DataFrame(rows, columns=["prefix", "wikidata", "name", "query", "count"])
    df.sort_values(["count", "prefix"], ascending=(False, True), inplace=True)
    df.to_csv(PATH, sep="\t", index=False)


def resource_to_pubmed_query(resource: bioregistry.Resource) -> str:
    name = resource.get_name()
    phrases = [
        name,
    ]
    if preferred_prefix := resource.get_preferred_prefix():
        phrases.append(f"{name} ({preferred_prefix})")
        if resource.prefix in USE_PP:
            phrases.append(preferred_prefix)
    return " OR ".join(f'"{phrase}"[tw]' for phrase in phrases)


if __name__ == "__main__":
    main()
