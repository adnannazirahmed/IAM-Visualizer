import argparse
import sys
import json
from pathlib import Path

from src.pipeline import load_sample, load_live, process_iam_data
from src.iam_parser import IAMParser

def main():
    parser = argparse.ArgumentParser(description="AWS IAM Privilege-Escalation Visualizer CLI")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("input", nargs="?", help="Path to input IAM JSON file")
    group.add_argument("--sample", help="Name of the sample dataset to load")
    group.add_argument("--live", action="store_true", help="Fetch live data from AWS using boto3")
    
    parser.add_argument("--output", required=True, help="Path to save the output graph JSON")
    
    args = parser.parse_args()
    
    try:
        if args.live:
            print("Fetching live IAM data...")
            iam_data = load_live()
            source_name = "live"
        elif args.sample:
            print(f"Loading sample dataset: {args.sample}...")
            iam_data = load_sample(args.sample)
            source_name = "sample"
        else:
            print(f"Parsing input file: {args.input}...")
            input_path = Path(args.input)
            if not input_path.exists():
                print(f"Error: Input file not found: {args.input}")
                sys.exit(1)
            
            with open(input_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            
            iam_parser = IAMParser()
            iam_data = iam_parser.parse(raw_data)
            source_name = "static"
            
        print("Building graph and detecting escalations...")
        graph_output = process_iam_data(iam_data)
        graph_output.metadata.source = source_name
        
        print(f"Saving graph to {args.output}...")
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(graph_output.model_dump_json(indent=2))
            
        print("Done!")
        print(f"Nodes: {graph_output.metadata.node_count}")
        print(f"Links: {graph_output.metadata.link_count}")
        print(f"Escalations: {graph_output.metadata.escalation_count}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
