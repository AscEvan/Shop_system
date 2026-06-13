import json
import time as tm

import util._shop as shop
from util import pause, clear


class Cart:
    """Encapsulates a user's shopping cart.

    Internally stored as: {item_name: {brand_name: {details...}}}
    where details include quantity, unit_price, total_price, unit,
    type, description, and status.
    """

    STATUS_PENDING = 'not yet purchased'
    STATUS_PURCHASED = 'purchased'

    def __init__(self):
        self._items = {}

    def is_empty(self):
        return not self._items

    def add(self, item_name, brand_name, quantity, price, unit, item_type, description):
        """Add (or increase quantity of) an item/brand in the cart."""
        if quantity <= 0:
            return False

        entry = self._items.setdefault(item_name, {}).setdefault(
            brand_name,
            {
                'quantity': 0,
                'unit_price': price,
                'total_price': 0,
                'unit': unit,
                'type': item_type,
                'description': description,
                'status': self.STATUS_PENDING,
            },
        )
        entry['quantity'] += quantity
        entry['unit_price'] = price
        entry['total_price'] = entry['quantity'] * entry['unit_price']
        entry['status'] = self.STATUS_PENDING
        return True

    def remove(self, item_name, brand_name):
        """Remove an item/brand entry from the cart entirely."""
        brands = self._items.get(item_name)
        if not brands or brand_name not in brands:
            return False

        del brands[brand_name]
        if not brands:
            del self._items[item_name]
        return True

    def all_items(self):
        """Iterate over (item_name, brand_name, details) for every entry."""
        for item_name, brands in self._items.items():
            for brand_name, details in brands.items():
                yield item_name, brand_name, details

    def pending_items(self):
        """Return a list of (item_name, brand_name, details) not yet purchased."""
        return [
            (item_name, brand_name, details)
            for item_name, brand_name, details in self.all_items()
            if details.get('status') == self.STATUS_PENDING
        ]

    def total_pending(self):
        return sum(details.get('total_price', 0) for _, _, details in self.pending_items())

    def mark_purchased(self, item_name, brand_name):
        brands = self._items.get(item_name)
        if brands and brand_name in brands:
            brands[brand_name]['status'] = self.STATUS_PURCHASED
            return True
        return False

    def get(self, item_name, brand_name):
        return self._items.get(item_name, {}).get(brand_name)

    def display(self):
        print('=' * 100)
        print('My cart')
        print('=' * 100)

        if self.is_empty():
            print('Your cart is empty!')
            return

        for item_name, brand_name, details in self.all_items():
            status = details.get('status', self.STATUS_PENDING)
            quantity = details.get('quantity', 0)
            total_price = details.get('total_price', 0)
            print(f"- {item_name.ljust(15)} | {brand_name.ljust(25)} | {str(quantity).ljust(3)} {details.get('unit', 'pcs')} | {str(total_price).ljust(15)} IDR | {status}")

        print('\nPending total (not yet purchased):', f"{self.total_pending()} IDR")


