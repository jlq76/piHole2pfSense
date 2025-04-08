import sys
import xml.etree.ElementTree as ET 
import csv  
import argparse  

# Parse the arguments
parser = argparse.ArgumentParser(description="Parse an XML file and export static mappings to a CSV file.")
parser.add_argument("--input-file", required=True, help="Path to the input XML file")  
parser.add_argument("--output-file", required=True, help="Path to the output CSV file")
args = parser.parse_args()
input_file = args.input_file  
output_file = args.output_file  

# Parse the XML file and get its root element
tree = ET.parse(input_file)
root = tree.getroot()  
# Check if the root element is <dhcpd>
if root.tag != "dhcpd":
    print(f"Unexpected root element: {root.tag}. Expected <dhcpd>.")
    sys.exit(1)

# Iterate through the interfaces
rows = []
for interface in root:  
    if interface.tag.startswith("lan") or interface.tag.startswith("opt"):
        for staticmap in interface.findall("staticmap"):
            # Check for ARP static entry presence
            arp_table_static_entry = staticmap.find("arp_table_static_entry") is not None

            # Collect all <dnsserver> entries
            dnsservers = [dns.text for dns in staticmap.findall("dnsserver") if dns.text]
            dnsservers_csv = "|".join(dnsservers)

            row = {
                "interface": interface.tag,  
                "mac": staticmap.findtext("mac", ""),  
                "cid": staticmap.findtext("cid", ""),  
                "ipaddr": staticmap.findtext("ipaddr", ""),
                "hostname": staticmap.findtext("hostname", ""), 
                "descr": staticmap.findtext("descr", ""),  
                "arp_table_static_entry": "x" if arp_table_static_entry else "",
                "dnsservers": dnsservers_csv
            }
            rows.append(row)

# Write the CSV file with the new field included
with open(output_file, "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=[
        "interface", "mac", "cid", "ipaddr", "hostname", "descr", "arp_table_static_entry", "dnsservers"
    ])
    writer.writeheader()  
    writer.writerows(rows)

# Print the number of exported static mappings to the console
print(f"Exported {len(rows)} static mappings to {output_file}")
