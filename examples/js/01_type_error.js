function totalPrice(items, taxRate) {
  const subtotal = items.reduce((sum, item) => sum + item.price, 0);
  return subtotal + taxRate;
}

function checkout(cart) {
  return totalPrice(cart, "0.08");
}

const cart = [{ price: 10 }, { price: 20 }, { price: 5 }];
const total = checkout(cart);
if (typeof total !== "number" || Number.isNaN(total)) {
  throw new TypeError(`checkout returned non-numeric total: ${total}`);
}
console.log(total);
