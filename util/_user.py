import json
import time as tm

import util._shop as shop
from util import pause, clear

class User:
    
    class Cart:
        def __init__(self):
            self
    
    def __init__(self, name=None, balance=0, address=None):
        self.name = name
        self.balance = balance
        self.address = address
        self.items = {
            # items : {
                # items_details : {
                    # items.json
                    # quantity : jumlah barang,
                    # total_price : harga total barang (price * quantity)
                    # }
                # status : "belum dibayar", "dibayar", "dibatalkan", "dikirim", "diterima",
                # address : "alamat pengiriman",                
            # }
        }
        self.cart = {} # items detail : {qty : .., price : ..., totalPrice : ..., }
        self.shop = shop.Shop()

    def new_user(self, name, balance, address):
        self.name = name
        self.balance = balance
        self.address = address
    
    def buy_item(self, item_name, quantity):
        if item_name in self.items:
            item_price = self.items[item_name]["price"]
            total_price = item_price * quantity
            
            if self.balance >= total_price:
                self.balance -= total_price
                self.items[item_name] = {
                    "quantity": quantity,
                    "total_price": total_price,
                    "status": "belum dibayar",
                    "address": self.address
                }
                print(f"{self.name} bought {quantity} {item_name}(s) for {total_price} IDR. Remaining balance: {self.balance} IDR.")
            else:
                print(f"{self.name} does not have enough balance to buy {quantity} {item_name}(s).")
        else:
            print(f"{item_name} is not available in the shop.")
    
    def top_up(self):
        print('-'*50)
        try:
            amount = int(input('Enter top-up amount : '))
            if amount <=0: print('Invalid top-up value!');tm.sleep(1);return
            self.balance += amount
            print(f"{self.name} topped up {amount} IDR. New balance: {self.balance} IDR."); tm.sleep(1)
            
        except ValueError:print('Invalid input!');tm.sleep(1)
        except (KeyboardInterrupt, EOFError):return
    
        
    def checkout_cart(self):
        pending_items = []

        for item_name, brands in self.cart.items():
            for brand_name, details in brands.items():
                if details.get('status') == 'not yet purchased':
                    pending_items.append((item_name, brand_name, details))

        if not pending_items:
            print('There are no pending items to pay for right now.')
            pause()
            return

        print('\nPending cart payment')
        print('=' * 50)
        for index, (item_name, brand_name, details) in enumerate(pending_items, start=1):
            print(f"{index}. {item_name} | {brand_name} | {details.get('quantity', 0)} {details.get('unit', 'pcs')} | {details.get('total_price', 0)} IDR")
        print('-' * 50)

        try:
            selection = input("Select item number(s) to buy (e.g. 1,3 or 'all', 0 to cancel): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return

        if selection in ('0', ''):
            print('Payment cancelled.')
            tm.sleep(1)
            return

        if selection == 'all':
            selected_items = pending_items
        else:
            selected_indices = []
            try:
                selected_indices = [int(value.strip()) - 1 for value in selection.replace(',', ' ').split() if value.strip()]
            except ValueError:
                print('Invalid item selection. Please use numbers like 1,3 or "all".')
                tm.sleep(1)
                return

            invalid = [index + 1 for index in selected_indices if index < 0 or index >= len(pending_items)]
            if invalid:
                print(f"Invalid item number(s): {', '.join(map(str, invalid))}")
                tm.sleep(1)
                return

            if not selected_indices:
                print('No items selected. Payment cancelled.')
                tm.sleep(1)
                return

            selected_items = [pending_items[index] for index in sorted(set(selected_indices))]

        total_due = 0
        for _, _, details in selected_items:
            total_due += details.get('total_price', details.get('quantity', 0) * details.get('unit_price', 0))

        print(f"Total to pay for your selection: {total_due} IDR")
        print('=' * 50)

        try:
            confirm = input('Confirm payment? (y/n): ').lower()
        except (EOFError, KeyboardInterrupt):
            return

        if confirm != 'y':
            print('Payment cancelled.')
            tm.sleep(1)
            return

        if self.balance < total_due:
            print('Insufficient balance to pay for the selected cart items.')
            pause()
            return

        try:
            with open('Items.json', 'r') as f:
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

            self.items.setdefault(item_name, []).append({
                'brand': brand_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price,
                'status': 'purchased',
                'address': self.address,
                'unit': details.get('unit', 'pcs'),
            })
            self.cart[item_name][brand_name]['status'] = 'purchased'

        try:
            with open('Items.json', 'w') as f:
                json.dump(data, f, indent=4)
        except Exception:
            print('Payment completed in memory, but inventory save failed.')
            tm.sleep(1)
            return

        self.shop.refresh_inventory()

        print(f'Payment successful. Remaining balance: {self.balance} IDR')
        pause()

    def check_cart(self):
        print("=" * 100)
        print('My cart')
        print("=" * 100)

        if not self.cart:
            print('Your cart is empty!')
            pause()
            return

        total_pending = 0
        for item_name, brands in self.cart.items():
            for brand_name, details in brands.items():
                status = details.get('status', 'not yet purchased')
                quantity = details.get('quantity', 0)
                total_price = details.get('total_price', 0)
                if status == 'not yet purchased':
                    total_pending += total_price
                print(f"- {(item_name).ljust(15)} | {(brand_name).ljust(15)} | {str(quantity).ljust(3)} {details.get('unit', 'pcs')} | {str(total_price).ljust(15)} IDR | {status}")

        print('\nPending total (not yet purchased):', f"{total_pending} IDR")
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
        print('-'*50)
        print(f"{self.name}'s address: {self.address}")
        try:
            choice = input("1. Update address\n0. Exit\n>>  ")
            match(choice):
                case "1":
                    new_address = input("Enter new address: ")
                    self.address = new_address
                    print(f"{self.name}'s address updated to: {self.address}\n"); pause()
                case "0":
                    print("Exiting address check."); tm.sleep(1.2)
                case _:
                    print("Invalid choice. Exiting address check."); tm.sleep(1.2)
            
        except (KeyboardInterrupt, EOFError):return
    
    def home(self):
        while True:
            clear()
            print(f"Welcome {self.name} ")
            print('='.center(30, '='))
            
            print('Balance:'.ljust(15), f"{self.balance} IDR")
            print('Address:'.ljust(15), self.address)
            print('='.center(30, '=')); tm.sleep(0.5)
            
            print("1. Check Shop")
            print('2. My Shopping cart')
            print("3. Top Up Balance")
            print("4. Check Address")
            print("0. Exit")
            
            try:
                choice = input(">>  ")
            except (EOFError, KeyboardInterrupt):return
            
            match(choice):
                
                case "1":
                    self.shop.display_categories(self)
                case '2':
                    self.check_cart()
                case "3":
                    self.top_up(); 
                case "4":
                    self.check_address()
                case "0":
                    print("Exiting shop. Goodbye!")
                    break
                case _:
                    print("Invalid choice. Please try again."); tm.sleep(1.2)
                
            
    

