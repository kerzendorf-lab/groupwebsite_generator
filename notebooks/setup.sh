#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")/../../kerzendorf-group.github.io"
rm -rf index.html Research.html Contact.html People.html Support.html News.html
rm -rf assets website_files members sub_research support_images news

mkdir members sub_research news

cp -r ../group-data/website_data/website_files ./
cp -r ../groupwebsite_generator/assets ./

rsync -av --exclude '*.json' --exclude 'jsons' ../group-data/members/ ./members
