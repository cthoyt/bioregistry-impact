import wikidata_client
import pandas as pd
from pathlib import Path
import bioregistry

HERE = Path(__file__).parent.resolve()
DATA = HERE.joinpath("data")
PATH = DATA.joinpath("depdends_on_bioregistry.tsv")

#: A SPARQL query that looks through the transitive software dependencies/uses
#: of the Bioregistry (Q109302681) and curies (Q116738064)
SPARQL = """\
    SELECT DISTINCT
        ?item ?shortName ?itemLabel ?itemDescription (GROUP_CONCAT(DISTINCT ?type; separator="|") as ?types)
    WHERE {
        VALUES ?software { wd:Q109302681 wd:Q116738064 }
        ?item (wdt:P1547|wdt:P2283)+ ?software .
        OPTIONAL { ?item wdt:P1813 ?shortName . }
        ?item wdt:P31/rdfs:label ?type .
        FILTER(lang(?type) = 'en')
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en". }
    }
    GROUP BY ?item ?shortName ?itemLabel ?itemDescription
    ORDER BY ?shortName
"""


def main():
    r = wikidata_client.query(SPARQL)
    # TODO categorize
    df = pd.DataFrame(r).replace(pd.NA, "").sort_values("shortName")
    df = df.drop_duplicates()
    df = df[df['itemLabel'].map(lambda s: not s.startswith("bio2bel-"))]
    df['bioregistry'] = df['item'].map(bioregistry.get_registry_invmap("wikidata.entity"))
    df.to_csv(PATH, sep='\t', index=False)


if __name__ == '__main__':
    main()
