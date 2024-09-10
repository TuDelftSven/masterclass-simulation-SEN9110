import salabim as sim
import random
import math
import pandas as pd
import matplotlib.pyplot as plt


# Set the model to yield-based (allow use of 'yield' in process functions)
sim.yieldless(False)

# Initialize the simulation environment
env = sim.Environment()

# Define the departments and their item distributions (min, mode, max)
departments_items = {
    'A': (4, 10, 22),   # Fruit & Vegetables
    'B': (0, 4, 9),     # Meat & Fish
    'C': (1, 4, 10),    # Bread
    'D': (1, 3, 11),    # Cheese & Dairy
    'E': (6, 17, 35),   # Canned & packed food
    'F': (2, 8, 19),    # Frozen foods
    'G': (1, 9, 20),    # Drinks
}

# Define routes
route_1 = ['A', 'B', 'C', 'D', 'E', 'F', 'G']  # 40% follow this route
route_2 = ['B', 'C', 'D', 'E', 'A', 'F', 'G']  # 60% follow this route

customers_info = pd.DataFrame(columns=['customer', 'cart', 'arrival_time', 'departure_time', 'total_time', 'cart_wait', 'bread_wait', 'cheese_wait', 'grocery_list', 'item_count', 'route'])

class Customer(sim.Component):
    def process(self):
        # Decide which route the customer will follow
        arrival_time = (env.now())  # Log the simulation time when the customer arrives
        if random.random() < 0.4:
            self.route = route_1  # 40% follow route A-B-C-D-E-F-G
        else:
            self.route = route_2  # 60% follow route B-C-D-E-A-F-G

        self.grocery_list = self.select_items()
        # Arrival at supermarket
        if random.random() < 0.8:
            self.had_cart = True
            cart_start = env.now()
            yield self.request(cart)  # 80% of customers take a cart
            cart_wait = env.now() - cart_start
        else:
            self.had_cart = False
            cart_wait = 0



        for dep, items in self.grocery_list.items():
            if dep == "C" and items != 0:
                bread_start = env.now()
                yield self.request(bread_counter)
                bread_wait = env.now() - bread_start
                bread_6 = math.ceil(items/6)
                for n in range(bread_6):
                    yield self.hold(120)
                self.release(bread_counter)

            elif dep == "D" and items != 0:
                cheese_start = env.now()
                yield self.request(cheese_counter)
                cheese_wait = env.now() - cheese_start
                cheese_6 = math.ceil(items / 6)
                for n in range(cheese_6):
                    yield self.hold(60)
                self.release(cheese_counter)
            else:
                for n in range(items):
                    yield self.hold(sim.Uniform(20, 30).sample())
        # Proceed to checkout


        checkout_line = min(checkout_lanes, key=lambda lane: lane.length())
        self.enter(checkout_line)
        item_count = 0
        for dep, item in self.grocery_list.items():
            item_count += item
        yield self.hold(item_count * 1.1 + sim.Uniform(40, 60).sample())  # Scanning & payment
        self.leave(checkout_line)
        if self.isclaiming(cart):
            self.release(cart)

        # Record the end time when the customer leaves
        departure_time = env.now()

        # Calculate total shopping time for the customer
        total_time = departure_time - arrival_time

        # Add the customer information to the dataframe (outside the cart conditional block)
        new_data = pd.DataFrame({
            'customer': [self.name()],
            'cart': [self.had_cart],
            'arrival_time': [arrival_time],
            'departure_time': [departure_time],
            'total_time': [total_time],
            'cart_wait': [cart_wait],
            'bread_wait': [bread_wait],
            'cheese_wait': [cheese_wait],
            'grocery_list': [self.grocery_list],
            'item_count': [item_count],
            'route': [self.route]
        })

        # Append to the dataframe using concat
        global customers_info
        customers_info = pd.concat([customers_info, new_data], ignore_index=True)

    def select_items(self):
        # Generate a random number of items for each department (based on min, mode, and max data)
        grocery_list = {}
        for dep in self.route:
            min_val, mode_val, max_val = departments_items[dep]
            items_picked = int(sim.Triangular(min_val, max_val, mode_val).sample())
            grocery_list[dep] = items_picked
        return grocery_list




# Resources (initialize after creating the environment)
cart = sim.Resource('Shopping cart', capacity=45)
bread_counter = sim.Resource('Bread counter', capacity=4)
cheese_counter = sim.Resource('Cheese counter', capacity=3)
checkout_lanes = [sim.Queue(f'Checkout lane {i + 1}') for i in range(3)]  # 3 checkout lanes


class ArrivalGenerator(sim.Component):
    def process(self):
        tot = 0
        for hour, arrival_rate in arrival_data:
            tot += arrival_rate
            # Generate customers for the current hour
            for _ in range(arrival_rate):
                Customer().activate()
                # Spread the arrivals uniformly over the hour (3600 seconds)
                yield self.hold(3600/arrival_rate)



# Customer arrival rates per hour
arrival_data = [
    (8, 30), (9, 80), (10, 110), (11, 90), (12, 80),
    (13, 70), (14, 80), (15, 90), (16, 100), (17, 120),
    (18, 90), (19, 40)
]


# Create a few test customers
ArrivalGenerator().activate()
env.run(12 * 3600)  # Simulate for 12 hours

# print(f'Averages:\n bread wait {customers_info['bread_wait'].mean()} \n cheese wait {customers_info['cheese_wait'].mean()}\n cart wait {customers_info['cart_wait'].mean()}')
# print(f'Max:\n bread wait {customers_info['bread_wait'].max()} \n cheese wait {customers_info['cheese_wait'].max()}\n cart wait {customers_info['cart_wait'].max()}')
# print(f'Min:\n bread wait {customers_info['bread_wait'].min()} \n cheese wait {customers_info['cheese_wait'].min()}\n cart wait {customers_info['cart_wait'].min()}')
print(bread_counter.print_statistics())