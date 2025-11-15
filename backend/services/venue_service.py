"""
Venue Service - Simple JSON loader for wedding venues
No vector DB, no pandas - just pure Python filtering
"""

import json

from backend.config import config


class VenueService:
    """Simple venue data loader - no vector DB"""

    def __init__(self):
        # Path to venues.json from config
        self.data_file = config.VENUES_FILE

    def load_all_venues(self) -> list[dict]:
        """Load all venues from JSON"""
        with open(self.data_file) as f:
            data = json.load(f)
        return data["venues"]

    def search(
        self,
        guest_count: int,
        total_budget: int,
        location_zone: str | None = None,
        max_price_per_table: int | None = None,
    ) -> list[dict]:
        """
        Filter venues by capacity, budget, and optional location

        Returns:
            List of matching venues sorted by rating
        """
        venues = self.load_all_venues()

        # Calculate tables needed (10 guests per table, round up)
        tables_needed = (guest_count + 9) // 10

        # Calculate budget per table
        budget_per_table = total_budget / tables_needed if tables_needed > 0 else 0

        # Use provided max or calculated budget (with 20% buffer)
        max_price = max_price_per_table or (budget_per_table * 1.2)

        # Filter by capacity and budget
        filtered = []
        for v in venues:
            capacity = v.get("capacity", {})
            pricing = v.get("pricing", {})
            location = v.get("location", {})

            # Check capacity constraints
            min_tables = capacity.get("min_tables", 0)
            max_capacity = capacity.get("max_capacity", 0)

            if max_capacity < guest_count:
                continue  # Too small
            if min_tables > tables_needed:
                continue  # Minimum too high

            # Check budget constraints
            price_per_table = pricing.get("price_per_table", 0)
            if price_per_table > max_price:
                continue  # Too expensive

            # Check minimum spend
            min_spend = pricing.get("min_spend", 0)
            if total_budget < min_spend:
                continue  # Below minimum spend

            # Optional location filter
            if location_zone:
                venue_zone = location.get("zone", "")
                if location_zone.lower() not in venue_zone.lower():
                    continue

            filtered.append(v)

        # Sort by rating (descending)
        filtered = sorted(filtered, key=lambda x: x.get("rating", 0), reverse=True)

        return filtered[:10]  # Top 10

    def get_venue_by_id(self, venue_id: str) -> dict | None:
        """Get a specific venue by ID"""
        venues = self.load_all_venues()
        for venue in venues:
            if venue.get("id") == venue_id:
                return venue
        return None

    def calculate_total_cost(self, venue: dict, guest_count: int, package_name: str | None = None) -> dict:
        """
        Calculate total cost for a venue

        Returns:
            Dict with cost breakdown
        """
        tables_needed = (guest_count + 9) // 10

        pricing = venue.get("pricing", {})
        price_per_table = pricing.get("price_per_table", 0)

        # If specific package requested, find it
        if package_name:
            packages = venue.get("packages", [])
            for pkg in packages:
                if pkg.get("name") == package_name:
                    price_per_table = pkg.get("price_per_table", price_per_table)
                    break

        # Base cost
        base_cost = price_per_table * tables_needed

        # Check pricing type (nett vs plus_plus)
        pricing_type = pricing.get("pricing_type", "plus_plus")  # Default to plus_plus for safety

        if pricing_type == "nett":
            # Nett pricing: GST and service charge already included
            gst = 0
            service_charge = 0
            total_cost = base_cost
        else:
            # Plus-plus pricing: add GST and service charge on top
            gst = base_cost * config.GST_RATE
            service_charge = base_cost * config.SERVICE_CHARGE_RATE
            total_cost = base_cost + gst + service_charge

        return {
            "guest_count": guest_count,
            "tables_needed": tables_needed,
            "price_per_table": price_per_table,
            "pricing_type": pricing_type,
            "base_cost": round(base_cost, 2),
            "gst": round(gst, 2),
            "service_charge": round(service_charge, 2),
            "total_cost": round(total_cost, 2),
            "total_with_surcharges": round(total_cost, 2),
            "cost_per_guest": round(total_cost / guest_count, 2),
        }
