# Singapore Wedding Venue Context

Essential Singapore-specific knowledge for venue data processing.

## MRT Lines and Codes

Valid MRT line codes for validation:

- **NS** (North-South Line) - Red
- **EW** (East-West Line) - Green
- **CC** (Circle Line) - Yellow
- **CE** (Circle Line Extension) - Yellow
- **NE** (North-East Line) - Purple
- **DT** (Downtown Line) - Blue
- **TE** (Thomson-East Coast Line) - Brown
- **BP** (Bukit Panjang LRT) - Grey
- **SW** (Sengkang LRT) - Grey
- **PE** (Punggol LRT) - Grey
- **SE** (Sentosa Express) - Grey

## Postal Code to Zone Mapping

Singapore postal codes map to geographic zones:

### Central (Districts 01-28, 78)
- 01-08: City Core (Raffles Place, Marina, CBD)
- 09-10: Orchard, River Valley
- 11-13: Novena, Thomson, Balestier
- 14-16: East Coast, Geylang, Paya Lebar
- 17-19: Bukit Timah, Holland
- 20-21: Clementi, West Coast
- 22-23: Jurong East, Tuas
- 24-25: Kranji, Woodlands
- 26-27: Upper Thomson, Sembawang
- 28: Seletar, Yio Chu Kang
- 78: Harbourfront, Telok Blangah

### East (Districts 29-48)
- 29-30: Katong, Marine Parade
- 31-33: Bedok, Upper East Coast
- 34-37: Changi, Pasir Ris
- 38-41: Tampines
- 42-45: Simei, Tanah Merah
- 46-48: Bedok Reservoir

### North (Districts 49-55, 79-80)
- 49-50: Seletar, Yio Chu Kang
- 51-52: Serangoon Gardens, Hougang
- 53-55: Ang Mo Kio, Bishan
- 79-80: Woodlands, Sembawang, Yishun

### West (Districts 60-77)
- 60-64: Jurong, Tuas, Pioneer
- 65-68: Clementi, West Coast
- 69-71: Lim Chu Kang, Tengah
- 72-73: Kranji, Choa Chu Kang
- 74-77: Bukit Batok, Bukit Panjang

## Venue Types

Standard venue type classification:

### Hotel
Luxury hotels with dedicated banquet facilities:
- Keywords: hotel, resort, grand hyatt, marriott, shangri-la, fairmont, mandarin, ritz, conrad, peninsula
- Examples: Fairmont Singapore, Shangri-La, Grand Hyatt

### Restaurant
Standalone restaurants offering wedding packages:
- Keywords: restaurant, dining, bistro, café, kitchen, grill, steakhouse
- Examples: TungLok, Paradise Group, Imperial Treasure

### Banquet Hall
Dedicated event/banquet halls:
- Keywords: hall, ballroom, function room, event space, banquet
- Examples: Orchid Country Club, Singapore Conference Hall

### Club
Country clubs and recreational clubs:
- Keywords: club, country club, yacht club, golf club, recreation
- Examples: Singapore Island Country Club, Raffles Country Club

### Unique
Unique or specialty venues:
- Keywords: garden, rooftop, terrace, museum, gallery, barn, warehouse, loft, conservatory
- Examples: Gardens by the Bay, National Gallery, Fort Canning Park

## Pricing Types

Singapore wedding pricing follows two models:

### Plus Plus (++)
- Base price + 9% GST + 10% service charge
- Final cost = Base × 1.09 × 1.10 = Base × 1.199
- Example: $1,500++ = $1,798.50 final

### Nett
- All-inclusive pricing
- No additional charges
- Example: $1,800 nett = $1,800 final

## Common Pricing Ranges (2024-2025)

Per table (10 guests):
- Budget: $500-$1,200 (mostly nett)
- Mid-range: $1,200-$2,000 (usually ++)
- Premium: $2,000-$3,500 (usually ++)
- Luxury: $3,500+ (usually ++)

## Phone Number Format

Singapore phone numbers:
- Format: +65 XXXX XXXX
- Landline: starts with 6
- Mobile: starts with 8 or 9
- Toll-free: starts with 1800

## Capacity Standards

- Standard table: 10 guests
- Comfortable capacity: ~90-95% of max capacity
- Standing cocktail: 1.5-2x seated capacity

## Peak Season

Wedding peak seasons affect pricing:
- **High season**: November-December
- **Mid season**: March-June, September-October
- **Low season**: January-February, July-August

## Common Amenities

Standard amenities to check:
- AV equipment (projector, sound, microphones)
- Bridal suite/changing room
- In-house catering
- Outdoor area
- Air conditioning
- Valet parking
- Multiple ballrooms
- Waterfront/city/garden views

## Validation Boundaries

Singapore geographic bounding box for geocoding:
- North: 1.470 latitude
- South: 1.150 latitude
- East: 104.100 longitude
- West: 103.600 longitude

Any coordinates outside this box should be flagged as invalid.
