import argparse
import geopandas as gpd
import pandas as pd
import h3pandas
import h3
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
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
        "--resolution", type=int, default=11, help="H3 resolution (default: 11)"
    )
    parser.add_argument(
        "--output-format",
        choices=["png", "geojson", "both"],
        default="both",
        help="Output format: png, geojson, or both (default: both)",
    )
    return parser.parse_args()


args = parse_args()

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

# Create H3 indexes from the tree coordinates
flowering_tree_df = flowering_tree_df.to_crs(epsg=4326)  # Ensure we're using WGS84
flowering_tree_df["h3_index"] = flowering_tree_df.geometry.apply(
    lambda point: h3.latlng_to_cell(point.y, point.x, res=args.resolution)
)

flowering_tree_df["colour_hex"] = flowering_tree_df["colour"]

# Loop through each month and create separate visualizations
for month in MONTHS:
    print(f"Processing month: {month}")

    # Filter data for trees flowering in the current month
    month_column = month  # Column names are the month names (Jan, Feb, etc.)
    flowering_in_month = flowering_tree_df[
        flowering_tree_df[month_column] == True
    ].copy()

    if len(flowering_in_month) == 0:
        print(f"No trees flowering in {month}, skipping...")
        continue

    # Group by H3 index and blend colors weighted by prominence
    # First, group by H3 index to get all trees in each cell
    h3_groups = flowering_in_month.groupby("h3_index")

    if len(h3_groups) == 0:
        print(f"No H3 cells with flowering trees in {month}, skipping...")
        continue

    # Apply prominence-weighted color blending to each H3 cell
    blended_colors = []
    for h3_index, group in h3_groups:
        blended_color = blend_colors_with_prominence(group)
        if blended_color:
            # Get unique tree species names for this H3 cell
            tree_species = group["TreeName"].unique().tolist()
            blended_colors.append({
                "h3_index": h3_index, 
                "colour_hex": blended_color,
                "tree_species": tree_species
            })

    if not blended_colors:
        print(f"No valid blended colors for {month}, skipping...")
        continue

    most_frequent_colors = pd.DataFrame(blended_colors)

    # Create a GeoDataFrame for the H3 cells
    def h3_cell_to_polygon(h3_index):
        """Convert H3 cell index to a Shapely polygon"""
        boundary = h3.cell_to_boundary(h3_index)
        # Convert list of (lat, lng) tuples to list of (x, y) tuples for Shapely
        polygon_coords = [(lng, lat) for lat, lng in boundary]
        # Create a Shapely Polygon object
        return Polygon(polygon_coords)

    h3_cells = gpd.GeoDataFrame(
        most_frequent_colors,
        geometry=most_frequent_colors["h3_index"].apply(
            lambda h3_index: h3_cell_to_polygon(h3_index)
        ),
    )

    # Plot the H3 grid with cells colored by the most frequent color
    fig, ax = plt.subplots(figsize=(12, 12))

    # Create a color map from hex values
    color_list = list(colour_hexes)
    cmap = mcolors.ListedColormap(color_list)


    # Plot with proper color handling
    h3_cells.plot(
        ax=ax,
        column="colour_hex",
        cmap=cmap,
        legend=True,
        edgecolor="black",
        linewidth=0.5,
        legend_kwds={"title": "Flower Color"},
    )

    # Add title and labels
    plt.title(
        f"Bangalore Tree Distribution - {month} - H3 Resolution {args.resolution}",
        fontsize=16,
    )
    plt.xlabel("Longitude", fontsize=12)
    plt.ylabel("Latitude", fontsize=12)

    # Show the plot and save PNG if requested
    if args.output_format in ["png", "both"]:
        plt.tight_layout()
        png_filename = f"h3_tree_distribution_{month}_resolution_{args.resolution}.png"
        plt.savefig(png_filename, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Saved PNG to '{png_filename}'")
    else:
        plt.close()

    # Save GeoJSON if requested
    if args.output_format in ["geojson", "both"]:
        geojson_filename = (
            f"h3_tree_distribution_{month}_resolution_{args.resolution}.geojson"
        )

        # Prepare GeoDataFrame for GeoJSON export
        geojson_gdf = h3_cells.copy()
        geojson_gdf["month"] = month
        geojson_gdf["resolution"] = args.resolution

        # Add properties for web mapping
        geojson_gdf["prominence"] = "blended"  # Indicates this is a blended color

        # Select relevant columns for GeoJSON
        geojson_gdf = geojson_gdf[
            [
                "h3_index",
                "colour_hex",
                "tree_species",
                "prominence",
                "month",
                "resolution",
                "geometry",
            ]
        ]

        # Ensure the GeoDataFrame has the correct CRS (WGS84)
        geojson_gdf = geojson_gdf.set_crs(epsg=4326)

        # Save as GeoJSON
        geojson_gdf.to_file(geojson_filename, driver="GeoJSON")
        print(f"Saved GeoJSON to '{geojson_filename}'")

    print(f"Created H3 grid with {len(h3_cells)} cells for {month}")
