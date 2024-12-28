import calendar
from datetime import datetime


class ValidatedList(list):
    #  def __init__(self, elements): 
    #     self._elements = []
    #     for element in elements: 
    #         if not (1 <= element <= 31):
    #             raise ValueError(f"Element {element} is out of range (1-31)")
    #         self._elements.append(element)
     def __init__(self, elements, min_value=1, max_value=31):
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(self._validate(elements))

     def _validate(self, elements):
        for element in elements:
            if not (self.min_value <= element <= self.max_value):
                raise ValueError(f"Element {element} is out of range ({self.min_value}-{self.max_value})")
        return elements

     def append(self, element):
        if not (self.min_value <= element <= self.max_value):
            raise ValueError(f"Element {element} is out of range ({self.min_value}-{self.max_value})")
        super().append(element)

     def extend(self, elements):
        super().extend(self._validate(elements))
try:
    valid_list = ValidatedList([10, 20, 30])  # Raises ValueError
except ValueError as e:
    print(e)

#valid_list = ValidatedList([10, 20, 30])  # Valid list

# Define the total number of days in the current month
current_year = datetime.now().year
current_month = datetime.now().month

# Get the number of days in the current month
days_in_current_month = calendar.monthrange(current_year, current_month)[1]
current_month_name = calendar.month_name[current_month]

# Define the amount of milk purchased each day
cow_milk_per_day = 1
buffalo_milk_per_day = 1

# Define the rates for cow and buffalo milk
cow_milk_rate = 44
buffalo_milk_rate = 58

# Define the days when no milk was purchased
no_milk_days = ValidatedList([1, 9, 17])

# Define the days when extra buffalo milk was purchased , which mean on these days no cow milk taken
extra_buffalo_milk_days = [(4, 2)]  # (day, liters)
# Define the days when extra cow milk was purchased, which mean on these days no buffalo milk taken
extra_cow_milk_days = [(5,3)]  # (day, liters)

#Defin the days when cow milk was not purchased
no_cow_milk_days = ValidatedList([7 , 4 ,15])

#Defin the days when buffalo milk was not purchased
no_buffalo_milk_days = ValidatedList([18])

# Calculate the total number of days when milk was purchased
total_milk_days = days_in_current_month - len(no_milk_days)

# Calculate the total number of days when cow milk was purchased
cow_milk_days = total_milk_days - len(no_cow_milk_days) #- len(extra_buffalo_milk_days)   # Subtract 1 for the day when only cow milk was off

# Calculate the total number of days when buffalo milk was purchased
buffalo_milk_days = total_milk_days - len(no_buffalo_milk_days) #- len(extra_cow_milk_days)  # Subtract 1 for the day when only buffalo milk was off

# Calculate the total cost of cow milk
cow_milk_cost = cow_milk_days * cow_milk_per_day * cow_milk_rate
for day, liters in extra_cow_milk_days:
    cow_milk_cost += (liters-cow_milk_per_day) * cow_milk_rate

# Calculate the total cost of buffalo milk
buffalo_milk_cost = buffalo_milk_days * buffalo_milk_per_day * buffalo_milk_rate
for day, liters in extra_buffalo_milk_days:
    buffalo_milk_cost += (liters-buffalo_milk_per_day) * buffalo_milk_rate

# Calculate the total cost of milk
total_milk_cost = cow_milk_cost + buffalo_milk_cost

# Print the total cost of milk
print(f"The total cost of milk in {current_month_name} is : {total_milk_cost}")