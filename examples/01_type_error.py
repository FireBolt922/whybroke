def total_price(items, tax_rate):
    subtotal = sum(item["price"] for item in items)
    return subtotal + tax_rate


def checkout(cart):
    return total_price(cart, "0.08")


if __name__ == "__main__":
    cart = [{"price": 10}, {"price": 20}, {"price": 5}]
    print(checkout(cart))
