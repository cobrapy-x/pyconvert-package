# pyconvert.py

# Conversion factors (now as a global dictionary)
convertion_factors = {
    'length': {
        'meter-->kilometer': 0.001,
        'kilometer-->meter': 1000,
        'centimeter-->meter': 0.01,
        'meter-->centimeter': 100,
        'millimeter-->centimeter': 0.1,
        'centimeter-->millimeter': 10,
        'lightyear-->kilometer': 9.461 * (10 ** 12),
        'feet-->inches': 12,
        'inches-->feet': 1 / 12,
        'meter-->feet': 0.3048,
        'feet-->meter': 1 / 0.3048,
    },
    'weight': {
        'gram-->kilogram': 0.001,
        'kilogram-->gram': 1000,
        'milligram-->gram': 0.001,
        'gram-->milligram': 1000,
        'solarmass-->kilogram': 1.989 * (10 ** 30),
        'quintal-->kilogram': 1000,
        'kilogram-->quintal': 0.001,
        'pound-->kilogram': 0.453592,
        'amu-->gram': 1.66054 * (10 ** (-24)),
        'kilogram-->pound': 2.20462,
    },
    'speed': {
        'meters_per_second-->kilometers_per_hour': 3.6,
        'kilometers_per_hour-->meters_per_second': 1 / 3.6,
        'miles_per_hour-->kilometers_per_hour': 1.60934,
        'kilometers_per_hour-->miles_per_hour': 1 / 1.60934,
        'speed_of_light-->meters_per_second': 299_792_458,
    },
    'area': {
        'square_meter-->square_kilometer': 0.000001,
        'square_kilometer-->square_meter': 1_000_000,
        'square_meter-->square_centimeter': 10_000,
        'square_centimeter-->square_meter': 0.0001,
        'square_meter-->square_feet': 10.7639,
        'square_feet-->square_meter': 1 / 10.7639,
        'acre-->square_meter': 4046.86,
        'square_meter-->acre': 1 / 4046.86,
        'hectare-->square_meter': 10000,
        'square_meter-->hectare': 0.0001,
    },
    'energy': {
        'joule-->kilojoule': 0.001,
        'kilojoule-->joule': 1000,
        'joule-->calorie': 1 / 4.184,
        'calorie-->joule': 4.184,
        'calorie-->kilocalorie': 0.001,
        'kilocalorie-->calorie': 1000,
        'joule-->watt_hour': 1 / 3600,
        'watt_hour-->joule': 3600,
        'kilowatt_hour-->joule': 3.6e6,
        'joule-->kilowatt_hour': 1 / 3.6e6,
    },
    'power': {
        'watt-->kilowatt': 0.001,
        'kilowatt-->watt': 1000,
        'horsepower-->watt': 745.7,
        'watt-->horsepower': 1 / 745.7,
        'kilowatt-->megawatt': 0.001,
        'megawatt-->kilowatt': 1000,
        'watt-->milliwatt': 1000,
        'milliwatt-->watt': 0.001,
        'watt-->btu_per_hour': 3.41214,
        'btu_per_hour-->watt': 1 / 3.41214,
    },
    'volume': {
        'liter-->milliliter': 1000,
        'milliliter-->liter': 0.001,
        'liter-->cubic_meter': 0.001,
        'cubic_meter-->liter': 1000,
        'liter-->gallon': 0.264172,
        'gallon-->liter': 1 / 0.264172,
        'cubic_feet-->liter': 28.3168,
        'liter-->cubic_feet': 1 / 28.3168,
        'cup-->liter': 0.236588,
        'liter-->cup': 1 / 0.236588,
    },
}

# Function to perform unit conversion
def convert(qty, units, value):
    # Check if category exists
    if qty not in convertion_factors:
        raise ValueError(f"Category '{qty}' is not supported.")
    
    # Check if the unit conversion is available
    if units not in convertion_factors[qty]:
        raise ValueError(f"Conversion '{units}' not supported in category '{qty}'.")
    
    # Get the conversion factor and return the result
    factor = convertion_factors[qty][units]
    return value * factor

# Function to convert a number to different bases
def convertnumber(base, number):
    if base < 2 or base > 36:
        raise ValueError("Base must be between 2 and 36.")

    integer_part = int(number)
    fractional_part = number - integer_part

    integer_result = ""
    while integer_part > 0:
        remainder = integer_part % base
        integer_result = _digit_to_char(remainder) + integer_result
        integer_part //= base
    integer_result = integer_result or "0"

    fractional_result = ""
    count = 0
    while fractional_part > 0 and count < 10:
        fractional_part *= base
        digit = int(fractional_part)
        fractional_result += _digit_to_char(digit)
        fractional_part -= digit
        count += 1

    if fractional_result:
        return f"{integer_result}.{fractional_result}"
    else:
        return integer_result

# Helper function to convert digits to characters for bases above 10
def _digit_to_char(digit):
    if digit < 10:
        return str(digit)
    else:
        return chr(ord('A') + digit - 10)
