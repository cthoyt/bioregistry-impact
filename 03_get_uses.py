import wikidata_client
import pandas as pd
from pathlib import Path

HERE = Path(__file__).parent.resolve()
DATA = HERE.joinpath("data")
PATH = DATA.joinpath("depdends_on_bioregistry.tsv")

#: A SPARQL query that looks through the transitive software dependencies/uses
#: of the Bioregistry (Q109302681) and curies (Q116738064)
SPARQL = """\
    SELECT DISTINCT
        ?item ?shortName ?itemLabel ?itemDescription
    WHERE {
        VALUES ?software { wd:Q109302681 wd:Q116738064 }
        ?item (wdt:P1547|wdt:P2283)+ ?software .
        OPTIONAL { ?item wdt:P1813 ?shortName . }
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en". }
    }
"""


def main():
    r = wikidata_client.query(SPARQL)
    df = pd.DataFrame(r).replace(pd.NA, "").sort_values("shortName")
    df = df[df['itemLabel'].map(lambda s: not s.startswith("bio2bel-"))]
    df.to_csv(PATH, sep='\t', index=False)


if __name__ == '__main__':
    main()
