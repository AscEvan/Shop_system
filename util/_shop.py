# currency : idr
import json
import time as tm


from util import pause, clear

class Shop:
    def __init__(self):
        with open("Items.json", "r") as f:
            self.items = json.load(f)
            self.items = {k: v for k, v in self.items.items() if k != "CATEGORY "}
            self.categories = set(
                item["category"]
                for item in self.items.values()
                if isinstance(item, dict) and "category" in item
            )

    def _group_items_by_category(self):
        items_by_category = {}
        for item_name, item_details in self.items.items():
            if isinstance(item_details, dict) and "category" in item_details:
                cat = item_details.get("category", "uncategorized").strip().lower()
                items_by_category.setdefault(cat, []).append((item_name, item_details))
        return items_by_category

    def refresh_inventory(self):
        try:
            with open("Items.json", "r") as f:
                data = json.load(f)
        except Exception:
            return False

        self.items = {k: v for k, v in data.items() if k != "CATEGORY "}
        self.categories = set(
            item["category"]
            for item in self.items.values()
            if isinstance(item, dict) and "category" in item
        )
        return True

    def add_to_cart(self, user, item_name, brand_name, quantity, price, unit, item_type, description):
        if user is None:
            print("No user is logged in to save this item to the cart.")
            return False

        if not hasattr(user, "cart") or user.cart is None:
            user.cart = {}

        brand_entry = user.cart.setdefault(item_name, {}).setdefault(
            brand_name,
            {
                "quantity": 0,
                "unit_price": price,
                "total_price": 0,
                "unit": unit,
                "type": item_type,
                "description": description,
                "status": "not yet purchased",
            },
        )
        brand_entry["quantity"] += quantity
        brand_entry["total_price"] = brand_entry["quantity"] * brand_entry["unit_price"]
        brand_entry["status"] = "not yet purchased"
        return True

    def display_categories(self, user=None):
        clear()
        print('=' * 50)
        print("Available categories in the shop:")
        sorted_categories = sorted(self.categories)
        for i, category in enumerate(sorted_categories, start=1):
            print(f"{i}. {category}")
        print('=' * 50)

        try:
            choice = input("Enter the number of the category you want to view (or 0 to exit):\n>> ")
            if choice == '0':
                print('Exit..')
                return

            choice = int(choice)
            if 1 <= choice <= len(sorted_categories):
                selected_category = sorted_categories[choice - 1]
                print(f"You selected: {selected_category}")
                self.display_items_paginated(user=user, start_category=selected_category)
            else:
                print("Invalid choice. Please try again.")
                tm.sleep(1)
        except ValueError:
            print("Invalid input. Please enter a number.")
            tm.sleep(1)
        except (EOFError, KeyboardInterrupt):
            return

    def display_items_paginated(self, user=None, items_per_page=5, start_category=None):
        """Display shop items with category pagination and cart-saving instead of immediate payment."""
        clear()
        items_by_category = self._group_items_by_category()
        sorted_categories = sorted(items_by_category.keys())

        if start_category is not None and start_category in sorted_categories:
            current_cat_index = sorted_categories.index(start_category)
        else:
            current_cat_index = 0

        
        while True:
            if current_cat_index >= len(sorted_categories):
                current_cat_index = len(sorted_categories) - 1
            if current_cat_index < 0:
                current_cat_index = 0
            
            current_category = sorted_categories[current_cat_index]
            items_in_cat = sorted(items_by_category[current_category])
            
            # Pagination for current category
            current_page = 0
            total_pages = (len(items_in_cat) + items_per_page - 1) // items_per_page
            
            while True:
                print(f"\n{'='*100}")
                print(f"[{current_cat_index + 1}/{len(sorted_categories)}] Category: {current_category.upper()} - Page {current_page + 1}/{total_pages}")
                print(f"{'='*100}")
                
                print(f"{'#'.ljust(5)} {'Item Name'.ljust(20)} {'Brand'.ljust(20)} {'Price (IDR)'.ljust(15)} {'Unit'.ljust(10)} {'Type'.ljust(20)}")
                print("-" * 100)
                
                # Display items on current page
                start_idx = current_page * items_per_page
                end_idx = start_idx + items_per_page
                page_items = items_in_cat[start_idx:end_idx]
                
                for item_index, (item_name, item_details) in enumerate(page_items, start=start_idx+1):
                    if "Brand" in item_details:
                        brand_list = item_details["Brand"]
                        for brand_index, (brand_name, brand_info) in enumerate(sorted(brand_list.items()), start=1):
                            price = brand_info.get("price", "N/A")
                            unit = brand_info.get('unit', 'N/A')
                            item_type = brand_info.get("type", "N/A")
                            display_num = f"{item_index}.{brand_index}"
                            print(f"{display_num.ljust(5)} {item_name.ljust(20)} {brand_name.ljust(20)} {str(price).ljust(15)} {str(unit).ljust(10)} {item_type.ljust(20)}")
                
                try:
                        
                    print("\nOptions: [N]ext page, [P]rev page, [C]hange category, [Q]uit, [B]Save to cart")
                    choice = input(">> ").lower()
                    
                    if choice == 'n' and current_page < total_pages - 1:
                        current_page += 1
                    elif choice == 'p' and current_page > 0:
                        current_page -= 1
                    elif choice == 'c':
                        # Show category list
                        print("\nAvailable categories:")
                        for i, cat in enumerate(sorted_categories, start=1):
                            print(f"{i}. {cat}")
                        try:
                            cat_choice = int(input("Enter category number (or 0 to cancel): "))
                            if 1 <= cat_choice <= len(sorted_categories):
                                current_cat_index = cat_choice - 1
                                current_page = 0
                                items_in_cat = sorted(items_by_category[sorted_categories[current_cat_index]])
                                total_pages = (len(items_in_cat) + items_per_page - 1) // items_per_page
                                break
                        except ValueError:
                            print('Invalid menu!');tm.sleep(1)
                    elif choice == 'q':
                        return
                    elif choice == 'b':
                        try:
                            sel = input("Enter item number to save to cart (e.g. 3.2) or 0 to cancel: ").strip()
                            if sel == '0' or sel == '':
                                continue
                            if '.' not in sel:
                                print('Invalid format. Use X.Y (e.g. 3.2)'); tm.sleep(1); continue
                            part_a, part_b = sel.split('.', 1)
                            item_idx = int(part_a) - 1
                            brand_idx = int(part_b) - 1
                        except ValueError:
                            print('Invalid selection.'); tm.sleep(1); continue

                        if item_idx < 0 or item_idx >= len(items_in_cat):
                            print('Item number out of range.'); tm.sleep(1); continue

                        item_name, item_details = items_in_cat[item_idx]
                        brand_list = item_details.get('Brand', {})
                        sorted_brands = sorted(brand_list.items())
                        if brand_idx < 0 or brand_idx >= len(sorted_brands):
                            print('Brand number out of range.'); tm.sleep(1); continue

                        brand_name, brand_info = sorted_brands[brand_idx]
                        price = brand_info.get('price', 0)
                        stock = brand_info.get('stock', 0)
                        unit = brand_info.get('unit', 'pcs')

                        try:
                            qty = int(input(f"Enter quantity to save (available: {stock} {unit}): "))
                            if qty <= 0:
                                print('Quantity must be positive.'); tm.sleep(1); continue
                            if qty > stock:
                                print('Not enough stock in store.'); tm.sleep(1); continue
                        except ValueError:
                            print('Invalid quantity.'); tm.sleep(1); continue

                        if user is None:
                            print('No user is logged in. Save cancelled.'); tm.sleep(1); continue

                        total_price = price * qty
                        self.add_to_cart(
                            user,
                            item_name=item_name,
                            brand_name=brand_name,
                            quantity=qty,
                            price=price,
                            unit=unit,
                            item_type=brand_info.get('type', 'N/A'),
                            description=item_details.get('description', ''),
                        )

                        print('\nItem saved to cart:')
                        print('='*40)
                        print(f"Item: {item_name.ljust(15)}")
                        print(f"Brand: {brand_name}")
                        print(f"Quantity: {qty} {unit}")
                        print(f"Estimated total: {total_price} IDR")
                        print("Status: not yet purchased")
                        print('='*40)
                        pause()

                    else:print('Invalid Menu!');tm.sleep(1)
                except(EOFError, KeyboardInterrupt):return
        



