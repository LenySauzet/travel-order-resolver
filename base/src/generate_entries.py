import pandas as pd
import unicodedata
import re
import os

def normalize_text(text: str) -> str:
    """Normalize text for fuzzy matching (lowercase, no accents, no punctuation)."""
    if pd.isna(text):
        return ""
    text = text.lower()
    # Remove accents
    normalized = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in normalized if not unicodedata.combining(c))
    # Remove punctuation
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # Collapse whitespace
    return re.sub(r'\s+', ' ', text).strip()

def main():
    input_file = "base/data/raw/gares-de-voyageurs.csv"
    output_file = "base/data/processed/entries.csv"
    
    print(f"Reading from {input_file}...")
    df = pd.read_csv(input_file, sep=";")
    
    # Columns in raw file: Nom;Trigramme;Segment(s) DRG;Position géographique;Code commune;Code(s) UIC
    
    # Load valid UICs from the graph
    graph_file = "base/data/station_durations.csv"
    valid_uics = set()
    if os.path.exists(graph_file):
        print(f"Loading valid UICs from {graph_file}...")
        graph_df = pd.read_csv(graph_file)
        if 'source_uic' in graph_df.columns and 'target_uic' in graph_df.columns:
            valid_uics.update(graph_df['source_uic'].dropna().astype(str).unique())
            valid_uics.update(graph_df['target_uic'].dropna().astype(str).unique())
        print(f"Found {len(valid_uics)} unique valid UICs in the routing graph.")
    else:
        print(f"Warning: Graph file {graph_file} not found. No filtering will be applied.")

    entries = []
    
    for idx, row in df.iterrows():
        raw_name = row['Nom']
        uics_raw = str(row['Code(s) UIC'])
        pos_geo = str(row['Position géographique'])
        
        # Parse UICs: take the first one as primary
        uic_list = [u.strip() for u in uics_raw.split(';') if u.strip()]
        primary_uic = uic_list[0] if uic_list else None
        
        if not primary_uic:
            # print(f"Skipping {raw_name}: No UIC code found.")
            continue
            
        # Filter: Check if UIC exists in the graph
        if valid_uics and primary_uic not in valid_uics:
            # print(f"Skipping {raw_name} ({primary_uic}): Not in routing graph.")
            continue

            
        # Parse Lat/Lon from "49.6852237, 1.7743058"
        lat, lon = None, None
        try:
            parts = pos_geo.split(',')
            if len(parts) == 2:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
        except ValueError:
            print(f"Skipping coords for {raw_name}: Invalid format '{pos_geo}'")
            
        # Normalize name for matching
        normalized_name = normalize_text(raw_name)
        
        entry = {
            "index": idx, # Stable index from original CSV order
            "raw": raw_name,
            "uic": primary_uic,
            "lat": lat,
            "lon": lon,
            "entries": normalized_name
        }
        entries.append(entry)
        
    # Create DataFrame
    result_df = pd.DataFrame(entries)
    
    # Save to CSV
    print(f"Saving {len(result_df)} entries to {output_file}...")
    result_df.to_csv(output_file, index=False)
    print("Done.")

if __name__ == "__main__":
    main()
