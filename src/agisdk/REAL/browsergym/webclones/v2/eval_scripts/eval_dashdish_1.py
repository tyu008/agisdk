import json, sys

def to_float(val):
    if val is None:
        return None
    try:
        s = str(val).strip()
        # Remove currency symbols and commas if any
        for ch in ['$', ',', '€', '£']:
            s = s.replace(ch, '')
        return float(s)
    except Exception:
        return None


def get_item_price(item):
    # Prefer finalPrice, else try basePrice+extraCost, else price
    final_price = item.get('finalPrice')
    fp = to_float(final_price)
    if fp is not None:
        return fp
    bp = to_float(item.get('basePrice'))
    ec = to_float(item.get('extraCost'))
    if bp is not None:
        if ec is None:
            ec = 0.0
        return bp + ec
    p = to_float(item.get('price'))
    return p


def is_pizza(item):
    name = item.get('name')
    if not isinstance(name, str):
        return False
    return 'pizza' in name.lower()


def has_exactly_one_valid_pizza(items):
    """Check if items list contains exactly one pizza strictly under $30."""
    if not isinstance(items, list):
        return False
    pizza_items = [it for it in items if isinstance(it, dict) and is_pizza(it) and to_float(it.get('quantity', 1)) != 0]
    # Must have exactly one pizza item
    if len(pizza_items) != 1:
        return False
    # The pizza must be strictly under $30
    price = get_item_price(pizza_items[0])
    if price is None:
        return False
    if price >= 30.0:
        return False
    return True


def evaluate_order(order_obj):
    """Evaluate a single order object."""
    if not isinstance(order_obj, dict):
        return False
    items = order_obj.get('cartItems', [])
    return has_exactly_one_valid_pizza(items)


def main():
    try:
        path = sys.argv[1]
        with open(path, 'r') as f:
            data = json.load(f)
    except Exception:
        print('FAILURE')
        return

    added = (data.get('initialfinaldiff') or {}).get('added') or {}
    cart = added.get('cart') or {}

    # 1) Prefer completed orders if present
    orders = cart.get('foodOrders')
    order_candidates = []
    if isinstance(orders, dict) and orders:
        order_candidates.extend(list(orders.values()))
    elif isinstance(orders, list) and orders:
        order_candidates.extend(orders)

    # Fallback: differences.foodOrders.added
    if not order_candidates:
        diffs_orders = ((data.get('differences') or {}).get('foodOrders') or {}).get('added')
        if isinstance(diffs_orders, dict) and diffs_orders:
            order_candidates.extend(list(diffs_orders.values()))
        elif isinstance(diffs_orders, list) and diffs_orders:
            order_candidates.extend(diffs_orders)

    # Evaluate any order that has exactly one valid pizza
    for ord_obj in order_candidates:
        if evaluate_order(ord_obj):
            print('SUCCESS')
            return

    # 2) Evaluate current cart if no qualifying order found
    cart_items = cart.get('cartItems', [])
    if has_exactly_one_valid_pizza(cart_items):
        print('SUCCESS')
        return

    print('FAILURE')

if __name__ == '__main__':
    main()