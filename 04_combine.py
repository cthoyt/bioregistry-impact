from pathlib import Path
import bioregistry
import pandas as pd
import pubmed_downloader
from tqdm import tqdm
import click

HERE = Path(__file__).parent.resolve()
DATA = HERE.joinpath("data")
PATH = DATA.joinpath("output.tsv")


@click.command()
def main():
    count_df = pd.read_csv(DATA.joinpath("literature_frequencies.tsv"), sep='\t')
    count_df['wikidata'] = count_df['prefix'].map(bioregistry.get_registry_map("wikidata.entity"))
    dd = dict(count_df[count_df['wikidata'].notna()][['wikidata', 'count']].values)
    print(dd)

    depdendency_df = pd.read_csv(DATA.joinpath("depdends_on_bioregistry.tsv"), sep='\t', dtype=str)
    for item, label in tqdm(depdendency_df[['item', 'itemLabel']].values):
        if item not in dd:
            try:
                count = pubmed_downloader.count_search_results('"' + label + '"', retmax=10)
            except Exception:
                tqdm.write(f"failed on {item} / {label}")
                continue
            else:
                dd[item] = count

    depdendency_df['frequency'] = depdendency_df['item'].map(dd)
    depdendency_df = depdendency_df[depdendency_df['frequency'].notna() & (depdendency_df['frequency'] > 0)]
    depdendency_df['frequency'] = depdendency_df['frequency'].astype(int)
    depdendency_df.sort_values("frequency", ascending=False, inplace=True)
    depdendency_df.to_csv(PATH, sep='\t', index=False)


if __name__ == '__main__':
    main()