class User:

    # Backward-compatible alias so `User.Cart` still works if referenced elsewhere.
    Cart = Cart

    def __init__(self, name=None, balance=0, address=None):
        self.name = name
        self.balance = balance
        self.address = address
        self.purchase_history = {
            # item_name : [ {brand, quantity, unit_price, total_price, status, address, unit}, ... ]
        }
        self.cart = Cart()
        self.shop = shop.Shop()

    def new_user(self, name, balance, address):
        self.name = name
        self.balance = balance
        self.address = address

    def top_up(self):
        print('-' * 50)
        try:
            amount = int(input('Enter top-up amount : '))
            if amount <= 0:
                print('Invalid top-up value!'); tm.sleep(1); return
            self.balance += amount
            print(f"{self.name} topped up {amount} IDR. New balance: {self.balance} IDR."); tm.sleep(1)
        except ValueError:
            print('Invalid input!'); tm.sleep(1)
        except (KeyboardInterrupt, EOFError):
            return

    def _select_pending_items(self, pending_items):
        """Prompt user to choose which pending cart items to pay for.

        Returns the selected list of (item_name, brand_name, details), or None if cancelled.
        """
        print('\nPending cart payment')
        print('=' * 80)
        for index, (item_name, brand_name, details) in enumerate(pending_items, start=1):
            print(f"{str(index).ljust(3)}. {item_name.ljust(15)} | {brand_name.ljust(25)} | {details.get('quantity', 0)} {details.get('unit', 'pcs')} | {details.get('total_price', 0)} IDR")
        print('-' * 80)

        try:
            selection = input("Select item number(s) to buy (e.g. 1,3 or 'all', 0 to cancel): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None

        if selection in ('0', ''):
            print('Payment cancelled.'); tm.sleep(1)
            return None

        if selection == 'all':
            return pending_items

        try:
            selected_indices = [int(v.strip()) - 1 for v in selection.replace(',', ' ').split() if v.strip()]
        except ValueError:
            print('Invalid item selection. Please use numbers like 1,3 or "all".'); tm.sleep(1)
            return None

        invalid = [i + 1 for i in selected_indices if i < 0 or i >= len(pending_items)]
        if invalid:
            print(f"Invalid item number(s): {', '.join(map(str, invalid))}"); tm.sleep(1)
            return None

        if not selected_indices:
            print('No items selected. Payment cancelled.'); tm.sleep(1)
            return None

        return [pending_items[i] for i in sorted(set(selected_indices))]

    def checkout_cart(self):
        pending_items = self.cart.pending_items()

        if not pending_items:
            print('There are no pending items to pay for right now.')
            pause()
            return

        selected_items = self._select_pending_items(pending_items)
        if not selected_items:
            return

        total_due = sum(details.get('total_price', 0) for _, _, details in selected_items)

        print(f"Total to pay for your selection: {total_due} IDR")
        print('=' * 50)

        try:
            confirm = input('Confirm payment? (y/n): ').lower()
        except (EOFError, KeyboardInterrupt):
            return

        if confirm != 'y':
            print('Payment cancelled.'); tm.sleep(1)
            return

        if self.balance < total_due:
            print('Insufficient balance to pay for the selected cart items.')
            pause()
            return

        try:
            with open(self.shop.catalog.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            print('Unable to update inventory right now.'); tm.sleep(1); return

        for item_name, brand_name, details in selected_items:
            if item_name not in data or 'Brand' not in data[item_name] or brand_name not in data[item_name]['Brand']:
                print(f"Item {item_name} / {brand_name} could not be verified in the inventory.")
                continue

            stock = data[item_name]['Brand'][brand_name].get('stock', 0)
            quantity = details.get('quantity', 0)
            if quantity > stock:
                print(f"Not enough stock for {item_name} ({brand_name}).")
                continue

            unit_price = data[item_name]['Brand'][brand_name].get('price', details.get('unit_price', 0))
            total_price = quantity * unit_price
            self.balance -= total_price
            data[item_name]['Brand'][brand_name]['stock'] = stock - quantity

            self.purchase_history.setdefault(item_name, []).append({
                'brand': brand_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price,
                'status': 'purchased',
                'address': self.address,
                'unit': details.get('unit', 'pcs'),
            })
            self.cart.mark_purchased(item_name, brand_name)

        try:
            with open(self.shop.catalog.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception:
            print('Payment completed in memory, but inventory save failed.')
            tm.sleep(1)
            return

        self.shop.refresh_inventory()

        print(f'Payment successful. Remaining balance: {self.balance} IDR')
        pause()

    def check_cart(self):
        self.cart.display()

        if self.cart.is_empty():
            pause()
            return

        print('\n1. Pay pending items in cart')
        print('0. Back')

        try:
            choice = input('>> ')
        except (EOFError, KeyboardInterrupt):
            return

        if choice == '1':
            self.checkout_cart()
        else:
            print('Returning to menu.')
            tm.sleep(1)

    def check_address(self):
        print('-' * 50)
        print(f"{self.name}'s address: {self.address}")
        try:
            choice = input("1. Update address\n0. Exit\n>>  ")
            match (choice):
                case "1":
                    new_address = input("Enter new address: ")
                    self.address = new_address
                    print(f"{self.name}'s address updated to: {self.address}\n"); pause()
                case "0":
                    print("Exiting address check."); tm.sleep(1.2)
                case _:
                    print("Invalid choice. Exiting address check."); tm.sleep(1.2)
        except (KeyboardInterrupt, EOFError):
            return

    def home(self):
        while True:
            clear()
            print(f"Welcome {self.name} ")
            print('='.center(40, '='))

            print('Balance:'.ljust(15), f"{self.balance} IDR")
            print('Address:'.ljust(15), self.address)
            print('='.center(40, '=')); tm.sleep(0.5)

            print("1. Check Shop")
            print('2. My Shopping cart')
            print("3. Top Up Balance")
            print("4. Check Address")
            print("0. Exit")

            try:
                choice = input(">>  ")
            except (EOFError, KeyboardInterrupt):
                return

            match (choice):
                case "1":
                    self.shop.display_categories(self)
                case '2':
                    self.check_cart()
                case "3":
                    self.top_up()
                case "4":
                    self.check_address()
                case "0":
                    print("Exiting shop. Goodbye!")
                    break
                case _:
                    print("Invalid choice. Please try again."); tm.sleep(1.2)
