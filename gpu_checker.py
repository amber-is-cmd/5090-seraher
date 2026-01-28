#!/usr/bin/env python3
"""
NVIDIA RTX 5090 Availability Checker for Canada
Monitors Best Buy, Newegg, and Amazon Canada for stock availability.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
import urllib.parse

class GPUChecker:
    """Handles checking GPU availability from various retailers."""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-CA,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def check_bestbuy_canada(self):
        """Check Best Buy Canada for RTX 5090 availability."""
        results = []
        try:
            # Best Buy Canada search URL for RTX 5090
            url = "https://www.bestbuy.ca/en-ca/search?search=rtx+5090"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for product containers
            products = soup.find_all('div', {'class': re.compile(r'productLine|product-item|x-product')})

            if not products:
                # Try API endpoint
                api_url = "https://www.bestbuy.ca/api/v2/json/search?query=rtx%205090&lang=en-CA"
                api_response = self.session.get(api_url, timeout=10)
                if api_response.status_code == 200:
                    data = api_response.json()
                    if 'products' in data:
                        for product in data['products'][:10]:
                            if '5090' in product.get('name', '').lower():
                                name = product.get('name', 'RTX 5090')
                                price = product.get('salePrice', product.get('regularPrice', 'N/A'))
                                available = product.get('isAvailableOnline', False) or product.get('isAvailable', False)

                                results.append({
                                    'name': name[:60] + '...' if len(name) > 60 else name,
                                    'price': f"${price}" if price != 'N/A' else 'N/A',
                                    'available': available,
                                    'store': 'Best Buy CA',
                                    'url': f"https://www.bestbuy.ca{product.get('productUrl', '')}"
                                })

            if not results:
                results.append({
                    'name': 'RTX 5090 (Search Results)',
                    'price': 'Check website',
                    'available': None,
                    'store': 'Best Buy CA',
                    'url': url
                })

        except requests.RequestException as e:
            results.append({
                'name': 'RTX 5090',
                'price': 'Error',
                'available': None,
                'store': 'Best Buy CA',
                'url': 'https://www.bestbuy.ca/en-ca/search?search=rtx+5090',
                'error': str(e)
            })

        return results

    def check_newegg_canada(self):
        """Check Newegg Canada for RTX 5090 availability."""
        results = []
        try:
            # Newegg Canada search URL for RTX 5090
            url = "https://www.newegg.ca/p/pl?d=rtx+5090"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for product items
            items = soup.find_all('div', {'class': 'item-cell'})

            for item in items[:10]:
                try:
                    # Get product name
                    name_elem = item.find('a', {'class': 'item-title'})
                    if not name_elem:
                        continue

                    name = name_elem.get_text(strip=True)
                    if '5090' not in name.lower():
                        continue

                    # Get price
                    price_elem = item.find('li', {'class': 'price-current'})
                    if price_elem:
                        price_strong = price_elem.find('strong')
                        price_sup = price_elem.find('sup')
                        if price_strong:
                            price = f"${price_strong.get_text(strip=True)}"
                            if price_sup:
                                price += price_sup.get_text(strip=True)
                        else:
                            price = 'N/A'
                    else:
                        price = 'N/A'

                    # Check availability
                    add_to_cart = item.find('button', {'class': re.compile(r'btn-primary|add-to-cart')})
                    out_of_stock = item.find(text=re.compile(r'OUT OF STOCK|SOLD OUT', re.I))

                    available = add_to_cart is not None and out_of_stock is None

                    product_url = name_elem.get('href', url)

                    results.append({
                        'name': name[:60] + '...' if len(name) > 60 else name,
                        'price': price,
                        'available': available,
                        'store': 'Newegg CA',
                        'url': product_url
                    })

                except Exception:
                    continue

            if not results:
                results.append({
                    'name': 'RTX 5090 (Search Results)',
                    'price': 'Check website',
                    'available': None,
                    'store': 'Newegg CA',
                    'url': url
                })

        except requests.RequestException as e:
            results.append({
                'name': 'RTX 5090',
                'price': 'Error',
                'available': None,
                'store': 'Newegg CA',
                'url': 'https://www.newegg.ca/p/pl?d=rtx+5090',
                'error': str(e)
            })

        return results

    def check_amazon_canada(self):
        """Check Amazon Canada for RTX 5090 availability."""
        results = []
        try:
            # Amazon Canada search URL for RTX 5090
            url = "https://www.amazon.ca/s?k=rtx+5090+graphics+card"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for search results
            items = soup.find_all('div', {'data-component-type': 's-search-result'})

            for item in items[:10]:
                try:
                    # Get product name
                    name_elem = item.find('span', {'class': 'a-text-normal'})
                    if not name_elem:
                        h2 = item.find('h2')
                        if h2:
                            name_elem = h2.find('span')

                    if not name_elem:
                        continue

                    name = name_elem.get_text(strip=True)
                    if '5090' not in name.lower():
                        continue

                    # Get price
                    price_whole = item.find('span', {'class': 'a-price-whole'})
                    price_fraction = item.find('span', {'class': 'a-price-fraction'})

                    if price_whole:
                        price = f"${price_whole.get_text(strip=True)}"
                        if price_fraction:
                            price += price_fraction.get_text(strip=True)
                    else:
                        price = 'N/A'

                    # Check availability
                    out_of_stock = item.find(text=re.compile(r'Currently unavailable|Out of Stock', re.I))
                    available = out_of_stock is None and price != 'N/A'

                    # Get product URL
                    link = item.find('a', {'class': 'a-link-normal s-no-outline'})
                    if link:
                        product_url = 'https://www.amazon.ca' + link.get('href', '')
                    else:
                        product_url = url

                    results.append({
                        'name': name[:60] + '...' if len(name) > 60 else name,
                        'price': price,
                        'available': available,
                        'store': 'Amazon CA',
                        'url': product_url
                    })

                except Exception:
                    continue

            if not results:
                results.append({
                    'name': 'RTX 5090 (Search Results)',
                    'price': 'Check website',
                    'available': None,
                    'store': 'Amazon CA',
                    'url': url
                })

        except requests.RequestException as e:
            results.append({
                'name': 'RTX 5090',
                'price': 'Error',
                'available': None,
                'store': 'Amazon CA',
                'url': 'https://www.amazon.ca/s?k=rtx+5090+graphics+card',
                'error': str(e)
            })

        return results

    def check_all(self):
        """Check all retailers and return combined results."""
        all_results = []

        # Run checks in parallel using threads
        threads = []
        results_lock = threading.Lock()

        def check_store(check_func):
            result = check_func()
            with results_lock:
                all_results.extend(result)

        for check_func in [self.check_bestbuy_canada, self.check_newegg_canada, self.check_amazon_canada]:
            t = threading.Thread(target=check_store, args=(check_func,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return all_results


class GPUCheckerGUI:
    """Main GUI application for GPU availability checking."""

    def __init__(self, root):
        self.root = root
        self.root.title("RTX 5090 Availability Checker - Canada")
        self.root.geometry("1000x600")
        self.root.minsize(800, 500)

        self.checker = GPUChecker()
        self.is_running = False
        self.update_interval = 1000  # 1 second in milliseconds

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="NVIDIA RTX 5090 Availability Checker - Canada",
            font=('Helvetica', 16, 'bold')
        )
        title_label.pack(pady=(0, 10))

        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Start/Stop button
        self.start_button = ttk.Button(
            control_frame,
            text="Start Checking",
            command=self.toggle_checking
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        # Check Now button
        self.check_now_button = ttk.Button(
            control_frame,
            text="Check Now",
            command=self.check_now
        )
        self.check_now_button.pack(side=tk.LEFT, padx=5)

        # Interval setting
        ttk.Label(control_frame, text="Interval (seconds):").pack(side=tk.LEFT, padx=(20, 5))
        self.interval_var = tk.StringVar(value="1")
        self.interval_entry = ttk.Entry(control_frame, textvariable=self.interval_var, width=5)
        self.interval_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Set", command=self.set_interval).pack(side=tk.LEFT, padx=5)

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(control_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # Last check time
        self.last_check_var = tk.StringVar(value="Last check: Never")
        ttk.Label(control_frame, textvariable=self.last_check_var).pack(side=tk.RIGHT, padx=20)

        # Results frame with treeview
        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview
        columns = ('store', 'name', 'price', 'status')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings')

        # Define headings
        self.tree.heading('store', text='Store')
        self.tree.heading('name', text='Product Name')
        self.tree.heading('price', text='Price (CAD)')
        self.tree.heading('status', text='Availability')

        # Define column widths
        self.tree.column('store', width=100, minwidth=80)
        self.tree.column('name', width=500, minwidth=300)
        self.tree.column('price', width=120, minwidth=80)
        self.tree.column('status', width=120, minwidth=80)

        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click to open URL
        self.tree.bind('<Double-1>', self.open_url)

        # Store URLs for each item
        self.item_urls = {}

        # Configure tags for coloring
        self.tree.tag_configure('available', background='#90EE90')  # Light green
        self.tree.tag_configure('unavailable', background='#FFB6C1')  # Light red
        self.tree.tag_configure('unknown', background='#FFFACD')  # Light yellow
        self.tree.tag_configure('error', background='#FFA07A')  # Light salmon

        # Legend frame
        legend_frame = ttk.Frame(main_frame)
        legend_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(legend_frame, text="Legend:").pack(side=tk.LEFT, padx=5)

        # Legend items
        legends = [
            ('In Stock', '#90EE90'),
            ('Out of Stock', '#FFB6C1'),
            ('Unknown', '#FFFACD'),
            ('Error', '#FFA07A')
        ]

        for text, color in legends:
            frame = ttk.Frame(legend_frame)
            frame.pack(side=tk.LEFT, padx=10)
            canvas = tk.Canvas(frame, width=15, height=15, bg=color, highlightthickness=1)
            canvas.pack(side=tk.LEFT, padx=2)
            ttk.Label(frame, text=text).pack(side=tk.LEFT)

        ttk.Label(legend_frame, text="(Double-click a row to open product page)").pack(side=tk.RIGHT, padx=5)

    def toggle_checking(self):
        """Toggle automatic checking on/off."""
        if self.is_running:
            self.stop_checking()
        else:
            self.start_checking()

    def start_checking(self):
        """Start automatic checking."""
        self.is_running = True
        self.start_button.config(text="Stop Checking")
        self.status_var.set("Running...")
        self.check_availability()

    def stop_checking(self):
        """Stop automatic checking."""
        self.is_running = False
        self.start_button.config(text="Start Checking")
        self.status_var.set("Stopped")

    def set_interval(self):
        """Set the check interval."""
        try:
            interval = int(self.interval_var.get())
            if interval < 1:
                raise ValueError("Interval must be at least 1 second")
            self.update_interval = interval * 1000
            messagebox.showinfo("Success", f"Interval set to {interval} seconds")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid interval: {e}")

    def check_now(self):
        """Perform a single check immediately."""
        self.status_var.set("Checking...")
        threading.Thread(target=self._perform_check, daemon=True).start()

    def check_availability(self):
        """Check availability and schedule next check."""
        if not self.is_running:
            return

        self.status_var.set("Checking...")
        threading.Thread(target=self._perform_check, daemon=True).start()

    def _perform_check(self):
        """Perform the actual availability check in a background thread."""
        try:
            results = self.checker.check_all()
            self.root.after(0, lambda: self._update_results(results))
        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))

        if self.is_running:
            self.root.after(self.update_interval, self.check_availability)

    def _update_results(self, results):
        """Update the results display."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.item_urls.clear()

        # Add new results
        for result in results:
            # Determine status text and tag
            if 'error' in result:
                status = 'Error'
                tag = 'error'
            elif result['available'] is True:
                status = 'IN STOCK'
                tag = 'available'
            elif result['available'] is False:
                status = 'Out of Stock'
                tag = 'unavailable'
            else:
                status = 'Unknown'
                tag = 'unknown'

            # Insert item
            item_id = self.tree.insert(
                '',
                tk.END,
                values=(result['store'], result['name'], result['price'], status),
                tags=(tag,)
            )

            # Store URL
            self.item_urls[item_id] = result.get('url', '')

        # Update last check time
        current_time = datetime.now().strftime("%H:%M:%S")
        self.last_check_var.set(f"Last check: {current_time}")
        self.status_var.set("Ready" if not self.is_running else "Running...")

    def _show_error(self, error_msg):
        """Show an error message."""
        self.status_var.set(f"Error: {error_msg}")

    def open_url(self, event):
        """Open the product URL when double-clicked."""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            url = self.item_urls.get(item_id, '')
            if url:
                import webbrowser
                webbrowser.open(url)


def main():
    """Main entry point."""
    root = tk.Tk()

    # Set theme
    style = ttk.Style()
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')

    app = GPUCheckerGUI(root)

    # Handle window close
    def on_closing():
        app.stop_checking()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()


if __name__ == "__main__":
    main()
