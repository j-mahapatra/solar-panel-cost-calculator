import json
import math

with open('./data/dataset_solar_calculator.json', 'r') as file:
    state_wise_data = json.load(file)

with open('./data/price_chart.json', 'r') as file:
    price_chart = json.load(file)

with open('./data/panel_constants.json', 'r') as file:
    panel_constants = json.load(file)

with open('./data/setup_cost_constants.json', 'r') as file:
    setup_cost_constants = json.load(file)

def get_field_from_json (field_to_match, value_to_match, return_field):
    for entry in state_wise_data:
        if entry[field_to_match] == value_to_match:
            return entry[return_field]
    return None

def calculate_unit_used (total_bill, pincode):
    state = get_field_from_json("Pincode", pincode, "StateoRuT")
   
    if state is None:
        return
    
    total_bill = total_bill * 0.97
    prices = price_chart[state]
    i = 0
    total_units = 0

    while (total_bill > 0): 
        remaining = total_bill - (prices[i] * 50)
        if (remaining < 0):
            total_units += (total_bill / prices[i])
            break
        else:
            total_bill -= (prices[i] * 50)
            total_units += 50
            if (i != len(prices) - 1):
                i += 1

    return total_units

def daily_consumption (total_units_consumed):
    return total_units_consumed / 30

def temperature_factor (type, pincode):
    temp = get_field_from_json("Pincode", pincode, "Avg Tmp")
    temp_coeff = panel_constants["temperature_coefficient"][type]
    return 1 + (temp_coeff * (temp - 25))

def shading_factor (pincode):
    return get_field_from_json("Pincode", pincode, "Shading Factor")

def soiling_factor (pincode):
    return get_field_from_json("Pincode", pincode, "Soiling Factor")

def average_irradiance (pincode):
    return get_field_from_json("Pincode", pincode, "Average Irradiance")

def derating_factor (type, pincode):
    return temperature_factor(type, pincode) * shading_factor(pincode) * soiling_factor(pincode) * panel_constants["inverter_efficiency"][type] * panel_constants["installation_quality_factor"][type]

def theoretical_daily_energy (type, pincode):
    return panel_constants["panel_efficiency"][type] * panel_constants["panel_area_m2"][type] * average_irradiance(pincode)

def adjusted_daily_energy (type, pincode):
    return theoretical_daily_energy(type, pincode) * derating_factor(type, pincode)

def number_of_solar_panels (type, pincode, total_units_consumed):
    res = daily_consumption(total_units_consumed) / adjusted_daily_energy(type, pincode)
    return math.ceil(res)

def total_energy_produced_daily (type, pincode, total_units_consumed):
    return number_of_solar_panels(type, pincode, total_units_consumed) * adjusted_daily_energy(type, pincode)

def total_kwh_setup (type, pincode, total_units_consumed):
    return number_of_solar_panels(type, pincode, total_units_consumed) * panel_constants["panel_wp"][type]

def co2_cut_in_tons (type, total_units_consumed):
    return (panel_constants["co2_emission_factor"][type] * daily_consumption(total_units_consumed) * 365) / 1000

def area_needed_in_sqft (type, pincode, total_units_consumed):
    return  number_of_solar_panels(type, pincode, total_units_consumed) * panel_constants["panel_area"][type]

def savings_on_electricity_per_year (total_bill):
    return 12 * total_bill

def generate_power_kwh_per_year (type, pincode, total_units_consumed):
    return number_of_solar_panels(type, pincode, total_units_consumed) * adjusted_daily_energy(type, pincode) * 365

def cost_of_panels (type, pincode, total_units_consumed):
    return number_of_solar_panels (type, pincode, total_units_consumed) * panel_constants["single_panel_costs"][type]

def setup_cost (type, pincode, total_units_consumed, field):
    return total_kwh_setup (type, pincode, total_units_consumed) * setup_cost_constants[field]

def total_setup_cost (type, pincode, total_units_consumed):
    total = 0

    total += cost_of_panels(type, pincode, total_units_consumed)

    total += setup_cost_constants["net_meter"]

    fields = ["inverter", 
        "mounting",
        "dc_db",
        "ac_db",
        "dc_cable",
        "ac_cable",
        "earthing_kit",
        "lightning_arrester",
        "connectors",
        "cable_ties",
        "installation_accessories",
        "labour_and_installation"
    ]

    for field in fields:
        total += setup_cost(type, pincode, total_units_consumed, field)
    
    return total

