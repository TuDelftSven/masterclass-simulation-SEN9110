import salabim as sim
import random
import math
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

from PIL.ImageColor import colormap


def simulation(replications, animation=True):
    # Lists that will hold all the data
    shop_info_all = pd.DataFrame()
    customer_info_all = []

    for i in range(replications):
        # Setting so that yield can be used
        sim.yieldless(False)
        print(f'Run number {i} with animation={animation} has begun')

        # Initialize the simulation environment
        env = sim.Environment()

        # Set seeds
        sim.random_seed(i)
        random.seed(i)

        # Define the departments and their item distributions (min, mode, max)
        env.departments_items = {
            'A': (4, 10, 22),  # Fruit & Vegetables
            'B': (0, 4, 9),  # Meat & Fish
            'C': (1, 4, 10),  # Bread
            'D': (1, 3, 11),  # Cheese & Dairy
            'E': (6, 17, 35),  # Canned & packed food
            'F': (2, 8, 19),  # Frozen foods
            'G': (1, 9, 20),  # Drinks
        }

        # Define routes
        env.route_1 = ['A', 'B', 'C', 'D', 'E', 'F', 'G']  # 40% follow this route
        env.route_2 = ['B', 'C', 'D', 'E', 'A', 'F', 'G']  # 60% follow this route

        # setting up dataframes for plotting and information gain
        env.customers_info = pd.DataFrame(
            columns=['customer', 'cart', 'arrival_time', 'departure_time', 'total_time', 'cart_wait', 'bread_wait',
                     'cheese_wait', 'grocery_list', 'item_count', 'route'])
        env.shop_info = pd.DataFrame(
            columns=["time", 'customers_in_store', 'cart_requestors', 'bread_requestors', 'cheese_requestors',
                     'checkout_requestors'])

        # Creation of the resources and queues
        cart = sim.Resource('Shopping cart', capacity=45)
        bread_counter = sim.Resource('Bread counter', capacity=4)
        cheese_counter = sim.Resource('Cheese counter', capacity=3)
        checkout_lanes = [sim.Queue(f'Checkout lane {i + 1}') for i in range(3)]  # 3 checkout lanes
        env.customers_in_store = 0

        # Trial of using store function to create the shop and aisles
        shop = sim.Store("Grocery Shop")
        dep_A = sim.Store("Fruit & Vegetable department")
        dep_A_aisle_1 = sim.Resource("Fruit & Vegetable Aisle 1", capacity=5)
        dep_A_aisle_2 = sim.Resource("Fruit & Vegetable Aisle 2", capacity=5)

        dep_B = sim.Store("Meat & Fish department")
        dep_B_aisle_1 = sim.Resource("Meat & Fish Aisle 1", capacity=5)
        dep_B_aisle_2 = sim.Resource("Meat & Fish Aisle 2", capacity=5)

        dep_E = sim.Store("Canned & Packed Food department")
        dep_E_aisle_1 = sim.Resource("Canned & Packed Food Aisle 1", capacity=5)
        dep_E_aisle_2 = sim.Resource("Canned & Packed Food Aisle 2", capacity=5)

        dep_F = sim.Store("Frozen Foods department")
        dep_F_aisle_1 = sim.Resource("Frozen Food Aisle 1", capacity=5)
        dep_F_aisle_2 = sim.Resource("Frozen Food Aisle 2", capacity=5)

        dep_G = sim.Store("Drinks department")
        dep_G_aisle_1 = sim.Resource("Drinks Aisle 1", capacity=5)
        dep_G_aisle_2 = sim.Resource("Drinks Aisle 2", capacity=5)

        env.department_map_aisles = {
            'A': [dep_A_aisle_1, dep_A_aisle_2],
            'B': [dep_B_aisle_1, dep_B_aisle_2],
            'E': [dep_E_aisle_1, dep_E_aisle_2],
            'F': [dep_F_aisle_1, dep_F_aisle_2],
            'G': [dep_G_aisle_1, dep_G_aisle_2]
        }

        env.department_map = {
            'A': [dep_A],
            'B': [dep_B],
            'E': [dep_E],
            'F': [dep_F],
            'G': [dep_G]
        }

        env.coords = {
            dep_A_aisle_1: [5, 13.5, 10, 18],
            dep_A_aisle_2: [13.5, 22, 10, 18],
            dep_B_aisle_1: [5, 13.5, 5, 10],
            dep_B_aisle_2: [13.5, 22, 5, 10],
            dep_E_aisle_1: [22, 27, 10, 22],
            dep_E_aisle_2: [27, 32, 10, 22],
            dep_F_aisle_1: [32, 35, 18, 22],
            dep_F_aisle_2: [35, 38, 18, 22],
            dep_G_aisle_1: [32, 35, 10, 18],
            dep_G_aisle_2: [35, 38, 10, 18],
            bread_counter: [1, 5, 12, 15],  # Single aisle
            cheese_counter: [1, 5, 15, 22],  # Single aisle
            "checkout": [32, 38, 5, 10]  # Checkout area
        }


        resources = [dep_A_aisle_1.requesters(), dep_A_aisle_2.requesters(), dep_B_aisle_1.requesters(),
                     dep_B_aisle_2.requesters(),
                     dep_E_aisle_1.requesters(), dep_E_aisle_2.requesters(), dep_F_aisle_1.requesters(),
                     dep_F_aisle_2.requesters(), bread_counter.requesters(),
                  cheese_counter.requesters(), cart.requesters()]

        queues = [checkout_lanes[0], checkout_lanes[1], checkout_lanes[2]]
        stores = [dep_A, dep_B, dep_E, dep_F, dep_G, shop]

        all = resources + queues + stores

        # Customer arrival rates per hour
        arrival_data = [
            (8, 30), (9, 80), (10, 110), (11, 90), (12, 80),
            (13, 70), (14, 80), (15, 90), (16, 100), (17, 120),
            (18, 90), (19, 40)
        ]

        # Setup of environment and variables are now done
        # Time to set up the customer classes and trackers

        class Customer(sim.Component):

            #The regular process of a customer shopping
            def process(self):

                # Let the Customer enter the store
                self.arrival_time = env.now()
                self.enter(shop)

                # Decide which route to take and which items to select
                if random.random() < 0.4:
                    self.route = env.route_1  # 40% follow route A-B-C-D-E-F-G
                else:
                    self.route = env.route_2  # 60% follow route B-C-D-E-A-F-G
                self.grocery_list = self.select_items()


                # Decide if the Customer will be using a Cart or not
                if random.random() < 0.8:
                    self.had_cart = True
                    yield self.request(cart)  # 80% of customers take a cart
                    self.speed = sim.Triangular(2,5,3).sample()
                    self.speed = self.speed / 3.6
                else:
                    self.had_cart = False
                    self.speed = sim.Uniform(4,5).sample()
                    self.speed = self.speed / 3.6

                # everyone starts at the location of the carts.
                # Location is given in (x,y)
                self.location = [25,5]

                # Start walking the route and getting groceries
                for dep, items in self.grocery_list.items():
                    # If not bread or cheese with their counters
                    if dep not in ["C", "D"]:
                        t = env.now()
                        half = items // 2
                        department = env.department_map.get(dep, [])[0]
                        self.enter(department)
                        aisles = env.department_map_aisles.get(dep, [])
                        choosen_aisle = min(aisles, key=lambda aisle: aisle.claimers())
                        for aisle, coords in env.coords.items():
                            if aisle is choosen_aisle:
                                x_min = coords[0]
                                x_max = coords[1]
                                y_min = coords[2]
                                y_max = coords[3]


                        for aisle in aisles:
                            if aisle is not choosen_aisle:
                                other_aisle = aisle

                        # Walk to aisle
                        x_mod = (x_max + x_min) / 2
                        y_mod = (y_max + y_min) / 2
                        x = sim.Triangular(x_min, x_max, x_mod).sample()
                        y = sim.Triangular(y_min, y_max, y_mod).sample()
                        yield self.hold(self.distance_to_time(x, y))

                        # Customer with cart takes 2 spaces in an aisle instead of 1
                        if self.isclaiming(cart):
                            yield self.request((choosen_aisle, 1))
                        else:
                            yield self.request((choosen_aisle,0)) #People with baskets can walk freely so no blockade

                        #Walk in aisle and picking items
                        for n in range(half):
                            x_mod = (x_max + x_min)/2
                            y_mod = (y_max + y_min)/2
                            x = sim.Triangular(x_min, x_max, x_mod).sample()
                            y = sim.Triangular(y_min, y_max, y_mod).sample()
                            yield self.hold(self.distance_to_time(x, y))
                            yield self.hold(sim.Uniform(17, 27).sample()) #Lowered pick-up time from 20:30 to 17:27 because of separate walking which has average of 4.4 but that includes walking between departments as well
                        self.release(choosen_aisle)

                        #walk to other aisle in department
                        for aisle, coords in env.coords.items():
                            if aisle is other_aisle:
                                x_min = coords[0]
                                x_max = coords[1]
                                y_min = coords[2]
                                y_max = coords[3]
                        x_mod = (x_max + x_min) / 2
                        y_mod = (y_max + y_min) / 2
                        x = sim.Triangular(x_min, x_max, x_mod).sample()
                        y = sim.Triangular(y_min, y_max, y_mod).sample()
                        yield self.hold(self.distance_to_time(x, y))

                        if self.isclaiming(cart):
                            yield self.request((other_aisle, 1))
                        else:
                            yield self.request((other_aisle, 0))
                        for n in range(half):
                            x_mod = (x_max + x_min) / 2
                            y_mod = (y_max + y_min) / 2
                            x = sim.Triangular(x_min, x_max, x_mod).sample()
                            y = sim.Triangular(y_min, y_max, y_mod).sample()
                            yield self.hold(self.distance_to_time(x, y))
                            yield self.hold(sim.Uniform(17, 27).sample())
                        self.release(other_aisle)
                        self.leave(department)


                    # Now for the bread department
                    elif dep in "C" and items != 0:

                        #walk to bread department
                        for aisle, coords in env.coords.items():
                            if aisle is bread_counter:
                                x_min = coords[0]
                                x_max = coords[1]
                                y_min = coords[2]
                                y_max = coords[3]
                        x_mod = (x_max + x_min) / 2
                        y_mod = (y_max + y_min) / 2
                        x = sim.Triangular(x_min, x_max, x_mod).sample()
                        y = sim.Triangular(y_min, y_max, y_mod).sample()
                        yield self.hold(self.distance_to_time(x, y))

                        yield self.request(bread_counter)
                        bread_6 = math.ceil(items/6)
                        for n in range(bread_6):
                            yield self.hold(sim.Uniform(100,140))
                        self.release(bread_counter)


                    # Now for Cheese department
                    elif dep == "D" and items != 0:
                        #walk to cheese
                        for aisle, coords in env.coords.items():
                            if aisle is cheese_counter:
                                x_min = coords[0]
                                x_max = coords[1]
                                y_min = coords[2]
                                y_max = coords[3]
                        x_mod = (x_max + x_min) / 2
                        y_mod = (y_max + y_min) / 2
                        x = sim.Triangular(x_min, x_max, x_mod).sample()
                        y = sim.Triangular(y_min, y_max, y_mod).sample()
                        yield self.hold(self.distance_to_time(x, y))

                        yield self.request(cheese_counter)
                        cheese_6 = math.ceil(items / 6)
                        for n in range(cheese_6):
                            yield self.hold(sim.Uniform(50,70))
                        self.release(cheese_counter)

                # walk to checkout
                for aisle, coords in env.coords.items():
                    if aisle == "checkout":
                        x_min = coords[0]
                        x_max = coords[1]
                        y_min = coords[2]
                        y_max = coords[3]
                x_mod = (x_max + x_min) / 2
                y_mod = (y_max + y_min) / 2
                x = sim.Triangular(x_min, x_max, x_mod).sample()
                y = sim.Triangular(y_min, y_max, y_mod).sample()
                yield self.hold(self.distance_to_time(x, y))


                # picking checkout based on items and length
                expected_time_checkout = []
                for checkout in checkout_lanes:
                    sum = 0 #amount of items in basked
                    for person in checkout:
                        for value in person.grocery_list.values():
                            sum += value
                    expected_time_checkout.append(sum * 1.1 + 50 * checkout.length())
                checkout_line = checkout_lanes[expected_time_checkout.index(min(expected_time_checkout))]


                self.enter(checkout_line)
                item_count = 0
                for dep, item in self.grocery_list.items():
                    item_count += item
                if random.random() < 0.05:
                    yield self.hold(sim.Exponential(12).sample())
                if random.random() < 0.02:
                    yield self.hold(sim.Uniform(30,45).sample())
                yield self.hold(item_count * 1.1 + sim.Uniform(40, 60).sample())  # Scanning & payment
                self.leave(checkout_line)

                # Walk to cart/exit
                yield self.hold(self.distance_to_time(25, 5)) #coords of cart location

                if self.isclaiming(cart):
                    self.release(cart)
                self.leave(shop)

            # The process of giving a Customer a grocery list
            def select_items(self):
                # Generate a random number of items for each department (based on min, mode, and max data)
                grocery_list = {}
                for dep in self.route:
                    min_val, mode_val, max_val = env.departments_items[dep]
                    items_picked = int(sim.Triangular(min_val, max_val, mode_val).sample())
                    grocery_list[dep] = items_picked
                return grocery_list


            # from docs to animate object
            def animation_objects(self, id):
                '''
                the way the component is determined by the id, specified in AnimateQueue
                'text' means just the name
                any other value represents the colour
                '''
                if id == 'text':
                    ao0 = sim.AnimateText(text=self.name(), textcolor='fg', text_anchor='nw')
                    return 0, 16, ao0
                else:
                    ao0 = sim.AnimateRectangle((-5, 0, 2, 20),
                                               fillcolor=id, textcolor='white', arg=self)
                    return 9, 0, ao0

            def distance_to_time(self,x2,y2):
                distance = math.sqrt((x2 - self.location[0]) ** 2 + (y2 - self.location[1]) ** 2)
                walking_time = distance / self.speed
                self.location = [x2,y2] # Update location
                return walking_time


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

        # This trackers logs data every 60 sec in case you want to use this data for graphs
        class Tracker(sim.Component):
            def process(self):
                row = 0
                env.customer_df = pd.DataFrame()
                while True:
                    time = env.now()
                    env.customer_df.loc[row,'time'] = time
                    for item in all:
                        env.customer_df.loc[row, f'{item}'] = item.length()
                    yield self.hold(60)  # Log every 60 seconds
                    row += 1

        # The code to activate the simulation
        ArrivalGenerator().activate()
        Tracker().activate()

        # Total time is 45900 so animation now takes roughly 45 sec
        env.speed(1028)
        env.background_color('20%gray')

        # Animation
        # Checkout lanes
        qa0 = sim.AnimateQueue(checkout_lanes[0], x=100, y=20, title='Checkout lane 0', direction='e', id='blue')
        qa1 = sim.AnimateQueue(checkout_lanes[1], x=100, y=60, title='Checkout lane 1', direction='e', id='blue')
        qa2 = sim.AnimateQueue(checkout_lanes[2], x=100, y=100, title='Checkout lane 2', direction='e', id='blue')

        # Bread_counter
        b0 = sim.AnimateQueue(bread_counter.requesters(), x=100, y=140, title='Bread counter queue', direction='e', id='red')

        # Cheese_counter
        c0 = sim.AnimateQueue(cheese_counter.requesters(), x=100, y=180, title='Cheese counter queue', direction='e', id='yellow')

        # cart queue
        cart0 = sim.AnimateQueue(cart.requesters(), x=100, y=220, title='Cart queue', direction='e', id='green')

        # List of all aisles
        aisles = [
            dep_A_aisle_1,
            dep_A_aisle_2,
            dep_B_aisle_1,
            dep_B_aisle_2,
            dep_E_aisle_1,
            dep_E_aisle_2,
            dep_F_aisle_1,
            dep_F_aisle_2
        ]

        # Starting y value for the first queue
        y_value = 260

        # Generating the AnimateQueue for each aisle with a 40 increment in y value
        for aisle in aisles:
            sim.AnimateQueue(aisle.requesters(), x=100, y=y_value, title=f'{aisle.name()} Queue', direction='e', id='purple')
            y_value += 40  # Increment y value by 40 for the next aisle queue


        # departments
        d0 = sim.AnimateText(text=lambda: f"People in Fruit & Vegetables department: {dep_A.length()}",
                x=500, y=300, fontsize=12)
        d1 = sim.AnimateText(text=lambda: f"People in Meat & Fish department: {dep_B.length()}",
                             x=500, y=330, fontsize=12)
        a0 = sim.AnimateText(text=lambda: f"People in Canned & packed food department: {dep_E.length()}",
                             x=500, y=210, fontsize=12)
        a0 = sim.AnimateText(text=lambda: f"People in Frozen Foods department: {dep_F.length()}",
                             x=500, y=240, fontsize=12)
        a0 = sim.AnimateText(text=lambda: f"People in Drinks department: {dep_G.length()}",
                             x=500, y=270, fontsize=12)

        sim.AnimateMonitor(shop.length, x=500, y=440, width=400, height=100, horizontal_scale=0.0125, vertical_scale=0.8,
                           title= 'Customer in Shop')

        sim.AnimateText(text=lambda: f"People in Shop: {shop.length()}",
                        x=500, y=420, fontsize=12)

        sim.AnimateMonitor(shop.length_of_stay, x=500, y=600, width=400, height=100, horizontal_scale=0.0125,
                           vertical_scale=0.020, title="Shop duration per Customer")
        sim.AnimateText(text=lambda: f"Average shopping time: {shop.length_of_stay.mean()}",
                        x=500, y=570, fontsize=12)

        env.animate(animation)
        env.modelname('Grocery store animation')


        env.run(12.75 * 3600)  # Simulate for 12 hours + 45 mins without people entering just leaving

        # Creating mean, max and 95 percentile shop information for this run
        for queue in all:
            shop_info_all.loc[i, f'{queue} mean length of stay'] = queue.length_of_stay.mean()
            shop_info_all.loc[i, f'{queue} max length of stay'] = queue.length_of_stay.mean()
            shop_info_all.loc[i, f'{queue} 95% percentile length of stay'] = queue.length_of_stay.percentile(95)

        # Creating customer_df from the tracker
        customer_info_all.append(env.customer_df)

        # Resetting the environmental variables
        env.reset_now()

    return shop_info_all, customer_info_all
