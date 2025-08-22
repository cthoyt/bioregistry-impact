from pathlib import Path
import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt

HERE = Path(__file__).parent.resolve()
DATA = HERE.joinpath("data")
PATH = DATA.joinpath("output.tsv")
OUT = DATA.joinpath("output.png")


def main():
    df = pd.read_csv(PATH, sep="\t")
    total = df["frequency"].sum()
    fig, ax = plt.subplots(1, 1, figsize=(8, 3))
    sns.barplot(data=df, x="itemLabel", y="frequency", ax=ax)
    ax.set_yscale("log")
    ax.set_title(
        f"Distribution of {total:,} references to software and\ndata resources that depend on the Bioregistry"
    )
    fig.tight_layout()
    fig.savefig(OUT, dpi=300)


if __name__ == "__main__":
    main()
