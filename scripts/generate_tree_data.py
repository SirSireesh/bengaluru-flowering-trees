#!/usr/bin/env python3
"""
Generate tree species data in JSON format from the parquet file.
This runs during the build process to avoid browser parquet reading issues.
"""

import pandas as pd
import json
import os

def main():
    # Read the parquet file
    # The script is run from the project root, so use relative path from there
    parquet_path = 'public/tree_species.parquet'
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Parquet file not found at {parquet_path}")
    df = pd.read_parquet(parquet_path)
    
    # Create tree species colors mapping
    tree_species_colors = {}
    
    for _, row in df.iterrows():
        tree_name = row['TreeName']
        colour = row['colour']
        
        # Skip if colour is null/undefined or tree is 'Others'
        if pd.notna(colour) and tree_name != 'Others':
            tree_species_colors[tree_name] = colour
    
    # Write to JSON file
    output_path = 'public/tree_species_colors.json'
    with open(output_path, 'w') as f:
        json.dump(tree_species_colors, f, indent=2)
    
    print(f"Generated tree species colors JSON: {output_path}")
    print(f"Number of species: {len(tree_species_colors)}")
    
    # Also create a minified version for production
    minified_path = 'public/tree_species_colors.min.json'
    with open(minified_path, 'w') as f:
        json.dump(tree_species_colors, f, separators=(',', ':'))
    
    print(f"Generated minified version: {minified_path}")

if __name__ == '__main__':
    main()