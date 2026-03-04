import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import h3pandas
import h3
from shapely.geometry import Polygon


# Parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate H3 tree distribution visualizations and GeoJSON"
    )
    parser.add_argument(
        "--tree-census-path", type=str, help="Path to the tree census file"
    )
    parser.add_argument(
        "--tree-species-data", type=str, help="Path to the tree species data"
    )
    parser.add_argument(
        "--resolutions", 
        type=str, 
        default="11", 
        help="Comma-separated list of H3 resolutions (default: 11)"
    )
    parser.add_argument(
        "--output-format",
        choices=["png", "geojson", "both"],
        default="both",
        help="Output format: png, geojson, or both (default: both)",
    )
    parser.add_argument(
        "--output-dir",
        help="The directory to store the resultant files in",
    )
    return parser.parse_args()


args = parse_args()

# Parse resolutions from comma-separated string
resolutions = [int(r.strip()) for r in args.resolutions.split(",")]

# Define prominence weights
prominence_weights = {"low": 1.0, "med": 2.0, "high": 3.0}


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    """Convert RGB tuple to hex color"""
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def blend_colors_with_prominence(group):
    """Blend colors in a group weighted by prominence"""
    # Get colors and their prominence weights
    colors = []
    weights = []

    for _, row in group.iterrows():
        if pd.notna(row["colour"]) and pd.notna(row["prominence"]):
            colors.append(hex_to_rgb(row["colour_hex"]))
            weights.append(prominence_weights[row["prominence"]])

    if not colors:
        return None

    # Normalize weights
    total_weight = sum(weights)
    if total_weight == 0:
        return None

    # Calculate weighted average in RGB space
    r = sum(c[0] * w for c, w in zip(colors, weights)) / total_weight
    g = sum(c[1] * w for c, w in zip(colors, weights)) / total_weight
    b = sum(c[2] * w for c, w in zip(colors, weights)) / total_weight

    return rgb_to_hex((int(r), int(g), int(b)))


# Load data (outside resolution loop)
gdf = gpd.read_file(args.tree_census_path)
tree_data = pd.read_parquet(args.tree_species_data)

colour_hexes = tree_data.colour.dropna().unique()

# Drop rows with NA values in relevant columns
tree_data.dropna(subset=["months", "colour"], inplace=True)

MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def convert_text_range_to_months(range_text: str) -> dict[str, bool]:
    flowering_months = {m: False for m in MONTHS}
    for r in range_text.split(";"):
        start_month, end_month = map(int, r.split("-"))
        for i in range(
            start_month - 1, end_month - 1 + 1
        ):  # -1 to get to 0 index, + 1 since we're using both inclusive
            flowering_months[MONTHS[i]] = True
    return flowering_months


tree_data["months_flowering"] = tree_data["months"].apply(convert_text_range_to_months)

tree_data = tree_data.join(tree_data["months_flowering"].apply(pd.Series))

flowering_tree_df = gdf.merge(tree_data, on=["TreeName"])

# Ensure we're using WGS84
flowering_tree_df = flowering_tree_df.to_crs(epsg=4326)
flowering_tree_df["colour_hex"] = flowering_tree_df["colour"]

# Sort resolutions from lowest to highest for optimization
resolutions_sorted = sorted(resolutions)

# Dictionary to store H3 indexes at different resolutions
# Key: resolution, Value: dataframe with index
resolution_h3_indexes = {}

# Loop through each resolution
for resolution in resolutions_sorted:
    print(f"\nProcessing resolution: {resolution}")

    # Loop through each month and create separate visualizations
    for month in MONTHS:
        print(f"Processing month: {month}")

        # Filter data for trees flowering in the current month
        month_column = month  # Column names are the month names (Jan, Feb, etc.)
        flowering_in_month = flowering_tree_df[
            flowering_tree_df[month_column]
        ].copy()

        # Add the count of each species within the cell
        # Group by H3 index and count species
        flowering_in_month = flowering_in_month.h3.geo_to_h3(resolution)

        # Group by H3 index (which is now in the DataFrame index) and get counts for each tree name
        h3_groups = flowering_in_month.groupby(level=0)

        # Count species within each H3 cell
        h3_species_counts = []
        for h3_index, group in h3_groups:
            # Count each species in this H3 cell
            species_counts = group["TreeName"].value_counts().to_dict()
            h3_species_counts.append({
                "h3_index": h3_index,
                "species_counts": species_counts,
                "total_trees": len(group),
            })

        if not h3_species_counts:
            print(f"No trees in H3 cells for {month}, skipping...")
            continue

        # Create DataFrame with species counts
        h3_counts_df = pd.DataFrame(h3_species_counts)

        # Create a GeoDataFrame for the H3 cells
        def h3_cell_to_polygon(h3_index):
            """Convert H3 cell index to a Shapely polygon"""
            boundary = h3.cell_to_boundary(h3_index)
            # Convert list of (lat, lng) tuples to list of (x, y) tuples for Shapely
            polygon_coords = [(lng, lat) for lat, lng in boundary]
            # Create a Shapely Polygon object
            return Polygon(polygon_coords)

        h3_cells = gpd.GeoDataFrame(
            h3_counts_df,
            geometry=h3_counts_df["h3_index"].apply(
                lambda h3_index: h3_cell_to_polygon(h3_index)
            ),
        )

        # Save GeoJSON if requested
        if args.output_format in ["geojson", "both"]:
            geojson_filename = (
                f"h3_tree_distribution_{month}_resolution_{resolution}.geojson"
            )

            # Prepare GeoDataFrame for GeoJSON export
            geojson_gdf = h3_cells.copy()
            geojson_gdf["month"] = month
            geojson_gdf["resolution"] = resolution

            # Select relevant columns for GeoJSON
            geojson_gdf = geojson_gdf[
                [
                    "h3_index",
                    "month",
                    "resolution",
                    "geometry",
                    "species_counts",
                ]
            ]

            # Ensure the GeoDataFrame has the correct CRS (WGS84)
            geojson_gdf = geojson_gdf.set_crs(epsg=4326)

            # Save as GeoJSON
            geojson_gdf.to_file(Path(args.output_dir) / geojson_filename, driver="GeoJSON")
            print(f"Saved GeoJSON to '{geojson_filename}'")

        print(f"Created H3 grid with {len(h3_cells)} cells for {month}")

# After processing all months and resolutions, generate the tree species colors JSON file
print("\nGenerating tree species colors JSON file...")

# Filter out 'Others' and rows with NaN colours
tree_data_filtered = tree_data[tree_data["TreeName"] != "Others"]
tree_data_filtered = tree_data_filtered.dropna(subset=["colour"])

# Create a dictionary of species to color
species_colors = {}
for idx, row in tree_data_filtered.iterrows():
    tree_name = row["TreeName"]
    colour = row["colour"]

    # Store both the full name and a cleaned version (without scientific names)
    species_colors[tree_name] = colour

# Save to JSON
json_filename = "tree_species_colors.json"
with open(Path(args.output_dir) / json_filename, "w") as f:
    json.dump(species_colors, f, indent=2)

print(
    f"Saved tree species colors to '{json_filename}' with {len(species_colors)} entries"
)
print("Sample entries:")
for i, (species, color) in enumerate(list(species_colors.items())[:10]):
    print(f"  '{species}' -> {color}")
