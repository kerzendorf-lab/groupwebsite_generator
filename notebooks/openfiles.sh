#!/bin/bash

# Path to the folder containing the group data
group_data_folder="../../group-data"

# Find all the basic_info.json files
json_files=$(find "$group_data_folder/members" -type f -name "experiences.json")

# Check if any files were found
if [[ -z $json_files ]]; then
  echo "No basic_info.json files found."
  exit 1
fi

# Open each json file in Visual Studio Code
for file in $json_files; do
  code "$file"
done

exit 0
