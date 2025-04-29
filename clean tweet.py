import re
import json
import pandas as pd
from datetime import datetime

def clean_pub_flood_data(raw_text):
    # Regular expression pattern to extract information
    pattern = r'PUB\n@PUBsingapore\n·\n([A-Za-z]+ \d+(?:, \d+)?)\n\[Risk of Flash Floods\]\s*\n\nDue to heavy rain, please avoid this location for the next 1 hour: (.*?)\s*\[(\d+:\d+) hours\]'
    
    matches = re.findall(pattern, raw_text, re.DOTALL)
    
    flood_warnings = []
    
    for match in matches:
        date_str, location, time_str = match
        
        # Handle date format (convert to YYYY-MM-DD)
        if ',' in date_str:
            date_obj = datetime.strptime(date_str, '%b %d, %Y')
        else:
            # For entries without year, assume current year (2025)
            date_obj = datetime.strptime(f"{date_str} 2025", '%b %d %Y')
        
        formatted_date = date_obj.strftime('%Y-%m-%d')
        
        # Clean and normalize location strings
        location = location.strip()
        
        # Split multiple locations if separated by semicolons
        locations = [loc.strip() for loc in location.split(';') if loc.strip()]
        
        # Create entry for each location
        for loc in locations:
            flood_warnings.append({
                'date': formatted_date,
                'time': time_str,
                'location': loc,
                'datetime': f"{formatted_date}T{time_str}:00"
            })
    
    return flood_warnings

