import csv
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Convert a Pi-hole export file to a CSV file")
parser.add_argument("--input-file", required=True, help="Path to the input file (e.g., pihole_export.txt)")
parser.add_argument("--output-file", required=True, help="Path to the output file (e.g., pihole_staticmaps.csv)")
args = parser.parse_args()

input_file = args.input_file
output_file = args.output_file

# Prepare rows
rows = []

with open(input_file, "r") as infile:
    for line in infile:
        parts = line.strip().split(",")
        if len(parts) >= 4:
            mac = parts[0]
            ipaddr = parts[2]
            hostname = parts[3]
            rows.append({
                "interface": "",  # Leave blank to fill manually later
                "mac": mac,
                "cid": hostname,
                "ipaddr": ipaddr,
                "hostname": hostname,
                "descr": hostname
            })

# Write to CSV
with open(output_file, "w", newline="") as csvfile:
    fieldnames = ["interface", "mac", "cid", "ipaddr", "hostname", "descr"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Converted {len(rows)} entries to {output_file}")
