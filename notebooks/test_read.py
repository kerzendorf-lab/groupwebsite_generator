#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Change the working directory to the desired location
# temporary, only for local
import os
#os.chdir("/home/bumblebealu/groupwebsite_generator/")
os.chdir("/Users/harshul/website clone/harshul/test/groupwebsite_generator")
os.getcwd()


# In[2]:


import pandas as pd
from pathlib import Path
import json


# In[6]:


MEMBERS_DIR_PATH = Path('../group-data/members/')


# In[14]:


member_records = []
for member_dir in MEMBERS_DIR_PATH.glob('*'):
    member_record = json.load(open(member_dir / 'info.json'))
    member_json_dir = member_dir / 'jsons'
    
    if (member_experience := (member_json_dir /  'experiences.json')).exists():
        current_position = json.load(open(member_experience))[-1]
        
    elif (member_education := (member_json_dir /  'education.json')).exists():
        current_position = json.load(open(member_education))[-1]

    elif (member_awards := (member_json_dir /  'awards.json')).exists():
        current_position = json.load(open(member_awards))[-1]
    elif (member_roles := (member_json_dir /  'roles.json')).exists():
        current_position = json.load(open(member_roles))[-1]
    elif (member_projects := (member_json_dir /  'projects.json')).exists():
        current_position = json.load(open(member_projects))[-1]   

    elif (member_website_media := (member_json_dir /  'website_media.json')).exists():
        current_position = json.load(open(member_website_media))[-1]
    elif (member_posters := (member_json_dir /  'posters.json')).exists():
        current_position = json.load(open(member_posters))[-1]
    elif (member_publications := (member_json_dir /  'publications.json')).exists():
        current_position = json.load(open(member_website_media))[-1]
    elif (member_outreach := (member_json_dir /  'outreach.json')).exists():
        current_position = json.load(open(member_outreach))[-1]



    member_record.update(current_position)
    member_records.append(member_record)


# In[16]:


current_position


# In[18]:


pd.DataFrame.from_records(member_records)


# In[ ]:




