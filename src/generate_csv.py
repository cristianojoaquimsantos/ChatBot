import csv
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

def generate_data():
    invoid_id = fake.uuid4()[:8]
    branch = random.choice(["A", "B", "C"])
    city = random.choice(["City A", "City B", "City C"])
    customer_type = random.choice(["Member", "Normal"])
    gender = random.choice(["Male", "Female"])
    product_line = random.choice([
        "Electronic", 
        "Fashion", 
        "Home", 
        "Beauty", 
        "Sports"])
    unit_price = round(random.uniform(10.0, 500.0), 2)
    quantity = random.randint(1, 10)
    tax = round((unit_price * quantity) * 0.05, 2)
    total = round(unit_price * quantity + tax, 2)
    date = fake.date_between(start_date='-1y', end_date='today').strftime('%Y-%m-%d')
    time = fake.time(pattern="%H:%M:%S")
    payment = random.choice(["Cash", "Credit Card", "E-wallet"])
    cogs = round(unit_price * quantity, 2)
    gross_margin_percentagem = 4.76
    gross_income = tax
    rating = round(random.uniform(4, 10), 1)

    return [
        invoid_id,
        branch,
        city,
        customer_type,
        gender,
        product_line,
        unit_price,
        quantity,
        tax,
        total,
        date,
        time,
        payment,
        cogs,
        gross_margin_percentagem,
        gross_income,
        rating
    ]

headers = [
    "Invoice ID",
    "Branch",
    "City",
    "Customer Type",
    "Gender",
    "Product Line",
    "Unit price",
    "Quantity",
    "Tax 5%",
    "Total",
    "Date",
    "Time",
    "Payment",
    "COGS",
    "Gross margin percentage",
    "Gross income",
    "Rating"
]

with open('sales_data.csv', mode='w', newline='', encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(headers)
    
    for _ in range(1000):  # Generate 1000 rows of data
        writer.writerow(generate_data())
    
print("O Aquivo 'sales_data.csv' gerado com sucesso.") 