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
            count = pubmed_downloader.count_search_results(query)
        except Exception:
            tqdm.write(f"failed on {resource.prefix}")
            continue
        else:
            rows.append((resource.prefix, resource.get_name() or "", query, count))

        if i % 20 == 0:
            _write(rows)

    _write(rows)


def _write(rows: list[tuple[str, str, str, str]]) -> None:
    df = pd.DataFrame(rows, columns=["prefix", "name", "query", "count"])
    df.to_csv(PATH, sep="\t", index=False)


def resource_to_pubmed_query(resource: bioregistry.Resource) -> str:
    name = resource.get_name()
    phrases = [
        name,
    ]
    if pp := resource.get_preferred_prefix():
        phrases.append(f"{name} ({pp})")
        phrases.append(pp)
    return " OR ".join(f'"{phrase}"' for phrase in phrases)


if __name__ == "__main__":
    main()
