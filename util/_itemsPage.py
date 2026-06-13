import json
import time as tm
from pathlib import Path


class InventoryCatalog:
    """Load the shop inventory and expose reusable item/category helpers."""

    DEFAULT_NON_CATEGORIES = ("currency",)

    def __init__(self, data_file=None, non_categories=None):
        self.non_categories = set(non_categories or self.DEFAULT_NON_CATEGORIES)
        base_dir = Path(__file__).resolve().parent.parent
        self.data_file = Path(data_file) if data_file else base_dir / "Items.json"
        self.reload()

    def reload(self):
        with open(self.data_file, "r", encoding="utf-8") as handle:
            self.db = json.load(handle)

        self.items = {name: details for name, details in self.db.items() if name != "CATEGORY"}
        self.category_codes = {
            name: code
            for name, code in self.db.get("CATEGORY", {}).items()
            if name not in self.non_categories
        }
        self.categories = sorted({
            str(details.get("category", "")).strip().lower()
            for details in self.items.values()
            if isinstance(details, dict) and details.get("category")
        })
        return self

    def items_by_category(self):
        grouped = {}
        for item_name, details in self.items.items():
            if isinstance(details, dict) and "category" in details:
                category = str(details.get("category", "uncategorized")).strip().lower()
                grouped.setdefault(category, []).append((item_name, details))
        return grouped

    def view_categories(self):
        return list(self.categories)

    def display_categories(self):
        print('=' * 50)
        print('Available categories in the shop:')
        for index, category in enumerate(self.view_categories(), start=1):
            print(f"{index}. {category}")
        print('=' * 50)

    def display_items(self, category=None):
        items = self.view_items(category)
        if not items:
            print('No items found for this category.')
            return

        print('=' * 100)
        for item_name, details in items.items():
            brands = details.get('Brand', {})
            print(f"{item_name:<18} | category={details.get('category', 'n/a'):<12} | brands={len(brands)}")
            for brand_name, brand_info in brands.items():
                print(f"   - {brand_name:<18} | price={brand_info.get('price', 0):>8} | stock={brand_info.get('stock', 0):>5} | unit={brand_info.get('unit', 'pcs')}")
        print('=' * 100)

    def add_to_cart_from_selection(self, user, selection, add_to_cart_fn):
        """Prompt the user to choose an item/brand and add it to the cart."""
        if not add_to_cart_fn:
            print('No cart handler is available.')
            tm.sleep(1)
            return False

        try:
            if '.' not in selection:
                print('Invalid format. Use X.Y (e.g. 3.2)')
                tm.sleep(1)
                return False

            item_token, brand_token = selection.split('.', 1)
            item_idx = int(item_token) - 1
            brand_idx = int(brand_token) - 1
        except ValueError:
            print('Invalid selection.')
            tm.sleep(1)
            return False

        items_in_cat = sorted(self.items_by_category().get(self.current_category, []))
        if item_idx < 0 or item_idx >= len(items_in_cat):
            print('Item number out of range.')
            tm.sleep(1)
            return False

        item_name, item_details = items_in_cat[item_idx]
        brand_list = item_details.get('Brand', {})
        sorted_brands = sorted(brand_list.items())
        if brand_idx < 0 or brand_idx >= len(sorted_brands):
            print('Brand number out of range.')
            tm.sleep(1)
            return False

        brand_name, brand_info = sorted_brands[brand_idx]
        price = brand_info.get('price', 0)
        stock = brand_info.get('stock', 0)
        unit = brand_info.get('unit', 'pcs')

        try:
            qty = int(input(f"Enter quantity to save (available: {stock} {unit}): "))
            if qty <= 0:
                print('Quantity must be positive.')
                tm.sleep(1)
                return False
            if qty > stock:
                print('Not enough stock in store.')
                tm.sleep(1)
                return False
        except ValueError:
            print('Invalid quantity.')
            tm.sleep(1)
            return False

        if user is None:
            print('No user is logged in. Save cancelled.')
            tm.sleep(1)
            return False

        return add_to_cart_fn(
            user,
            item_name=item_name,
            brand_name=brand_name,
            quantity=qty,
            price=price,
            unit=unit,
            item_type=brand_info.get('type', 'N/A'),
            description=item_details.get('description', ''),
        )

    def browse_items(self, user=None, items_per_page=5, start_category=None, role='user', add_to_cart_fn=None):
        """Interactive catalog browser shared by the shop and admin modules."""
        items_by_category = self.items_by_category()
        sorted_categories = sorted(items_by_category.keys())

        if start_category is not None and start_category in sorted_categories:
            current_cat_index = sorted_categories.index(start_category)
        else:
            current_cat_index = 0

        self.current_category = sorted_categories[current_cat_index] if sorted_categories else None

        while True:
            if not sorted_categories:
                print('No items available in the catalog.')
                return

            if current_cat_index >= len(sorted_categories):
                current_cat_index = len(sorted_categories) - 1
            if current_cat_index < 0:
                current_cat_index = 0

            current_category = sorted_categories[current_cat_index]
            self.current_category = current_category
            items_in_cat = sorted(items_by_category[current_category])
            current_page = 0
            total_pages = (len(items_in_cat) + items_per_page - 1) // items_per_page

            while True:
                print(f"\n{'=' * 100}")
                print(f"[{current_cat_index + 1}/{len(sorted_categories)}] Category: {current_category.upper()} - Page {current_page + 1}/{total_pages}")
                print(f"{'=' * 100}")
                print(f"{'#'.ljust(5)} {'Item Name'.ljust(20)} {'Brand'.ljust(20)} {'Price (IDR)'.ljust(15)} {'Unit'.ljust(10)} {'Type'.ljust(20)}")
                print('-' * 100)

                start_idx = current_page * items_per_page
                end_idx = start_idx + items_per_page
                page_items = items_in_cat[start_idx:end_idx]

                for item_index, (item_name, item_details) in enumerate(page_items, start=start_idx + 1):
                    if 'Brand' in item_details:
                        for brand_index, (brand_name, brand_info) in enumerate(sorted(item_details['Brand'].items()), start=1):
                            display_num = f"{item_index}.{brand_index}"
                            print(f"{display_num.ljust(5)} {item_name.ljust(20)} {brand_name.ljust(20)} {str(brand_info.get('price', 'N/A')).ljust(15)} {str(brand_info.get('unit', 'N/A')).ljust(10)} {str(brand_info.get('type', 'N/A')).ljust(20)}")

                print("\nOptions: [N]ext page, [P]rev page, [C]hange category, [Q]uit" + (" , [B]Save to cart" if role != 'admin' else ''))

                try:
                    choice = input('>> ').lower()
                except (EOFError, KeyboardInterrupt):
                    return

                if choice == 'n' and current_page < total_pages - 1:
                    current_page += 1
                    continue
                if choice == 'p' and current_page > 0:
                    current_page -= 1
                    continue
                if choice == 'c':
                    print("\nAvailable categories:")
                    for i, cat in enumerate(sorted_categories, start=1):
                        print(f"{i}. {cat}")
                    try:
                        cat_choice = int(input('Enter category number (or 0 to cancel): '))
                    except ValueError:
                        print('Invalid menu!')
                        tm.sleep(1)
                        continue
                    if 1 <= cat_choice <= len(sorted_categories):
                        current_cat_index = cat_choice - 1
                        current_page = 0
                        break
                    continue
                if choice == 'q':
                    return
                if choice == 'b' and role != 'admin':
                    try:
                        selection = input('Enter item number to save to cart (e.g. 3.2) or 0 to cancel: ').strip()
                    except (EOFError, KeyboardInterrupt):
                        return
                    if selection in ('0', ''):
                        continue
                    success = self.add_to_cart_from_selection(user, selection, add_to_cart_fn)
                    if success:
                        print('Item saved to cart.')
                        tm.sleep(1)
                    continue

                print('Invalid Menu!')
                tm.sleep(1)

    def view_items(self, category=None):
        if category is None:
            return dict(self.items)

        category = category.strip().lower()
        return {
            item_name: details
            for item_name, details in self.items.items()
            if isinstance(details, dict) and str(details.get("category", "")).strip().lower() == category
        }


class Page(InventoryCatalog):
    """Backward-compatible alias for the old Page helper."""

    def view_category(self):
        return self.view_categories()


def make_catalog(data_file=None, non_categories=None):
    return InventoryCatalog(data_file=data_file, non_categories=non_categories)
    
