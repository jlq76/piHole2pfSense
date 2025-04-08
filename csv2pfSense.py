import xml.etree.ElementTree as ET
import csv
import argparse
from xml.dom import minidom
import re

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Update pfSense DHCP config from CSV")
parser.add_argument('--csv', required=True, help="Path to the CSV file containing static mappings")
parser.add_argument('--input-xml', required=True, help="Path to the input config XML file")
parser.add_argument('--output-xml', required=True, help="Path to the output config XML file")
parser.add_argument('--overwrite', action='store_true', help="Remove existing staticmaps before adding new ones")
args = parser.parse_args()

# Read CSV data
csv_data = {}
with open(args.csv, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Ensure required fields are not missing
        if not row["interface"] or not row["mac"] or not row["ipaddr"] or not row["hostname"]:
            print(f"Invalid row (missing required fields): {row}")
            continue  # Skip this row if any of the required fields are missing
        
        iface = row["interface"].strip()  
        if iface not in csv_data:
            csv_data[iface] = []
        csv_data[iface].append(row)


# Parse XML
tree = ET.parse(args.input_xml)
root = tree.getroot()

# Fields required in each staticmap block (found in the pfsense export file)
required_fields = [
    "mac", "cid", "ipaddr", "hostname", "descr", 
    "filename", "rootpath", "defaultleasetime", "maxleasetime", "gateway", "domain",
    "domainsearchlist", "ddnsdomain", "ddnsdomainprimary", "ddnsdomainsecondary",
    "ddnsdomainkeyname", "ddnsdomainkeyalgorithm", "ddnsdomainkey",
    "tftp", "ldap", "nextserver", "filename32", "filename64",
    "filename32arm", "filename64arm", "uefihttpboot", "numberoptions"
]

# If the --overwrite flag is set, remove existing staticmaps
if args.overwrite:
    for interface in root:
        if interface.tag in csv_data:
            for sm in interface.findall("staticmap"):
                interface.remove(sm)
            print(f"Removed existing staticmaps for {interface.tag}")

# Add or update staticmap entries for interfaces specified in the CSV
for interface in root:
    if interface.tag in csv_data:
        # Collect existing staticmap elements and their MAC addresses for the interface
        existing_staticmaps = {sm.find('mac').text: sm for sm in interface.findall("staticmap")}
        
        for row in csv_data[interface.tag]:
            mac = row.get("mac", "")
            
            # Check if staticmap with this MAC exists
            if mac in existing_staticmaps:
                # Update the existing staticmap
                sm = existing_staticmaps[mac]
                for tag in required_fields:
                    val = row.get(tag, "") if tag in row else ""
                    tag_elem = sm.find(tag)

                # Handle <arp_table_static_entry>
                arp_entry = row.get("arp_table_static_entry", "").strip()
                arp_tag_elem = sm.find("arp_table_static_entry")
                if arp_entry == "x":
                    # If it's "x", add the <arp_table_static_entry> tag if not present
                    if arp_tag_elem is None:
                        ET.SubElement(sm, "arp_table_static_entry").text = "x"
                        print(f"Added <arp_table_static_entry> for MAC {mac} ({row.get('hostname')}) in interface {interface.tag}")
                else:
                    # If it's empty, remove the <arp_table_static_entry> tag if present
                    if arp_tag_elem is not None:
                        sm.remove(arp_tag_elem)
                        print(f"Removed <arp_table_static_entry> for MAC {mac} ({row.get('hostname')}) in interface {interface.tag}")

                print(f"Updated staticmap with MAC {mac} ({row.get('hostname')}) for interface {interface.tag}")
            else:
                # Add a new staticmap for this MAC
                sm = ET.SubElement(interface, "staticmap")
                for tag in required_fields:
                    val = row.get(tag, "") if tag in row else ""
                    ET.SubElement(sm, tag).text = val

                # Handle <arp_table_static_entry> for the new staticmap
                arp_entry = row.get("arp_table_static_entry", "").strip()
                if arp_entry == "x":
                    ET.SubElement(sm, "arp_table_static_entry").text = "x"
                    print(f"Added <arp_table_static_entry> for MAC {mac} ({row.get('hostname')}) to interface {interface.tag}")

                print(f"Added new staticmap with MAC {mac} ({row.get('hostname')}) to interface {interface.tag}")


# Convert to pretty XML
rough_string = ET.tostring(root, encoding="unicode")
parsed = minidom.parseString(rough_string)
pretty_xml = parsed.toprettyxml(indent="\t")

# Fix empty tags <tag/> → <tag></tag>
pretty_xml = re.sub(r"<(\w+?)\s*/>", r"<\1></\1>", pretty_xml)

# Inject CDATA into <descr>
def inject_cdata(text):
    def replace_descr(match):
        content = match.group(1)
        return f"<descr><![CDATA[{content}]]></descr>" if content.strip() else "<descr></descr>"
    return re.sub(r"<descr>(.*?)</descr>", replace_descr, text, flags=re.DOTALL)

pretty_xml = inject_cdata(pretty_xml)
# Remove multiple consecutive empty lines
pretty_xml = re.sub(r'\n\s*\n+', '\n', pretty_xml)

# Remove XML declaration line
pretty_xml = "\n".join(line for line in pretty_xml.splitlines() if not line.strip().startswith("<?xml"))

# Write output
with open(args.output_xml, "w", newline="\n") as f:
    f.write(pretty_xml)

print(f"✅ Updated config written to {args.output_xml}")
