import csv

# Input and output filenames
input_file = "pihole_export.txt"
output_file = "pihole_staticmaps.csv"

# Prepare rows
rows = []

with open(input_file, "r") as infile:
    for line in infile:
        parts = line.strip().split(",")
        if len(parts) >= 4:
            mac = parts[0]
            cid = parts[3]  # We'll use the hostname as client ID
            ipaddr = parts[2]
            hostname = parts[3]
            rows.append({
                "interface": "",  # Leave blank or fill manually later
                "mac": mac,
                "cid": cid,
                "ipaddr": ipaddr,
                "hostname": hostname,
                "descr": cid
            })

# Write to CSV
with open(output_file, "w", newline="") as csvfile:
    fieldnames = ["interface", "mac", "cid", "ipaddr", "hostname", "descr"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Converted {len(rows)} entries to {output_file}")
