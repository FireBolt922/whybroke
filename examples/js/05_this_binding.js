class Counter {
  constructor() {
    this.value = 0;
  }

  increment() {
    this.value += 1;
    return this.value;
  }
}

const counter = new Counter();
const tick = counter.increment;
tick();
console.log(counter.value);
