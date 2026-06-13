# currency : idr
import json
import time as tm

from . import clear, pause
from util._itemsPage import InventoryCatalog

class Shop:
    def __init__(self, admin=False):
        self.catalog = InventoryCatalog()
        self.items = dict(self.catalog.items)
        self.categories = set(self.catalog.categories)
        if admin is True:
            self.user = 'admin'
        else:
            self.user = 'user'

    def _group_items_by_category(self):
        return self.catalog.items_by_category()

    def refresh_inventory(self):
        try:
            self.catalog.reload()
        except Exception:
            return False

        self.items = dict(self.catalog.items)
        self.categories = set(self.catalog.categories)
        return True

    def add_to_cart(self, user, item_name, brand_name, quantity, price, unit, item_type, description):
        if user is None:
            print("No user is logged in to save this item to the cart.")
            return False

        if not hasattr(user, "cart") or user.cart is None:
            from util._user import Cart
            user.cart = Cart()

        return user.cart.add(item_name, brand_name, quantity, price, unit, item_type, description)

    def add_item_to_cart(self, user, item_name, brand_name, quantity, price, unit, item_type, description):
        """Small wrapper for the catalog browser to add a selected item to the user cart."""
        return self.add_to_cart(user, item_name, brand_name, quantity, price, unit, item_type, description)

    def display_categories(self, user=None):
        clear()
        self.catalog.display_categories()

        try:
            choice = input("Enter the number of the category you want to view (or 0 to exit):\n>> ")
            if choice == '0':
                print('Exit..')
                return

            category_number = int(choice)
            categories = self.catalog.view_categories()
            if 1 <= category_number <= len(categories):
                selected_category = categories[category_number - 1]
                print(f"You selected: {selected_category}")
                self.catalog.browse_items(user=user, role=self.user, start_category=selected_category, add_to_cart_fn=self.add_item_to_cart)
            else:
                print('Invalid choice. Please try again.')
                tm.sleep(1)
        except ValueError:
            print('Invalid input. Please enter a number.')
            tm.sleep(1)
        except (EOFError, KeyboardInterrupt):
            return

    def display_items_paginated(self, user=None, items_per_page=5, start_category=None):
        """Use the shared catalog browser for item display and cart actions."""
        clear()
        self.catalog.browse_items(user=user, role=self.user, items_per_page=items_per_page, start_category=start_category, add_to_cart_fn=self.add_item_to_cart)
        



