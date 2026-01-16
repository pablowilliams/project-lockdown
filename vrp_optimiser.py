"""
Vehicle Routing Problem (VRP) Optimiser for Project Lockdown
============================================================

This script assigns delivery postcodes to the nearest warehouse and 
optimises delivery routes for a fleet of trucks during the LA1 lockdown.

Author: Group E (MSCI391 Business Analytics)
Date: March 2025

Requirements:
    - requests
    - Google Maps API key

Usage:
    python vrp_optimiser.py
"""

import os
import requests
import logging
from collections import defaultdict
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your own API key or set as environment variable
API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "YOUR_API_KEY_HERE")


class RouteOptimiser:
    """
    Handles distance calculations and route optimisation using Google Maps API.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_distance(self, origin: str, destination: str) -> Optional[int]:
        """
        Get driving distance between two locations in meters.
        
        Args:
            origin: Starting location (postcode or address)
            destination: End location (postcode or address)
            
        Returns:
            Distance in meters, or None if request fails
        """
        url = (
            f"https://maps.googleapis.com/maps/api/distancematrix/json"
            f"?origins={origin}&destinations={destination}&mode=driving&key={self.api_key}"
        )
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "OK" and data["rows"]:
                element = data["rows"][0]["elements"][0]
                if element["status"] == "OK" and "distance" in element:
                    return element["distance"]["value"]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving distance from {origin} to {destination}: {e}")
        
        return None

    def get_optimised_route(self, waypoints: List[str]) -> List[Dict[str, str]]:
        """
        Get optimised route through multiple waypoints.
        
        Args:
            waypoints: List of locations to visit (first and last are start/end)
            
        Returns:
            List of route legs with addresses and distances
        """
        if not waypoints:
            return []

        origin = waypoints[0]
        destination = waypoints[-1]
        stops = waypoints[1:-1]
        waypoints_str = "|".join(stops)
        
        url = (
            f"https://maps.googleapis.com/maps/api/directions/json?"
            f"origin={origin}&destination={destination}&waypoints=optimize:true|{waypoints_str}&key={self.api_key}"
        )

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "OK":
                route_info = []
                for leg in data["routes"][0]["legs"]:
                    route_info.append({
                        "end_address": leg["end_address"],
                        "distance": leg["distance"]["value"]
                    })
                return route_info
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving optimised route: {e}")
        
        return []

    def calculate_warehouse_distances(
        self, 
        warehouses: List[str], 
        postcodes: List[str]
    ) -> Dict[str, Dict[str, int]]:
        """
        Calculate distances from each warehouse to each postcode.
        
        Args:
            warehouses: List of warehouse postcodes
            postcodes: List of delivery postcodes
            
        Returns:
            Nested dict: warehouse -> postcode -> distance
        """
        warehouse_distances = {warehouse: {} for warehouse in warehouses}

        for warehouse in warehouses:
            for postcode in postcodes:
                distance = self.get_distance(warehouse, postcode)
                if distance is not None:
                    warehouse_distances[warehouse][postcode] = distance

        return warehouse_distances

    def assign_postcodes_to_warehouses(
        self, 
        warehouses: List[str], 
        postcodes: List[str]
    ) -> Dict[str, List[str]]:
        """
        Assign each postcode to its nearest warehouse.
        
        Args:
            warehouses: List of warehouse postcodes
            postcodes: List of delivery postcodes
            
        Returns:
            Dict mapping warehouse -> list of assigned postcodes
        """
        warehouse_distances = self.calculate_warehouse_distances(warehouses, postcodes)
        warehouse_assignments = {warehouse: [] for warehouse in warehouses}

        for postcode in postcodes:
            min_distance = float('inf')
            nearest_warehouse = None

            for warehouse in warehouses:
                if postcode in warehouse_distances[warehouse]:
                    distance = warehouse_distances[warehouse][postcode]
                    if distance < min_distance:
                        min_distance = distance
                        nearest_warehouse = warehouse

            if nearest_warehouse:
                warehouse_assignments[nearest_warehouse].append(postcode)
            else:
                # Fallback: assign to first warehouse if no valid distance found
                warehouse_assignments[warehouses[0]].append(postcode)

        return warehouse_assignments

    def optimise_routes_for_trucks(
        self, 
        trucks: Dict[int, List[str]], 
        warehouse: str
    ) -> Dict[int, Dict[str, any]]:
        """
        Optimise routes for each truck assigned to a warehouse.
        
        Args:
            trucks: Dict mapping truck_id -> list of postcodes
            warehouse: Warehouse postcode (start and end point)
            
        Returns:
            Dict with route info and total distance for each truck
        """
        truck_routes = {}
        
        for truck_id, stops in trucks.items():
            if not stops:
                continue
                
            route_info = self.get_optimised_route([warehouse] + stops + [warehouse])
            total_distance = sum([leg["distance"] for leg in route_info]) if route_info else 0
            
            truck_routes[truck_id] = {
                "route": [leg["end_address"] for leg in route_info],
                "total_distance": total_distance / 1000  # Convert to kilometers
            }
            
        return truck_routes


def divide_postcodes_among_trucks(
    postcodes: List[str], 
    num_trucks: int
) -> Dict[int, List[str]]:
    """
    Evenly distribute postcodes among available trucks.
    
    Args:
        postcodes: List of postcodes to distribute
        num_trucks: Number of trucks available
        
    Returns:
        Dict mapping truck_id -> list of assigned postcodes
    """
    trucks = defaultdict(list)
    for i, pc in enumerate(postcodes):
        trucks[i % num_trucks].append(pc)
    return trucks


def main():
    """
    Main execution: assign postcodes to warehouses and optimise delivery routes.
    """
    # Warehouse locations (LA1 postcodes)
    warehouses = ["LA1 1UJ", "LA1 1HH"]  # Aldi, Sainsbury's
    warehouse_alias = {"LA1 1HH": "Sainsbury", "LA1 1UJ": "Aldi"}

    # Sample postcodes for demonstration (expand for full implementation)
    postcodes = [
        "LA1 5NS", "LA1 5NT", "LA1 5NU", "LA1 5NX", "LA1 5NY", "LA1 5NZ",
        "LA1 4JA", "LA1 4JB", "LA1 4JD", "LA1 4JE", "LA1 4JF", "LA1 4JG",
        "LA1 3HG", "LA1 3HJ", "LA1 3HL", "LA1 3HP", "LA1 3HQ", "LA1 3HR",
        "LA1 2QR", "LA1 2QS", "LA1 2QT", "LA1 2QU", "LA1 2QW", "LA1 2QX",
        "LA1 1PN", "LA1 1PP", "LA1 1PQ", "LA1 1PR", "LA1 1PS", "LA1 1PT"
    ]

    # Total fleet size
    total_trucks = 30

    # Initialise optimiser
    optimiser = RouteOptimiser(API_KEY)

    # Step 1: Assign postcodes to nearest warehouse
    print("Assigning postcodes to warehouses...")
    warehouse_assignments = optimiser.assign_postcodes_to_warehouses(warehouses, postcodes)

    # Step 2: Calculate truck allocation per warehouse
    total_postcodes = len(postcodes)
    trucks_per_warehouse = {}

    for warehouse in warehouses:
        assigned_postcodes = len(warehouse_assignments[warehouse])
        proportion = assigned_postcodes / total_postcodes
        trucks_per_warehouse[warehouse] = max(1, round(proportion * total_trucks))

    # Adjust to ensure exactly 30 trucks total
    trucks_diff = total_trucks - sum(trucks_per_warehouse.values())
    if trucks_diff != 0:
        larger_warehouse = max(warehouses, key=lambda w: len(warehouse_assignments[w]))
        trucks_per_warehouse[larger_warehouse] += trucks_diff

    # Step 3: Optimise routes for each warehouse
    grand_total_distance = 0
    global_truck_id = 0

    for warehouse in warehouses:
        warehouse_label = warehouse_alias.get(warehouse, warehouse)
        assigned_postcodes = warehouse_assignments[warehouse]
        num_trucks = trucks_per_warehouse[warehouse]

        if not assigned_postcodes:
            continue

        # Divide postcodes among trucks
        trucks = divide_postcodes_among_trucks(assigned_postcodes, num_trucks)

        # Optimise routes
        truck_routes = optimiser.optimise_routes_for_trucks(trucks, warehouse)

        # Print results
        print("\n" + "=" * 60)
        print(f"Warehouse: {warehouse_label} (Assigned {num_trucks} trucks)")
        print("=" * 60)

        warehouse_total_distance = 0

        for local_truck_id, data in truck_routes.items():
            actual_truck_id = global_truck_id + 1
            global_truck_id += 1

            distance = data['total_distance']
            warehouse_total_distance += distance
            grand_total_distance += distance

            print(f"\nTruck {actual_truck_id} Route (Total Distance: {distance:.2f} km):")
            for stop in data['route']:
                print(f"    → {stop}")
            print("-" * 50)

        print(f"\nTotal distance for {warehouse_label}: {warehouse_total_distance:.2f} km")

    print("\n" + "=" * 60)
    print(f"GRAND TOTAL DISTANCE: {grand_total_distance:.2f} km")
    print("=" * 60)


if __name__ == "__main__":
    main()
