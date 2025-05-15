import pandas as pd

# Load the CSV file containing IPs
ips_to_subnets = pd.read_csv('/Users/pb/Downloads/IPs_to_subnets.csv')

# Add /24 to each IP address
ips_to_subnets['IP'] = ips_to_subnets['IP'].apply(lambda x: f"{x}/23")

# Save the transformed data to a new CSV file
ips_to_subnets.to_csv('/Users/pb/Downloads/IPs_with_subnets.csv', index=False)

print("Transformation complete. New file saved to '/Users/Downloads/IPs_with_subnets.csv'.")