# Read the raw data
raw_data = """PUB
@PUBsingapore
·
Apr 26
[Risk of Flash Floods] 

Due to heavy rain, please avoid this location for the next 1 hour: Riverside Road (near Junction of Riverside Road and Admiralty Road) [Issued 14:40 hours]
PUB
@PUBsingapore
·
Apr 21
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Yishun Ave 7 (near intersection of Yishun St 22) [15:18 hours]
PUB
@PUBsingapore
·
Apr 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Jln Pokok Serunai [17:19 hours]
PUB
@PUBsingapore
·
Apr 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Alexandra Rd (opp Alexis Condo) [17:19 hours]
PUB
@PUBsingapore
·
Apr 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Boon Lay Way and Corporation Rd [17:17 hours]
PUB
@PUBsingapore
·
Apr 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: KG Java Rd (Newton Circus to CTE) [17:15 hours]
PUB
@PUBsingapore
·
Apr 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Stevens Rd and Balmoral Rd [17:14 hours]
PUB
@PUBsingapore
·
Apr 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Orchard Rd (Paterson Rd to Mt Elizabeth) [17:13 hours]
PUB
@PUBsingapore
·
Apr 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Cambridge Rd;
Carlisle Rd; [17:12 hours]
PUB
@PUBsingapore
·
Apr 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Sunset Dr and Sunset Way Rd [17:06 hours]
PUB
@PUBsingapore
·
Apr 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Hillcrest Rd (Watten Rise to Dunearn Rd) [17:02 hours]
PUB
@PUBsingapore
·
Apr 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Thomson Rd (Balestier Rd to Novena Rise) [17:02 hours]
PUB
@PUBsingapore
·
Apr 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Toa Payoh Lor 1 and Toa Payoh Lor 2
 [17:00 hours]
PUB
@PUBsingapore
·
Apr 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Lor Kismis and Toh Tuck Rise [17:00 hours]
PUB
@PUBsingapore
·
Apr 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Eng Kong Pl (Greenridge Cres to Eng Kong Gdn) [16:56 hours]
PUB
@PUBsingapore
·
Apr 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Upp Paya Lebar Service Rd (Lim Teck Boo Rd to Rochdale Rd);
Jln Lokam (near Upp Paya Lebar Rd);
Thrift Dr (near Jln Usaha); [16:48 hours]
PUB
@PUBsingapore
·
Apr 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: KPE(ECP) after Buangkok East Dr Exit [16:36 hours]
PUB
@PUBsingapore
·
Apr 15
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: TPE (Punggol West Flyover) [16:55 hours]
PUB
@PUBsingapore
·
Apr 15
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Yishun Ave 7 (near intersection of Yishun St 22) [16:28 hours]


PUB
@PUBsingapore
·
Apr 13
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Jln Pokok Serunai [14:15 hours]
PUB
@PUBsingapore
·
Apr 13
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Bt Timah Rd (Wilby Rd to Blackmore Dr) [14:15 hours]
PUB
@PUBsingapore
·
Apr 13
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Lor Ong Lye (near Lor Lew Lian) [14:12 hours]
PUB
@PUBsingapore
·
Apr 13
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Toa Payoh Lor 1 and Toa Payoh Lor 2
 [14:11 hours]
PUB
@PUBsingapore
·
Apr 13
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Eng Kong Pl (Greenridge Cres to Eng Kong Gdn) [14:11 hours]
PUB
@PUBsingapore
·
Apr 13
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Upp Paya Lebar Service Rd (Lim Teck Boo Rd to Rochdale Rd);
Jln Lokam (near Upp Paya Lebar Rd);
Thrift Dr (near Jln Usaha); [14:03 hours]
PUB
@PUBsingapore
·
Apr 13
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: TPE Slip Rd towards Punggol Rd [13:56 hours]
PUB
@PUBsingapore
·
Apr 13
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: KPE(ECP) after Buangkok East Dr Exit [13:53 hours]
PUB
@PUBsingapore
·
Apr 13
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: TPE (Punggol West Flyover) [13:51 hours]
PUB
@PUBsingapore
·
Apr 13
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Yishun Ave 2 and Yishun Ave 5 [13:49 hours]
PUB
@PUBsingapore
·
Apr 13
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Yishun Avenue 7 [13:39 hours]
PUB
@PUBsingapore
·
Apr 5
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Jln Arif [18:35 hours]
PUB
@PUBsingapore
·
Mar 24
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Thomson Rd (Balestier Rd to Novena Rise) [00:37 hours]
PUB
@PUBsingapore
·
Mar 24
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Macpherson Rd OD (Siang Kuang Ave) [00:33 hours]
PUB
@PUBsingapore
·
Mar 24
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Lor Gambir
 [00:29 hours]
PUB
@PUBsingapore
·
Mar 24
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Puay Hee Ave (near Siak Kew Ave);
Siang Kuang Ave; [00:28 hours]
PUB
@PUBsingapore
·
Mar 24
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Upp Paya Lebar Service Rd (Lim Teck Boo Rd to Rochdale Rd);
Jln Lokam (near Upp Paya Lebar Rd);
Thrift Dr (near Jln Usaha); [00:28 hours]
PUB
@PUBsingapore
·
Mar 24
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Toa Payoh Lor 1 and Toa Payoh Lor 2
 [00:23 hours]
PUB
@PUBsingapore
·
Mar 24
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Langsat Rd (Everitt Rd North to Lor 106 Changi);
Lor 105 Changi; [00:20 hours]
PUB
@PUBsingapore
·
Mar 24
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Marine Parade Ctrl;
Marine Parade Rd [00:15 hours]
PUB
@PUBsingapore
·
Mar 24
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: East Coast Rd [00:12 hours]
PUB
@PUBsingapore
·
Mar 23
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Mountbatten Road/Jalan Seaview [01:31 hours]
PUB
@PUBsingapore
·
Mar 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Mountbatten Road/Jalan Seaview [13:50 hours]
PUB
@PUBsingapore
·
Mar 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: ECP (towards Changi Airport) after Bayshore Rd Exit [13:40 hours]
PUB
@PUBsingapore
·
Mar 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: ECP (towards Changi Airport) at Tanah Merah Coast Road Entrance [10:20 hours]
PUB
@PUBsingapore
·
Mar 20
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: PIE (towards Changi Airport) after TPE [07:40 hours]
PUB
@PUBsingapore
·
Mar 19
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Mountbatten Road / Jalan Seaview [14:45 hours]
PUB
@PUBsingapore
·
Mar 8
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Lor Buangkok (near Kampung Buangkok) [15:20 hours]
PUB
@PUBsingapore
·
Mar 8
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Sim Ave East (towards New Upper Changi Rd), from Lengkong Tiga to Jln Kembangan [15:20 hours]
PUB
@PUBsingapore
·
Mar 8
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Aljunied Rd under PIE Flyover [15:10 hours]
PUB
@PUBsingapore
·
Feb 17
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Braddell Road (towards Bartley) after Toa Payoh [16:30 hours]
PUB
@PUBsingapore
·
Feb 17
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Lor Gambir
 [15:56 hours]
PUB
@PUBsingapore
·
Feb 15
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Happy Ave North
 [16:20 hours]
PUB
@PUBsingapore
·
Feb 15
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Wan Tho Ave (Pheng Geck Ave) [16:08 hours]
PUB
@PUBsingapore
·
Feb 15
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Upp Paya Lebar Service Rd (Lim Teck Boo Rd to Rochdale Rd);
Jln Lokam (near Upp Paya Lebar Rd);
Thrift Dr (near Jln Usaha); [16:08 hours]

PUB
@PUBsingapore
·
Feb 15
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Lor Gambir
 [16:06 hours]
PUB
@PUBsingapore
·
Feb 15
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Puay Hee Ave (near Siak Kew Ave);
Siang Kuang Ave; [16:04 hours]
PUB
@PUBsingapore
·
Feb 15
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Toa Payoh Lor 1 and Toa Payoh Lor 2
 [15:54 hours]
PUB
@PUBsingapore
·
Jan 10
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Jln Pokok Serunai [21:15 hours]
PUB
@PUBsingapore
·
Jan 10
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Jln Seaview;
Junction of Mtbatten Rd and TG Katong Rd South; [20:02 hours]
PUB
@PUBsingapore
·
Jan 10
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Jln Seaview;
Junction of Mtbatten Rd and TG Katong Rd South; [19:23 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Thomson Rd (Balestier Rd to Novena Rise) [16:57 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Queen's Rd [16:56 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Puay Hee Ave (near Siak Kew Ave);
Siang Kuang Ave; [16:54 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Sunset Dr and Sunset Ter [16:52 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Sunset Dr and Sunset Way Rd [16:50 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Hillcrest Rd (Watten Rise to Dunearn Rd) [16:50 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Upp Paya Lebar Service Rd (Lim Teck Boo Rd to Rochdale Rd);
Jln Lokam (near Upp Paya Lebar Rd);
Thrift Dr (near Jln Usaha); [16:50 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Craig Rd (Duxton Rd to TG Pagar Rd) [16:49 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Bishan St 21 and Jln Pemimpin [16:48 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Upp Hokkien St [16:48 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Bt Timah Rd (Wilby Rd to Blackmore Dr) [16:47 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Dunearn Rd (Yarwood Ave to Binjai Pk) [16:47 hours]


PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Dunearn Rd (Yarwood Ave to Binjai Pk) [16:47 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Lor Kismis and Toh Tuck Rise [16:45 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Eng Kong Pl (Greenridge Cres to Eng Kong Gdn) [16:45 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Toa Payoh Lor 1 and Toa Payoh Lor 2
 [16:45 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Lor Gambir
 [16:43 hours]
PUB
@PUBsingapore
·
Dec 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Choa Chu Kang Ave 1 (towards Choa Chu Kang Way, Choa Chu kang Dr to Teck Whye Lane) [16:39 hours]
PUB
@PUBsingapore
·
Dec 16, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Bedok North Ave 3 (Bedok Reservoir MRT) [15:18 hours]
PUB
@PUBsingapore
·
Dec 16, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Jln Pokok Serunai [15:18 hours]
PUB
@PUBsingapore
·
Dec 16, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Upp Paya Lebar Service Rd (Lim Teck Boo Rd to Rochdale Rd);
Jln Lokam (near Upp Paya Lebar Rd);
Thrift Dr (near Jln Usaha); [15:17 hours]
PUB
@PUBsingapore
·
Dec 16, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Lor Gambir
 [15:11 hours]
PUB
@PUBsingapore
·
Dec 11, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Upp Paya Lebar Service Rd (Lim Teck Boo Rd to Rochdale Rd);
Jln Lokam (near Upp Paya Lebar Rd);
Thrift Dr (near Jln Usaha); [19:12 hours]
PUB
@PUBsingapore
·
Dec 3, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Upp East Coast Rd (near Parbury Ave) [19:32 hours]
PUB
@PUBsingapore
·
Dec 3, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Jln Pokok Serunai [19:23 hours]
PUB
@PUBsingapore
·
Dec 3, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Swan Lake Ave and Jln Terang Bulan [19:22 hours]
PUB
@PUBsingapore
·
Dec 3, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Lor Gambir
 [19:09 hours]
PUB
@PUBsingapore
·
Nov 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Bt Timah Rd (Wilby Rd to Blackmore Dr) [06:30 hours]
PUB
@PUBsingapore
·
Nov 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Dunearn Rd (Yarwood Ave to Binjai Pk) [06:27 hours]
PUB
@PUBsingapore
·
Nov 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Neo Pee Teck Lane and Pasir Panjang Rd [06:13 hours]


PUB
@PUBsingapore
·
Nov 29, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Jln Boon Lay (Enterprise Rd to International Rd) [06:03 hours]
PUB
@PUBsingapore
·
Nov 24, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Jln Boon Lay (Enterprise Rd to International Rd) [16:43 hours]
PUB
@PUBsingapore
·
Nov 23, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Lor Gambir
 [18:42 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Jln Nipah (cul-de-sac) [15:22 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Jln Seaview;
Junction of Mtbatten Rd and TG Katong Rd South; [15:22 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Choa Chu Kang Ave 1 (towards Choa Chu Kang Way, Choa Chu kang Dr to Teck Whye Lane) [15:16 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Aljunied Rd under PIE Flyover [15:14 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Upp Changi Rd and Bedok Ave 4 [15:12 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Serangoon Ave 2 (Boundary Rd to Serangoon Ave 3) [15:04 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Macpherson Rd OD (Siang Kuang Ave) [15:00 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Upp Paya Lebar Service Rd (Lim Teck Boo Rd to Rochdale Rd) [14:58 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Lor Gambir [14:58 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Serangoon Ave 2 (Boundary Rd to Serangoon Ave 3) [14:58 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Colchester Grove
 [14:57 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Junction of Macpherson Rd and Playfair Rd [14:57 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Jln Chengkek [14:55 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Jln Gembira 
 [14:54 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Wan Tho Ave (Pheng Geck Ave) [14:54 hours]
PUB
@PUBsingapore
·
Nov 22, 2024
[Risk of Flash Floods]

Due to heavy rain, please avoid this location for the next 1 hour: Mt Vernon Rd (near Bartley Rd); [14:53 hours]"""

# Clean the data
flood_warnings = clean_pub_flood_data(raw_data)

# Process data to remove duplicates
df = pd.DataFrame(flood_warnings)
df = df.drop_duplicates(subset=['date', 'time', 'location'])

# Print statistics
print(f"Extracted {len(df)} unique flood warning entries")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print(f"Number of unique locations: {df['location'].nunique()}")

# Convert back to list of dictionaries and save to JSON
clean_data = df.to_dict('records')

with open("flood_warnings_clean.json", "w") as file:
    json.dump(clean_data, file, indent=2)

# Print the first few records as an example
print("\nSample entries:")
for i, warning in enumerate(clean_data[:5]):
    print(f"{i+1}. {warning['date']} at {warning['time']} - {warning['location']}")

# Create a sample CSV file 
df.to_csv("flood_warnings_clean.csv", index=False)

# Show data summary
print("\nData Summary:")
print(df.describe(include='all'))

# Output the cleaned data
clean_data