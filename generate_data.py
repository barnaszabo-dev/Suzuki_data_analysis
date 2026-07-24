import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

# Suzuki (Maruti Suzuki, global Suzuki) model lineup with segment info
models_info = [
    ("Swift",            "Hatchback",      6.5, 1.0),
    ("Baleno",           "Premium Hatchback", 7.2, 0.85),
    ("Celerio",          "Hatchback",      5.8, 0.55),
    ("WagonR",           "Hatchback",      5.9, 0.9),
    ("Alto K10",         "Hatchback",      4.5, 0.8),
    ("S-Presso",         "Hatchback",      4.8, 0.45),
    ("Ignis",            "Hatchback",      5.9, 0.3),
    ("Dzire",            "Sedan",          6.8, 0.95),
    ("Ciaz",             "Sedan",          9.5, 0.4),
    ("Ertiga",           "MUV",            8.9, 0.7),
    ("XL6",              "MUV",           11.5, 0.35),
    ("Vitara Brezza",    "Compact SUV",    8.7, 0.75),
    ("Fronx",            "Compact SUV",    8.0, 0.4),
    ("Jimny",            "SUV",           13.0, 0.25),
    ("Grand Vitara",     "SUV",           11.5, 0.3),
]

fuel_types_by_segment = {
    "Hatchback": [("Petrol", 0.72), ("CNG", 0.28)],
    "Premium Hatchback": [("Petrol", 0.75), ("CNG", 0.25)],
    "Sedan": [("Petrol", 0.8), ("CNG", 0.2)],
    "MUV": [("Petrol", 0.85), ("Diesel", 0.15)],
    "Compact SUV": [("Petrol", 0.9), ("CNG", 0.1)],
    "SUV": [("Petrol", 1.0)],
}

n_rows = 1200
rows = []
weights = np.array([m[3] for m in models_info])
weights = weights / weights.sum()

current_year = 2024

for i in range(n_rows):
    name, segment, base_price, _ = models_info[rng.choice(len(models_info), p=weights)]

    year = int(np.clip(rng.normal(2018, 4), 2008, 2023))
    age = current_year - year

    base_km_per_year = rng.normal(12000, 3000)
    km_driven = max(500, int(base_km_per_year * age + rng.normal(0, 8000)))

    fuels, probs = zip(*fuel_types_by_segment[segment])
    fuel = rng.choice(fuels, p=np.array(probs) / sum(probs))

    auto_prob = 0.15 + 0.03 * max(0, year - 2015) + (0.15 if segment in ["SUV", "Compact SUV", "MUV"] else 0)
    auto_prob = min(auto_prob, 0.65)
    transmission = rng.choice(["Manual", "Automatic"], p=[1 - auto_prob, auto_prob])

    owner = rng.choice(
        ["First Owner", "Second Owner", "Third Owner", "Fourth & Above Owner"],
        p=[0.62, 0.27, 0.08, 0.03]
    )

    seller_type = rng.choice(["Individual", "Dealer", "Trustmark Dealer"], p=[0.62, 0.28, 0.10])

    base_mileage = {
        "Hatchback": 21.5, "Premium Hatchback": 22.0, "Sedan": 21.0,
        "MUV": 19.5, "Compact SUV": 20.5, "SUV": 16.5
    }[segment]
    if fuel == "CNG":
        mileage = base_mileage + rng.normal(9, 1.5)
    elif fuel == "Diesel":
        mileage = base_mileage + rng.normal(4, 1.2)
    else:
        mileage = base_mileage + rng.normal(0, 1.2)
    mileage = round(max(14, mileage), 1)

    engine_cc = {
        "Hatchback": 998, "Premium Hatchback": 1197, "Sedan": 1197,
        "MUV": 1462, "Compact SUV": 1462, "SUV": 1462
    }[segment] + int(rng.normal(0, 15))
    max_power = round({
        "Hatchback": 67, "Premium Hatchback": 82, "Sedan": 82,
        "MUV": 103, "Compact SUV": 103, "SUV": 103
    }[segment] + rng.normal(0, 3), 1)

    seats = {"Hatchback": 5, "Premium Hatchback": 5, "Sedan": 5,
             "MUV": rng.choice([6, 7], p=[0.4, 0.6]), "Compact SUV": 5,
             "SUV": rng.choice([4, 5], p=[0.3, 0.7])}[segment]

    depreciation_rate = 0.09
    price = base_price * ((1 - depreciation_rate) ** age)
    price *= max(0.55, 1 - (km_driven / 300000))
    owner_penalty = {"First Owner": 1.0, "Second Owner": 0.92, "Third Owner": 0.85, "Fourth & Above Owner": 0.75}[owner]
    price *= owner_penalty
    if transmission == "Automatic":
        price *= 1.08
    price *= rng.normal(1.0, 0.07)
    price = round(max(1.2, price), 2)

    rows.append({
        "name": f"Suzuki {name}",
        "model": name,
        "segment": segment,
        "year": year,
        "selling_price_lakh": price,
        "km_driven": km_driven,
        "fuel": fuel,
        "seller_type": seller_type,
        "transmission": transmission,
        "owner": owner,
        "mileage_kmpl": mileage,
        "engine_cc": engine_cc,
        "max_power_bhp": max_power,
        "seats": seats,
    })

df = pd.DataFrame(rows)
messy = df.copy()

# 1. Missing values
for col, frac in [("mileage_kmpl", 0.04), ("engine_cc", 0.02), ("seats", 0.03), ("max_power_bhp", 0.02)]:
    idx = messy.sample(frac=frac, random_state=1).index
    messy.loc[idx, col] = np.nan

# 2. Duplicate rows
dupes = messy.sample(n=15, random_state=2)
messy = pd.concat([messy, dupes], ignore_index=True)

# 3. Inconsistent casing / whitespace
idx = messy.sample(frac=0.05, random_state=3).index
messy.loc[idx, "fuel"] = messy.loc[idx, "fuel"].str.upper()
idx2 = messy.sample(frac=0.05, random_state=4).index
messy.loc[idx2, "transmission"] = messy.loc[idx2, "transmission"].apply(lambda x: f" {x} ")

# 4. Mileage as string with unit for a subset (cast column to object first)
messy["mileage_kmpl"] = messy["mileage_kmpl"].astype(object)
idx3 = messy.sample(frac=0.15, random_state=5).index
messy.loc[idx3, "mileage_kmpl"] = messy.loc[idx3, "mileage_kmpl"].apply(
    lambda x: f"{x} kmpl" if pd.notna(x) else x
)

# 5. Outliers / bad entries
messy.loc[messy.sample(n=3, random_state=6).index, "km_driven"] = 999999
messy.loc[messy.sample(n=2, random_state=7).index, "selling_price_lakh"] = 0.01

messy = messy.sample(frac=1, random_state=8).reset_index(drop=True)
messy.to_csv("suzuki_cars_raw.csv", index=False)
print(messy.shape)
print(messy.dtypes)
print(messy.head())
