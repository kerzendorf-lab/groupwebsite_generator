#!/bin/bash

members_folder="../../group-data/members"


for folder in "$members_folder"/*; do
    if [ -d "$folder" ]; then  # if it is a directory
        folder_name=$(basename "$folder")
        json_file="$folder/$folder_name.json"
        

        if [ -f "$json_file" ]; then
            rm "$json_file"
            echo "Deleted $json_file"
        fi
    fi
done

cd ../../group-data
rm -rf members/common
rm -rf website_data/research/sub_research_data/combined
rm -rf website_data/news/combined_news.json
rm -rf website_data/people_list.json