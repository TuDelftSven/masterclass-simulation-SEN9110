from assignment_1 import simulation, plot_shop_info
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

all_shop_info, all_customer_info = simulation(10)

plot_shop_info(9, all_shop_info)
