# write a code of a random list that generates costumers that walk in a grosery store and buy items in salabim
import salabim as sim
import random
import statistics
import matplotlib.pyplot as plt

# create a class for the grosery store
class GroseryStore(sim.Component):
    def process(self):
        while True:
            Customer()
            yield self.hold(sim.Uniform(1, 5).sample())

# create a class for the customer
class Customer(sim.Component):
    def process(self):
        self.enter(store)
        yield self.request(store.cashier)
        yield self.hold(1)
        self.leave(store)

# create a class for the cashier

class Cashier(sim.Component):
    def process(self):
        while True:
            if len(store.waiting_customers()) > 0:
                customer = store.waiting_customers()[0]
                yield self.request(customer)
                yield self.hold(1)
                self.release(customer)
            else:
                yield self.passivate()

# create a class for the store
class Store(sim.Component):
    def process(self):
        self.cashier = Cashier()
        while True:
            yield self.hold(1)

# create a environment
env = sim.Environment(trace=True)
store = Store()
env.run(till=100)

# create a list of the waiting time of the customers
waiting_time = []
for customer in store.exiters():
    waiting_time.append(customer.waiting_time())

# create a histogram of the waiting time of the customers
plt.hist(waiting_time, bins=range(0, 20))
plt.show()

# print the average waiting time of the customers
print(statistics.mean(waiting_time))

# print the maximum waiting time of the customers
print(max(waiting_time))

# print the minimum waiting time of the customers
print(min(waiting_time))

# print the standard deviation of the waiting time of the customers
print(statistics.stdev(waiting_time))

# print the median of the waiting time of the customers
print(statistics.median(waiting_time))

# print the mode of the waiting time of the customers
print(statistics.mode(waiting_time))

# print the variance of the waiting time of the customers
print(statistics.variance(waiting_time))

# print the skewness of the waiting time of the customers
print(statistics.skew(waiting_time))
