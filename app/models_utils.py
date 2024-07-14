""" Models utils """

from django.core.mail import send_mail, get_connection
from django.template.loader import render_to_string

def find_position(nums):
    """ Automatic position calculation """

    nums.sort()

    # Wenn die Liste leer ist, geben Sie 1 zurück
    if not nums:
        return 1

    # Überprüfen Sie, ob eine Zahl zwischen den vorhandenen Zahlen fehlt
    for i in range(1, len(nums)):
        if nums[i] - nums[i - 1] > 1:
            return nums[i - 1] + 1

    # Wenn keine Zahl fehlt, geben Sie die nächste Zahl nach der letzten Zahl in der Liste zurück
    return nums[-1] + 1

def calculate_fixed_supplement(amount, tiers):
    """ Calculate price per amount """

    # Tiers represented as a list of tuples: (Max weight, Price per gram)
    total_price = 0
    amount_calculated = 0

    for limit, price_per_gram in tiers:
        if amount <= limit:
            total_price += (amount - amount_calculated) * price_per_gram
            break
        else:
            total_price += (limit - amount_calculated) * price_per_gram
            amount_calculated = limit

    return round(total_price, 2) 
