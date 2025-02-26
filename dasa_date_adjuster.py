from datetime import datetime
from dateutil.relativedelta import relativedelta

# Define the full mahadasha periods (in years) for each dasa.
dasha_periods = {
    "sun": 6,
    "moon": 10,
    "mars": 7,
    "rahu": 18,
    "jupiter": 16,
    "saturn": 19,
    "mercury": 17,
    "ketu": 7,
    "venus": 20
}

def adjust_dasa_start_date(present_date, pada, current_dasa):
    """
    Calculate the updated dasa start date based on the given date, current dasa, and pada.
    
    Formula:
      new_dasa_start_date = given_date - ((pada - 1) / 4 * full dasa period in years)
    
    Parameters:
      present_date (datetime): The given date.
      pada (int or str): The pada number (1, 2, 3, or 4).
      current_dasa (str): The dasa name (e.g., "Venus", "Moon").
    
    Returns:
      datetime: The updated starting date.
    """
    current_dasa_lower = current_dasa.lower()
    if current_dasa_lower not in dasha_periods:
        raise ValueError(f"Invalid dasa provided: {current_dasa}")
    
    period = dasha_periods[current_dasa_lower]
    fraction_elapsed = (int(pada) - 1) / 4.0  # e.g., 0 for pada 1, 0.25 for pada 2, etc.
    offset_years = period * fraction_elapsed
    
    years_offset = int(offset_years)
    months_offset = int(round((offset_years - years_offset) * 12))
    
    updated_start_date = present_date - relativedelta(years=years_offset, months=months_offset)
    return updated_start_date

if __name__ == '__main__':
    date_str = input("Enter the given date (YYYY-MM-DD): ")
    current_dasa = input("Enter the current dasa (e.g., Venus, Moon): ")
    pada = input("Enter the pada (1-4): ")
    
    try:
        given_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        exit(1)
    
    try:
        new_date = adjust_dasa_start_date(given_date, pada, current_dasa)
        print("Updated dasa starting date:", new_date.strftime("%d-%m-%Y"))
    except Exception as e:
        print("Error:", e)
