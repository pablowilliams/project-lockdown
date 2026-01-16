"""
Demand Forecasting for Project Lockdown
========================================

Uses exponential smoothing to predict weekly food demand for the LA1 area
during a 28-day lockdown scenario.

Author: Group E (MSCI391 Business Analytics)
Date: March 2025

The exponential smoothing formula:
    F(t+1) = α × D(t) + (1 - α) × F(t)
    
Where:
    - F(t+1) = forecast for next period
    - D(t) = actual demand in current period
    - F(t) = forecast for current period
    - α = smoothing constant (0 < α < 1)
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class PopulationSegment:
    """Represents a demographic segment with caloric requirements."""
    name: str
    population: int
    daily_calories: int  # kcal per person per day


# LA1 demographic data (based on 2021 Census)
LA1_POPULATION = 52000
LA1_HOUSEHOLDS = 25000

# Population breakdown by age group
POPULATION_SEGMENTS = [
    PopulationSegment("0-14", int(LA1_POPULATION * 0.18), 1500),
    PopulationSegment("15-64", int(LA1_POPULATION * 0.63), 2300),
    PopulationSegment("65+", int(LA1_POPULATION * 0.19), 1900),
]

# Average energy density of food (kcal per kg)
# Based on USDA data for mixed food baskets
ENERGY_DENSITY_KCAL_PER_KG = 3780


def calculate_daily_caloric_demand(segments: List[PopulationSegment]) -> int:
    """
    Calculate total daily caloric demand for all population segments.
    
    Args:
        segments: List of population segments with caloric requirements
        
    Returns:
        Total daily calories required (kcal)
    """
    return sum(seg.population * seg.daily_calories for seg in segments)


def calories_to_tonnes(calories: int, energy_density: int = ENERGY_DENSITY_KCAL_PER_KG) -> float:
    """
    Convert caloric requirement to food weight in tonnes.
    
    Args:
        calories: Total calories required
        energy_density: Average kcal per kg of food
        
    Returns:
        Food weight in tonnes
    """
    kg = calories / energy_density
    tonnes = kg / 1000
    return tonnes


def exponential_smoothing_forecast(
    actual_demand: float,
    previous_forecast: float,
    alpha: float = 0.3
) -> float:
    """
    Calculate next period's forecast using exponential smoothing.
    
    F(t+1) = α × D(t) + (1 - α) × F(t)
    
    Args:
        actual_demand: Observed demand in current period
        previous_forecast: Forecast made for current period
        alpha: Smoothing constant (higher = more weight on recent data)
        
    Returns:
        Forecast for next period
    """
    return alpha * actual_demand + (1 - alpha) * previous_forecast


def run_forecast_simulation(
    initial_forecast: float,
    actual_demands: List[float],
    alpha: float = 0.3
) -> List[Tuple[int, float, float, float]]:
    """
    Run exponential smoothing over multiple periods.
    
    Args:
        initial_forecast: Starting forecast value
        actual_demands: List of actual demand values for each period
        alpha: Smoothing constant
        
    Returns:
        List of tuples: (period, forecast, actual, error_pct)
    """
    results = []
    forecast = initial_forecast
    
    for period, actual in enumerate(actual_demands, 1):
        error_pct = abs(forecast - actual) / actual * 100
        results.append((period, forecast, actual, error_pct))
        forecast = exponential_smoothing_forecast(actual, forecast, alpha)
    
    return results


def calculate_macronutrient_requirements(
    segments: List[PopulationSegment],
    days: int = 28
) -> dict:
    """
    Calculate macronutrient requirements for the lockdown period.
    
    Based on standard dietary guidelines:
    - Protein: ~0.042 kg per person per day
    - Carbohydrates: ~0.333 kg per person per day
    - Fat: ~0.097 kg per person per day
    
    Args:
        segments: Population segments
        days: Number of days in lockdown
        
    Returns:
        Dict with total kg required for each macronutrient
    """
    # Daily requirements per person (kg) - varies by age group
    requirements = {
        "0-14": {"protein": 0.042, "carbs": 0.333, "fat": 0.097},
        "15-64": {"protein": 0.055, "carbs": 0.333, "fat": 0.097},
        "65+": {"protein": 0.053, "carbs": 0.310, "fat": 0.091},
    }
    
    totals = {"protein": 0, "carbs": 0, "fat": 0}
    
    for segment in segments:
        reqs = requirements.get(segment.name, requirements["15-64"])
        for nutrient, daily_kg in reqs.items():
            totals[nutrient] += segment.population * daily_kg * days
    
    return totals


def main():
    """
    Main execution: calculate demand forecasts for Project Lockdown.
    """
    print("=" * 60)
    print("PROJECT LOCKDOWN - DEMAND FORECASTING")
    print("=" * 60)
    
    # Calculate baseline daily demand
    daily_calories = calculate_daily_caloric_demand(POPULATION_SEGMENTS)
    daily_tonnes = calories_to_tonnes(daily_calories)
    weekly_tonnes = daily_tonnes * 7
    
    print(f"\n📊 BASELINE CALCULATIONS")
    print(f"   Total population: {LA1_POPULATION:,}")
    print(f"   Total households: {LA1_HOUSEHOLDS:,}")
    print(f"   Daily caloric demand: {daily_calories:,} kcal")
    print(f"   Daily food requirement: {daily_tonnes:.2f} tonnes")
    print(f"   Weekly food requirement: {weekly_tonnes:.2f} tonnes")
    print(f"   28-day food requirement: {daily_tonnes * 28:.2f} tonnes")
    
    # Simulate demand with some variation
    print(f"\n📈 EXPONENTIAL SMOOTHING SIMULATION (α = 0.3)")
    print("-" * 60)
    
    # Simulated actual demands (with some random variation)
    actual_demands = [
        weekly_tonnes * 1.02,  # Week 1: 2% over baseline (initial rush)
        weekly_tonnes * 1.05,  # Week 2: 5% over (stockpiling)
        weekly_tonnes * 0.98,  # Week 3: settling down
        weekly_tonnes * 1.00,  # Week 4: back to normal
    ]
    
    results = run_forecast_simulation(weekly_tonnes, actual_demands, alpha=0.3)
    
    print(f"{'Week':<8} {'Forecast':<15} {'Actual':<15} {'Error %':<10}")
    print("-" * 48)
    
    for week, forecast, actual, error in results:
        print(f"{week:<8} {forecast:>12.2f} t  {actual:>12.2f} t  {error:>7.2f}%")
    
    avg_error = sum(r[3] for r in results) / len(results)
    print("-" * 48)
    print(f"Average forecast error: {avg_error:.2f}%")
    
    # Macronutrient breakdown
    print(f"\n🥗 MACRONUTRIENT REQUIREMENTS (28 days)")
    print("-" * 60)
    
    macros = calculate_macronutrient_requirements(POPULATION_SEGMENTS, days=28)
    
    for nutrient, kg in macros.items():
        print(f"   {nutrient.capitalize():<15}: {kg:>12,.2f} kg")
    
    print(f"\n   Total macronutrients: {sum(macros.values()):>12,.2f} kg")
    
    # Cost estimation (simplified)
    print(f"\n💷 ESTIMATED FOOD COSTS")
    print("-" * 60)
    
    cost_per_kg = {
        "protein": 11.86,
        "carbs": 3.37,
        "fat": 10.00,
    }
    
    total_cost = 0
    for nutrient, kg in macros.items():
        cost = kg * cost_per_kg[nutrient]
        total_cost += cost
        print(f"   {nutrient.capitalize():<15}: £{cost:>12,.2f}")
    
    # Add fruits & veg estimate
    fruits_veg_kg = LA1_POPULATION * 23.81 * 0.28  # ~28 days of fruit consumption
    fruits_veg_cost = fruits_veg_kg * 1.58
    total_cost += fruits_veg_cost
    print(f"   {'Fruits & Veg':<15}: £{fruits_veg_cost:>12,.2f}")
    
    print("-" * 48)
    print(f"   {'TOTAL':<15}: £{total_cost:>12,.2f}")
    
    print("\n" + "=" * 60)
    print("Forecast complete. Data ready for warehouse allocation.")
    print("=" * 60)


if __name__ == "__main__":
    main()
