from tools import search_products, find_physical_stores

print("Testing search_products...")
products = search_products("melk", size=1)
if "data" in products:
    print("✅ search_products success")
    print(products['data'][0]['name'])
else:
    print("❌ search_products failed")
    print(products)

print("\nTesting find_physical_stores...")
stores = find_physical_stores(search="Oslo", size=1)
if "data" in stores:
    print("✅ find_physical_stores success")
else:
    print("❌ find_physical_stores failed")
    print(stores)