def gst (type, pincode, total_units_consumed):
    total = total_setup_cost(type, pincode, total_units_consumed)
    return (0.7 * total * 0.12) + (0.3 * total * 0.18)
    
def government_subsidy (type, pincode, total_units_consumed):
    if (type == "without_subsidy"):
        return 0
    
    total_kwh_setup_amount = total_kwh_setup(type, pincode, total_units_consumed)

    if ((total_kwh_setup_amount / 1000) >= 3):
        return 78000
    
    if ((total_kwh_setup_amount / 1000) > 2):
        return 60000 + (((total_kwh_setup_amount / 1000) - 2) * 18000)
    
    if ((total_kwh_setup_amount / 1000) == 2):
        return 60000
    
    if ((total_kwh_setup_amount / 1000) < 2):
        return (total_kwh_setup_amount / 1000) * 30000
    
def total_overall_cost (type, pincode, total_units_consumed):
    return total_setup_cost(type, pincode, total_units_consumed) + gst(type, pincode, total_units_consumed) - government_subsidy(type, pincode, total_units_consumed)

monthly_bill = int(input("Enter your Average Monthly Bill: "))
pincode = int(input("Enter your Pincode: "))
subsidy = input("Do you want subsidy? Y/N: ")

subsidy_type = "with_subsidy" if (subsidy == "Y" or subsidy == "y") else "without_subsidy"
total_units_used = calculate_unit_used(monthly_bill, pincode)

print("\n")

print("No. of Solar Panels: {}".format(number_of_solar_panels(subsidy_type, pincode, total_units_used)))
print("Area needed in Sqft: {}".format(area_needed_in_sqft(subsidy_type, pincode, total_units_used)))
print("Savings on electricity per year: {}".format(savings_on_electricity_per_year(monthly_bill)))
print("Generate Power KwH/Year: {}".format(generate_power_kwh_per_year(subsidy_type, pincode, total_units_used)))
print("Recovery in no. of Years: {}".format(total_overall_cost(subsidy_type, pincode, total_units_used) / savings_on_electricity_per_year(monthly_bill)))
print("Total Energy Produced Daily: {}".format(total_energy_produced_daily(subsidy_type, pincode, total_units_used)))
print("Total kWh Setup: {}".format((total_kwh_setup(subsidy_type, pincode, total_units_used) / 1000)))
print("Tons of CO2 Cut: {}".format(co2_cut_in_tons(subsidy_type, total_units_used)))
print("\n\n")

print("Solar Panels: {}".format(cost_of_panels(subsidy_type, pincode, total_units_used)))
print("Solar Inverter: {}".format(setup_cost(subsidy_type, pincode, total_units_used, "inverter")))
print("Mounting Structure: {}".format(setup_cost(subsidy_type, pincode, total_units_used, "mounting")))
print("AC & DC Distribution Box: {}".format(setup_cost(subsidy_type, pincode, total_units_used, "dc_db") + setup_cost(subsidy_type, pincode, total_units_used, "ac_db")))
print("AC & DC Cables: {}".format(setup_cost(subsidy_type, pincode, total_units_used, "dc_cable") + setup_cost(subsidy_type, pincode, total_units_used, "ac_cable")))
print("Earthing Kit: {}".format(setup_cost(subsidy_type, pincode, total_units_used, "earthing_kit")))
print("Lightning Arrestor: {}".format(setup_cost(subsidy_type, pincode, total_units_used, "lightning_arrester")))
print("Net Meter (as per DISCOM): {}".format(setup_cost_constants["net_meter"]))
print("All Other Installation Accessories: {}".format(setup_cost(subsidy_type, pincode, total_units_used, "connectors") + setup_cost(subsidy_type, pincode, total_units_used, "cable_ties") + setup_cost(subsidy_type, pincode, total_units_used, "installation_accessories")))
print("Labor & Installation Charges: {}".format(setup_cost(subsidy_type, pincode, total_units_used, "labour_and_installation")))
print("GST Charges: {}".format(gst(subsidy_type, pincode, total_units_used)))
print("Government Subsidy: {}".format(government_subsidy(subsidy_type, pincode, total_units_used)))
print("Total Cost: {}".format(total_overall_cost(subsidy_type, pincode, total_units_used)))
