#!/usr/bin/env python3
"""
NVIDIA RTX 5090 Availability Checker for Canada
Monitors Best Buy, Newegg, and Amazon Canada for stock availability.
Includes embedded web browser for viewing product pages.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import webbrowser
import sys

# Try to import webview for embedded browser
try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False

# Try to import tkhtmlview for simple HTML display
try:
    from tkhtmlview import HTMLLabel
    TKHTMLVIEW_AVAILABLE = True
except ImportError:
    TKHTMLVIEW_AVAILABLE = False


class GPUChecker:
    """Handles checking GPU availability from various retailers."""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-CA,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }

    # Store URLs for quick access
    STORE_URLS = {
        'Best Buy CA': 'https://www.bestbuy.ca/en-ca/search?search=rtx+5090',
        'Newegg CA': 'https://www.newegg.ca/p/pl?d=rtx+5090',
        'Amazon CA': 'https://www.amazon.ca/s?k=rtx+5090+graphics+card'
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def check_bestbuy_canada(self):
        """Check Best Buy Canada for RTX 5090 availability."""
        results = []
        try:
            url = self.STORE_URLS['Best Buy CA']
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            products = soup.find_all('div', {'class': re.compile(r'productLine|product-item|x-product')})

            if not products:
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
                'url': self.STORE_URLS['Best Buy CA'],
                'error': str(e)
            })

        return results

    def check_newegg_canada(self):
        """Check Newegg Canada for RTX 5090 availability."""
        results = []
        try:
            url = self.STORE_URLS['Newegg CA']
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('div', {'class': 'item-cell'})

            for item in items[:10]:
                try:
                    name_elem = item.find('a', {'class': 'item-title'})
                    if not name_elem:
                        continue

                    name = name_elem.get_text(strip=True)
                    if '5090' not in name.lower():
                        continue

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
                'url': self.STORE_URLS['Newegg CA'],
                'error': str(e)
            })

        return results

    def check_amazon_canada(self):
        """Check Amazon Canada for RTX 5090 availability."""
        results = []
        try:
            url = self.STORE_URLS['Amazon CA']
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('div', {'data-component-type': 's-search-result'})

            for item in items[:10]:
                try:
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

                    price_whole = item.find('span', {'class': 'a-price-whole'})
                    price_fraction = item.find('span', {'class': 'a-price-fraction'})

                    if price_whole:
                        price = f"${price_whole.get_text(strip=True)}"
                        if price_fraction:
                            price += price_fraction.get_text(strip=True)
                    else:
                        price = 'N/A'

                    out_of_stock = item.find(text=re.compile(r'Currently unavailable|Out of Stock', re.I))
                    available = out_of_stock is None and price != 'N/A'

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
                'url': self.STORE_URLS['Amazon CA'],
                'error': str(e)
            })

        return results

    def check_all(self):
        """Check all retailers and return combined results."""
        all_results = []
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


class BrowserWindow:
    """Manages embedded browser windows using pywebview."""

    def __init__(self):
        self.windows = {}

    def open_url(self, url, title="RTX 5090 - Product Page"):
        """Open a URL in a new webview window."""
        if WEBVIEW_AVAILABLE:
            # Open in embedded browser
            def create_window():
                window = webview.create_window(title, url, width=1200, height=800)
                webview.start()

            threading.Thread(target=create_window, daemon=True).start()
        else:
            # Fallback to system browser
            webbrowser.open(url)


class GPUCheckerGUI:
    """Main GUI application for GPU availability checking."""

    def __init__(self, root):
        self.root = root
        self.root.title("RTX 5090 Availability Checker - Canada")
        self.root.geometry("1200x700")
        self.root.minsize(900, 600)

        self.checker = GPUChecker()
        self.browser = BrowserWindow()
        self.is_running = False
        self.update_interval = 1000

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
        ttk.Label(control_frame, text="Interval (sec):").pack(side=tk.LEFT, padx=(20, 5))
        self.interval_var = tk.StringVar(value="1")
        self.interval_entry = ttk.Entry(control_frame, textvariable=self.interval_var, width=5)
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Set", command=self.set_interval).pack(side=tk.LEFT, padx=5)

        # Status and last check
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(control_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.RIGHT, padx=5)

        self.last_check_var = tk.StringVar(value="Last check: Never")
        ttk.Label(control_frame, textvariable=self.last_check_var).pack(side=tk.RIGHT, padx=20)

        # Quick store access frame
        store_frame = ttk.LabelFrame(main_frame, text="Quick Store Access - Click to Open in Browser", padding="5")
        store_frame.pack(fill=tk.X, pady=(0, 10))

        for store_name, store_url in GPUChecker.STORE_URLS.items():
            btn = ttk.Button(
                store_frame,
                text=f"Open {store_name}",
                command=lambda url=store_url, name=store_name: self.open_store(url, name)
            )
            btn.pack(side=tk.LEFT, padx=10, pady=5)

        # Add "Open All" button
        ttk.Button(
            store_frame,
            text="Open All Stores",
            command=self.open_all_stores
        ).pack(side=tk.LEFT, padx=20, pady=5)

        # Browser mode indicator
        if WEBVIEW_AVAILABLE:
            browser_text = "Embedded browser available (pywebview)"
        else:
            browser_text = "Using system browser (install pywebview for embedded)"
        ttk.Label(store_frame, text=browser_text, foreground="gray").pack(side=tk.RIGHT, padx=10)

        # Create paned window for results and browser
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - Results
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        # Results label
        ttk.Label(left_frame, text="Search Results:", font=('Helvetica', 11, 'bold')).pack(anchor=tk.W)

        # Results frame with treeview
        results_frame = ttk.Frame(left_frame)
        results_frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview
        columns = ('store', 'name', 'price', 'status')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings')

        self.tree.heading('store', text='Store')
        self.tree.heading('name', text='Product Name')
        self.tree.heading('price', text='Price (CAD)')
        self.tree.heading('status', text='Status')

        self.tree.column('store', width=90, minwidth=70)
        self.tree.column('name', width=300, minwidth=200)
        self.tree.column('price', width=100, minwidth=70)
        self.tree.column('status', width=90, minwidth=70)

        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        self.item_urls = {}

        # Configure tags
        self.tree.tag_configure('available', background='#90EE90')
        self.tree.tag_configure('unavailable', background='#FFB6C1')
        self.tree.tag_configure('unknown', background='#FFFACD')
        self.tree.tag_configure('error', background='#FFA07A')

        # Right panel - Web preview / URL info
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)

        ttk.Label(right_frame, text="Product Details:", font=('Helvetica', 11, 'bold')).pack(anchor=tk.W)

        # URL display and action buttons
        url_frame = ttk.Frame(right_frame)
        url_frame.pack(fill=tk.X, pady=5)

        ttk.Label(url_frame, text="URL:").pack(side=tk.LEFT)
        self.url_var = tk.StringVar(value="Select a product to see details")
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, state='readonly')
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ttk.Button(url_frame, text="Copy URL", command=self.copy_url).pack(side=tk.LEFT, padx=2)
        ttk.Button(url_frame, text="Open in Browser", command=self.open_selected_url).pack(side=tk.LEFT, padx=2)

        # Product info display
        info_frame = ttk.LabelFrame(right_frame, text="Selected Product", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.product_info = tk.Text(info_frame, wrap=tk.WORD, height=10, font=('Helvetica', 11))
        self.product_info.pack(fill=tk.BOTH, expand=True)
        self.product_info.insert('1.0', "Select a product from the list to view details.\n\n"
                                        "Double-click any row to open the product page.\n\n"
                                        "Use the 'Quick Store Access' buttons above to open store pages directly.")
        self.product_info.config(state='disabled')

        # Action buttons for selected product
        action_frame = ttk.Frame(right_frame)
        action_frame.pack(fill=tk.X, pady=5)

        self.open_btn = ttk.Button(action_frame, text="Open Product Page", command=self.open_selected_url, state='disabled')
        self.open_btn.pack(side=tk.LEFT, padx=5)

        self.open_embedded_btn = ttk.Button(action_frame, text="Open in New Window", command=self.open_embedded, state='disabled')
        self.open_embedded_btn.pack(side=tk.LEFT, padx=5)

        # Legend frame
        legend_frame = ttk.Frame(main_frame)
        legend_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(legend_frame, text="Legend:").pack(side=tk.LEFT, padx=5)

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

        ttk.Label(legend_frame, text="| Double-click to open product page").pack(side=tk.LEFT, padx=20)

    def open_store(self, url, name):
        """Open a store URL."""
        if WEBVIEW_AVAILABLE:
            self.browser.open_url(url, f"RTX 5090 - {name}")
        else:
            webbrowser.open(url)

    def open_all_stores(self):
        """Open all store pages."""
        for name, url in GPUChecker.STORE_URLS.items():
            webbrowser.open(url)

    def on_select(self, event):
        """Handle selection change in treeview."""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            url = self.item_urls.get(item_id, '')
            values = self.tree.item(item_id, 'values')

            self.url_var.set(url)
            self.open_btn.config(state='normal')
            self.open_embedded_btn.config(state='normal')

            # Update product info
            self.product_info.config(state='normal')
            self.product_info.delete('1.0', tk.END)

            info_text = f"Store: {values[0]}\n\n"
            info_text += f"Product: {values[1]}\n\n"
            info_text += f"Price: {values[2]}\n\n"
            info_text += f"Status: {values[3]}\n\n"
            info_text += f"URL: {url}\n\n"
            info_text += "Actions:\n"
            info_text += "• Double-click the row to open in browser\n"
            info_text += "• Click 'Open in Browser' button\n"
            info_text += "• Click 'Copy URL' to copy link"

            self.product_info.insert('1.0', info_text)
            self.product_info.config(state='disabled')
        else:
            self.url_var.set("Select a product to see details")
            self.open_btn.config(state='disabled')
            self.open_embedded_btn.config(state='disabled')

    def on_double_click(self, event):
        """Handle double-click on treeview item."""
        self.open_selected_url()

    def copy_url(self):
        """Copy current URL to clipboard."""
        url = self.url_var.get()
        if url and url != "Select a product to see details":
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            messagebox.showinfo("Copied", "URL copied to clipboard!")

    def open_selected_url(self):
        """Open the selected product URL."""
        url = self.url_var.get()
        if url and url != "Select a product to see details":
            webbrowser.open(url)

    def open_embedded(self):
        """Open URL in embedded browser window."""
        url = self.url_var.get()
        if url and url != "Select a product to see details":
            selection = self.tree.selection()
            if selection:
                values = self.tree.item(selection[0], 'values')
                title = f"{values[0]} - {values[1][:30]}"
            else:
                title = "RTX 5090 Product"
            self.browser.open_url(url, title)

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
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.item_urls.clear()

        for result in results:
            if 'error' in result:
                status = 'Error'
                tag = 'error'
            elif result['available'] is True:
                status = 'IN STOCK!'
                tag = 'available'
            elif result['available'] is False:
                status = 'Out of Stock'
                tag = 'unavailable'
            else:
                status = 'Unknown'
                tag = 'unknown'

            item_id = self.tree.insert(
                '',
                tk.END,
                values=(result['store'], result['name'], result['price'], status),
                tags=(tag,)
            )
            self.item_urls[item_id] = result.get('url', '')

        current_time = datetime.now().strftime("%H:%M:%S")
        self.last_check_var.set(f"Last check: {current_time}")
        self.status_var.set("Ready" if not self.is_running else "Running...")

        # Check for in-stock items and notify
        in_stock = [r for r in results if r.get('available') is True]
        if in_stock:
            self.root.bell()  # System beep
            self.root.attributes('-topmost', True)
            self.root.attributes('-topmost', False)

    def _show_error(self, error_msg):
        """Show an error message."""
        self.status_var.set(f"Error: {error_msg}")


def main():
    """Main entry point."""
    root = tk.Tk()

    style = ttk.Style()
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')

    app = GPUCheckerGUI(root)

    def on_closing():
        app.stop_checking()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
