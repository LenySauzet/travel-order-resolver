import pandas as pd
import os
import re

def parse_time_to_minutes(time_str):
    """Converts HH:MM:SS string to minutes from midnight. Handles times > 24h."""
    if pd.isna(time_str):
        return None
    try:
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        return hours * 60 + minutes + seconds / 60
    except Exception:
        return None

def extract_uic(stop_id: str) -> str | None:
    """
    Extracts the numeric UIC code from a GTFS stop_id.
    Examples:
    - "StopPoint:OCETGV INOUI-71043075" -> "71043075"
    - "StopArea:OCE87586461" -> "87586461"
    """
    if pd.isna(stop_id):
        return None
    
    # Check for the pattern [Prefix]-[Number] or just [Number] at the end
    # Using regex to find the last sequence of digits
    match = re.search(r'(\d+)$', stop_id)
    if match:
        return match.group(1)
    return None

def main():
    base_path = 'base/data/Export_OpenData_SNCF_GTFS_NewTripId'
    stops_file = os.path.join(base_path, 'stops.txt')
    stop_times_file = os.path.join(base_path, 'stop_times.txt')

    print("Loading data...")
    # Load stops
    stops_df = pd.read_csv(stops_file)
    
    # Create mapping from stop_id to UIC code
    # We will use this to replace stop_id with UIC in the graph
    stops_df['uic_code'] = stops_df['stop_id'].apply(extract_uic)
    
    # Filter out stops where UIC couldn't be extracted
    valid_stops = stops_df.dropna(subset=['uic_code'])
    stop_map = valid_stops.set_index('stop_id')['uic_code'].to_dict()
    
    # Also create a mapping for station names (just for debugging/verification if needed)
    # or if we want to include names in the output CSV for readability
    name_map = valid_stops.set_index('stop_id')['stop_name'].to_dict()

    # Load stop_times
    # Use only necessary columns to save memory if file is large
    stop_times_df = pd.read_csv(stop_times_file, usecols=['trip_id', 'stop_id', 'arrival_time', 'departure_time', 'stop_sequence'])
    
    print("Processing stop times...")
    # Convert time strings to minutes
    stop_times_df['arrival_min'] = stop_times_df['arrival_time'].apply(parse_time_to_minutes)
    stop_times_df['departure_min'] = stop_times_df['departure_time'].apply(parse_time_to_minutes)
    
    # Sort by trip and sequence
    stop_times_df = stop_times_df.sort_values(['trip_id', 'stop_sequence'])
    
    # Create segments by shifting
    stop_times_df['next_stop_id'] = stop_times_df['stop_id'].shift(-1)
    stop_times_df['next_arrival_min'] = stop_times_df['arrival_min'].shift(-1)
    stop_times_df['next_trip_id'] = stop_times_df['trip_id'].shift(-1)
    
    # Filter where next_trip_id == trip_id (valid segment)
    segments = stop_times_df[stop_times_df['trip_id'] == stop_times_df['next_trip_id']].copy()
    
    # Calculate duration
    segments['duration_min'] = segments['next_arrival_min'] - segments['departure_min']
    
    # Filter out negative durations
    segments = segments[segments['duration_min'] >= 0]
    
    # Map stop IDs to UIC codes
    segments['source_uic'] = segments['stop_id'].map(stop_map)
    segments['target_uic'] = segments['next_stop_id'].map(stop_map)
    
    # Add names for readability/debugging
    segments['source_name'] = segments['stop_id'].map(name_map)
    segments['target_name'] = segments['next_stop_id'].map(name_map)
    
    # Drop rows where UICs are missing
    segments = segments.dropna(subset=['source_uic', 'target_uic'])
    
    # Aggregate: Find minimum duration between two stations (by UIC)
    print("Aggregating durations...")
    # Group by UICs now instead of names
    graph_edges = segments.groupby(['source_uic', 'target_uic'])['duration_min'].min().reset_index()
    
    # Rename columns
    graph_edges.rename(columns={'duration_min': 'weight_minutes'}, inplace=True)
    
    # Add representative names back (optional, but helpful)
    # We can take the first name associated with each UIC from our stops df
    uic_to_name = valid_stops.drop_duplicates(subset=['uic_code']).set_index('uic_code')['stop_name'].to_dict()
    graph_edges['source_name'] = graph_edges['source_uic'].map(uic_to_name)
    graph_edges['target_name'] = graph_edges['target_uic'].map(uic_to_name)
    
    # Reorder columns
    graph_edges = graph_edges[['source_uic', 'target_uic', 'weight_minutes', 'source_name', 'target_name']]
    
    # Save to CSV
    output_file = 'base/data/station_durations.csv'
    graph_edges.to_csv(output_file, index=False)
    print(f"Graph edges saved to {output_file}")
    print(graph_edges.head())

if __name__ == "__main__":
    main()
