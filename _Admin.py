import json

import util._shop as Shop
from util import pause, clear
from util._itemsPage import InventoryCatalog


class Admin:
    def __init__(self):
        self.catalog = InventoryCatalog()
        self.db = self.catalog.db
        self.non_category = list(self.catalog.non_categories)
        self.shop = Shop.Shop(True)
        self.category_codes = self.catalog.category_codes
    
    def save(self, db):
        with open(self.catalog.data_file, 'w', encoding='utf-8') as handle:
            json.dump(db, handle, indent=2)

    def view_items(self, category=None):
        """Show all inventory items, optionally filtered by category."""
        if category is None:
            try:
                category = input('Enter category to filter (blank for all): ').strip().lower()
            except (KeyboardInterrupt, EOFError):
                return

        self.catalog.display_items(category)
        pause()

    def view_all_category(self):
        self.catalog.display_categories()
        
    
    def add_category(self):
        print('===  ADD CATEGORY  ===')

        print('Category to add : ')
        try:
            category = input('>> ').strip().lower()

            if not category:
                print('Category name cannot be empty!'); pause(); return

            if category in self.db.get('CATEGORY', {}):
                print('Category already exists!'); pause(); return

            id = input('Category id(ex. 1xxxxx, 121xxx (6 digits))\n>> ').strip()

            if len(id) != 6 or not id.isdigit():
                print('Invalid ID! Must be exactly 6 digits.'); pause(); return

            if id in self.category_codes.values():
                print('ID already exists!'); pause(); return

            self.db['CATEGORY'][category] = id
            self.save(self.db)
            self.catalog.reload()
            self.category_codes = self.catalog.category_codes
            print('Category added successfully.'); pause()

        except (KeyboardInterrupt, EOFError):
            return

    def _next_item_id(self, category):
        """Generate the next available item ID for a category, based on its category code."""
        category_id = self.db.get('CATEGORY', {}).get(category, '000000')
        prefix = category_id[:3]

        used_ids = set()
        for name, details in self.db.items():
            if name == 'CATEGORY' or not isinstance(details, dict):
                continue
            for brand_info in details.get('Brand', {}).values():
                used_ids.add(str(brand_info.get('id', '')))

        for n in range(1, 1000):
            candidate = f"{prefix}{n:03d}"
            if candidate not in used_ids:
                return candidate

        raise ValueError('No available IDs left in this category (000-999 exhausted).')

    def add_item(self):
        print('=== ADD ITEM ===')
        try:
            item_name = input('Item name: ').strip().title()
            if not item_name or item_name == 'Category':
                print('Invalid item name.'); pause(); return

            existing_item = self.db.get(item_name)

            if existing_item is not None:
                category = existing_item.get('category', '')
                print(f"Item '{item_name}' already exists (category: {category}).")
                brand_name = input('New brand name to add: ').strip()
                if not brand_name:
                    print('Brand name cannot be empty.'); pause(); return

                if brand_name in existing_item.get('Brand', {}):
                    print(f"Brand '{brand_name}' already exists for '{item_name}'."); pause(); return

                price = int(input('Price: '))
                stock = int(input('Stock: '))
                item_type = input('Type: ').strip()
                unit = input('Unit (pcs/kg/liter): ').strip() or 'pcs'

                new_id = self._next_item_id(category)
                existing_item.setdefault('Brand', {})[brand_name] = {
                    'id': new_id,
                    'price': price,
                    'stock': stock,
                    'type': item_type,
                    'unit': unit,
                }
                self.save(self.db)
                self.catalog.reload()
                print(f"Brand '{brand_name}' added to '{item_name}' with ID {new_id}.")
                pause()
                return

            category = input('Category: ').strip().lower()
            if category not in self.db.get('CATEGORY', {}):
                print('Unknown category. Add the category first or pick an existing one.'); pause(); return

            description = input('Description: ').strip()
            brand_name = input('Brand name: ').strip()
            if not brand_name:
                print('Brand name cannot be empty.'); pause(); return

            price = int(input('Price: '))
            stock = int(input('Stock: '))
            item_type = input('Type: ').strip()
            unit = input('Unit (pcs/kg/liter): ').strip() or 'pcs'

            new_id = self._next_item_id(category)
            new_item = {
                'Brand': {
                    brand_name: {
                        'id': new_id,
                        'price': price,
                        'stock': stock,
                        'type': item_type,
                        'unit': unit,
                    }
                },
                'description': description,
                'category': category,
            }
            self.db[item_name] = new_item
            self.save(self.db)
            self.catalog.reload()
            print(f"Item '{item_name}' added successfully with ID {new_id}.")
            pause()
        except ValueError as e:
            print(str(e) if str(e) else 'Invalid number entered.')
            pause()
        except (KeyboardInterrupt, EOFError):
            return



def main():
    admin = Admin()
    while True:
        clear()
        
        print('======== ADMIN ========')
        print('1. View all categories')
        print('2. View all items')
        print('3. Add category')
        print('4. Add item')
        
        
        try:
            
            choice = input('or 0. to exit\n>> ')
        except(KeyboardInterrupt, EOFError):return
        
        match(choice):
            case '1':
                admin.view_all_category()
                pause();
            case '2':
                admin.view_items()
                
            case '3':
                admin.add_category()
            case '4':
                admin.add_item()
                
            case '0':
                print('Exit..');return
        
            case _:
                print('Invalid Input!'); pause()


def test():
    a = Admin()
    
    n = a.category_codes
    print(n)


if __name__ == '__main__':
    main()
    test()