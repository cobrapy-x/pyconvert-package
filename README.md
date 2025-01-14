# **PyConvert**

PyConvert is a simple and powerful Python module for performing various unit conversions and number system conversions. It supports conversions for length, weight, speed, area, energy, power, volume, and number systems (base conversions). PyConvert is designed to be easy to use, requiring no complex setup or class instantiation.

---

## **Features**
- **Unit Conversion**:
  - Length: Convert between meters, kilometers, feet, inches, lightyears, etc.
  - Weight: Convert grams, kilograms, pounds, solar masses, etc.
  - Speed: Convert meters/second, kilometers/hour, miles/hour, and more.
  - Area: Convert square meters, hectares, acres, and more.
  - Energy: Convert joules, calories, kilowatt-hours, etc.
  - Power: Convert watts, horsepower, kilowatts, and more.
  - Volume: Convert liters, milliliters, gallons, cubic feet, etc.
  
- **Number System Conversion**:
  - Convert decimal numbers into any base (e.g., binary, octal, hexadecimal, or custom bases).

---

## **Installation**
To install PyConvert, use pip :
```bash
pip install pyconvert

## **Usage**
- **Importing the Module**:
  -You can use PyConvert directly after importing it:
    import pyconvert
- **Unit Convertion**:
   -You can convert units using the format :
      pyconvert.convert(<quantity>,<convertion instruction>,<value>)
   -Examples:
      -1.Convert 500 grams to kilograms:
         result = pyconvert.convert('weight', 'gram-->kilogram', 500)
         print(result)  # Output: 0.5
      -2.Convert 60 miles per hour to kilometers per hour:
         result = pyconvert.convert('speed', 'miles_per_hour-->kilometers_per_hour', 60)
         print(result)  # Output: 96.56064
      -3.Convert 3 liters to gallons:
         result = pyconvert.convert('volume', 'liter-->gallon', 3)
         print(result)  # Output: 0.792516
- **Number System Conversion**:
    -You can convert numbers using the format:
       pyconvert.convertnumber(<base>,<decimal number>)
    -Example:
      -1.Convert 100 to base 3:
         result = pyconvert.convertnumber(3, 100)
         print(result)  # Output: 10201

## **Supported Units**
     1. Length
	•	meter, kilometer, centimeter, millimeter, feet, inches, lightyear

     2. Weight
	•	gram, kilogram, milligram, pound, solar mass

     3. Speed
	•	meters/second, kilometers/hour, miles/hour, speed of light

     4. Area
	•	square meter, square kilometer, square centimeter, acre, hectare

     5. Energy
	•	joule, kilojoule, calorie, kilocalorie, watt-hour, kilowatt-hour

     6. Power
	•	watt, kilowatt, megawatt, horsepower, milliwatt

     7. Volume
	•	liter, milliliter, cubic meter, gallon, cup, cubic feet  

## **Contributing**
     We welcome all contributions! To contribute:
	 1.	Fork the repository.
	 2.	Create a new branch for your feature or bugfix.
	 3.	Make your changes and commit them.
	 4.	Open a pull request with a clear description of your changes. 

## **License**
    PyConvert is licensed under the MIT License. See the LICENSE file for more details.          