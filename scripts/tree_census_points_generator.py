import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd

MONTHS = [
    "JAN",
    "FEB",
    "MAR",
    "APR",
    "MAY",
    "JUN",
    "JUL",
    "AUG",
    "SEP",
    "OCT",
    "NOV",
    "DEC",
]


def convert_text_range_to_months(range_text: str) -> dict[str, bool]:
    if not isinstance(range_text, str):
        print(type(range_text), range_text)
    flowering_months = {m: False for m in MONTHS}
    for r in range_text.split(";"):
        start_month, end_month = map(int, r.split("-"))
        for i in range(
            start_month - 1, end_month - 1 + 1
        ):  # -1 to get to 0 index, + 1 since we're using both inclusive
            flowering_months[MONTHS[i]] = True
    return flowering_months


def main():
    parser = argparse.ArgumentParser(prog="tree_census_points_generator")
    parser.add_argument("--tree-census-data")
    parser.add_argument("--tree-bloom-data")
    parser.add_argument("--output-dir")

    args = parser.parse_args()

    tree_census = gpd.read_file(args.tree_census_data)
    tree_bloom = pd.read_parquet(args.tree_bloom_data)
    print(len(tree_census))

    tree_census = tree_census.merge(tree_bloom, on=["TreeName"], how="left")
    tree_census = tree_census[
        ["geometry", "TreeName", "months", "colour", "prominence"]
    ]
    tree_census = tree_census.dropna(subset=["months"]).reset_index(drop=True)
    print(len(tree_census))

    tree_census["months"].apply(convert_text_range_to_months)
    tree_census["months_flowering"] = tree_census["months"].apply(convert_text_range_to_months)
    tree_census = tree_census.join(tree_census["months_flowering"].apply(pd.Series))
    print(tree_census)
    
    # Write all trees data
    tree_census[["TreeName", "colour", "prominence", "geometry"]].to_file(Path(args.output_dir) / "trees_all.geojson")

    # Write monthly files
    for month in MONTHS:
        month_data = tree_census.loc[tree_census[month]]
        month_data.set_crs(epsg=4326)
        month_data[["TreeName", "colour", "prominence", "geometry"]].to_file(Path(args.output_dir) / f"trees_{month}.geojson")


if __name__ == "__main__":
    main()
