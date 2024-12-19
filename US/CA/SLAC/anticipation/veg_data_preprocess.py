import pandas as pd
import sys

def extract_poles() :
	input_file_name = sys.argv[1]
	output_file_name = sys.argv[2]

	df = pd.read_csv(input_file_name)

	# Create a new DataFrame with only rows where 'class' is 'pole'
	filtered_df = df[df['class'] == 'pole']

	# Reset the index of the filtered DataFrame
	filtered_df.reset_index(drop=True, inplace=True)

	# Extract 'pole_length' from the corresponding 'pole_configuration' rows
	pole_length_map = dict(zip(df[df['class'] == 'pole_configuration']['name'], df[df['class'] == 'pole_configuration']['pole_length']))

	# Map 'pole_length' values based on 'class' using .map after creating a copy
	filtered_df = filtered_df.copy()  # Create a copy to avoid SettingWithCopyWarning

	filtered_df['pole_length'] = filtered_df['configuration'].map(pole_length_map)

	# Check for missing values in latitude and longitude columns and drop rows with any missing value
	filtered_df.dropna(subset=["latitude", "longitude"], inplace=True)

	# Reset the index
	filtered_df.reset_index(drop=True, inplace=True)

	# Display the final DataFrame
	filtered_df.to_csv(output_file_name, index=False)


if __name__ == "__main__":
	extract_poles()