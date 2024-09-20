from assignment_1 import simulation, plot_shop_info
import pandas as pd


#Run the simulation with x replications
#Provinding 2 separate lists of dataframes containing different variables
replications = 10
all_shop_info_list, all_customer_info_list = simulation(replications)

#Plot the amount of shoppers in queues and in the store during the day for a specific run
run_number = 0
plot_shop_info(run_number, all_shop_info_list)

#Creating full customer dataframe instead of list of dataframes
customer_df = all_customer_info_list[0]
for df in all_customer_info_list:
    if df is not all_customer_info_list[0]:
        customer_df = pd.concat([customer_df, df], ignore_index=True)

#Calculating and printing the mean, max and 95% confidence interval of all runs and all queues
for column in range(4,8):
    std = customer_df.iloc[:, column].std()
    n = customer_df.iloc[:, column].count()
    se = std / (n ** 0.5)
    margin_of_error = 1.96 * se
    lower_bound = customer_df.iloc[:, column].mean() - margin_of_error
    upper_bound = customer_df.iloc[:, column].mean() + margin_of_error
    print(f" {customer_df.columns[column]}\n Average {customer_df.iloc[:, column].mean()}\n Max "
          f"{customer_df.iloc[:, column].max()}\n lower_bound {lower_bound}\n upper_bound {upper_bound}\n")


