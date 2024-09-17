import salabim as sim
import random
import math
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def simulation(replications):
    shop_info_all = []
    customer_info_all = []
    for i in range(replications):

        sim.yieldless(False)
        # Initialize the simulation environment
        env = sim.Environment()


        # Set seeds
        sim.random_seed(i)
        random.seed(i)

        # Define the departments and their item distributions (min, mode, max)
        env.departments_items = {
            'A': (4, 10, 22),   # Fruit & Vegetables
            'B': (0, 4, 9),     # Meat & Fish
            'C': (1, 4, 10),    # Bread
            'D': (1, 3, 11),    # Cheese & Dairy
            'E': (6, 17, 35),   # Canned & packed food
            'F': (2, 8, 19),    # Frozen foods
            'G': (1, 9, 20),    # Drinks
        }

        # Define routes
        env.route_1 = ['A', 'B', 'C', 'D', 'E', 'F', 'G']  # 40% follow this route
        env.route_2 = ['B', 'C', 'D', 'E', 'A', 'F', 'G']  # 60% follow this route

        env.customers_info = pd.DataFrame(columns=['customer', 'cart', 'arrival_time', 'departure_time', 'total_time', 'cart_wait', 'bread_wait', 'cheese_wait', 'grocery_list', 'item_count', 'route'])
        env.shop_info = pd.DataFrame(columns=["time", 'customers_in_store', 'cart_requestors','bread_requestors','cheese_requestors', 'checkout_requestors'])

        class Customer(sim.Component):
            def process(self):
                # Decide which route the customer will follow
                arrival_time = (env.now())  # Log the simulation time when the customer arrives
                if random.random() < 0.4:
                    self.route = env.route_1  # 40% follow route A-B-C-D-E-F-G
                else:
                    self.route = env.route_2  # 60% follow route B-C-D-E-A-F-G

                self.grocery_list = self.select_items()

                env.customers_in_store +=1

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
                        # print('bread counter occup is:', bread_counter.length.print)
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
                env.customers_in_store -= 1

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
                env.customers_info = pd.concat([env.customers_info, new_data], ignore_index=True)

            def select_items(self):
                # Generate a random number of items for each department (based on min, mode, and max data)
                grocery_list = {}
                for dep in self.route:
                    min_val, mode_val, max_val = env.departments_items[dep]
                    items_picked = int(sim.Triangular(min_val, max_val, mode_val).sample())
                    grocery_list[dep] = items_picked
                return grocery_list




        # Resources (initialize after creating the environment)
        cart = sim.Resource('Shopping cart', capacity=45)
        bread_counter = sim.Resource('Bread counter', capacity=4)
        cheese_counter = sim.Resource('Cheese counter', capacity=3)
        checkout_lanes = [sim.Queue(f'Checkout lane {i + 1}') for i in range(3)]  # 3 checkout lanes
        env.customers_in_store = 0


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

        # List to track customer count over time
        customer_count_over_time = []

        # Tracker component to log the number of customers in the store every 60 seconds
        class Tracker(sim.Component):
            def process(self):
                while True:
                    checkout_1 = len(checkout_lanes[0])
                    checkout_2 = len(checkout_lanes[1])
                    checkout_3 = len(checkout_lanes[2])
                    checkout_requestors = checkout_1 + checkout_2 + checkout_3
                    new_data = pd.DataFrame({
                        'time': [env.now()],
                        'customers_in_store': [env.customers_in_store],
                        'cart_requestors': [len(cart.requesters())],
                        'bread_requestors': [len(bread_counter.requesters())],
                        'cheese_requestors': [len(cheese_counter.requesters())],
                        'checkout_requestors': [checkout_requestors]

                    })
                    env.shop_info = pd.concat([env.shop_info, new_data], ignore_index=True)
                    yield self.hold(60)  # Log every 60 seconds

        ArrivalGenerator().activate()
        Tracker().activate()

        env.run(12 * 3600)  # Simulate for 12 hours
        shop_info_all.append(env.shop_info)
        customer_info_all.append(env.customers_info)

        env.reset_now()

    return shop_info_all, customer_info_all


# plot shop info during the run
def plot_shop_info(run_number, all_shop_info):
    df = all_shop_info[run_number]  # change number for different run

    # Function to convert simulation time (seconds) to clock time starting from 08:00
    def convert_time(sim_time):
        start_time = datetime(2024, 1, 1, 8, 0, 0)  # Simulation starts at 08:00
        return (start_time + timedelta(seconds=sim_time)).strftime('%H:%M')

    # Apply the convert_time function to the time column
    df['time_clock'] = df['time'].apply(convert_time)

    # Plotting the data with converted time
    plt.figure(figsize=(12, 8))
    hourly_times = [datetime(2024, 1, 1, hour, 0, 0).strftime('%H:%M') for hour in range(8, 21)]
    # Plot customers in store over time
    plt.plot(df['time_clock'], df['customers_in_store'], label='Customers in Store', color='blue')

    # Plot requestors for cart, bread, and cheese counters
    plt.plot(df['time_clock'], df['cart_requestors'], label='Cart Requestors', color='green')
    plt.plot(df['time_clock'], df['bread_requestors'], label='Bread Counter Requestors', color='orange')
    plt.plot(df['time_clock'], df['cheese_requestors'], label='Cheese Counter Requestors', color='red')
    plt.plot(df['time_clock'], df['checkout_requestors'], label='checkout Requestors', color='purple')

    # Adding labels and title
    plt.xlabel('Time (HH:MM)')
    plt.ylabel('Number of People')
    plt.title('Number of Customers in Store and Resource Requestors Over Time')
    plt.xticks(hourly_times, rotation=45)  # Rotate the x-axis labels for better readability
    plt.grid(True)
    plt.legend()

    # Show the plot
    plt.tight_layout()  # Adjust the layout so labels don’t overlap
    plt.show()
