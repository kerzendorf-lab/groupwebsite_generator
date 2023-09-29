#!/usr/bin/env python
# coding: utf-8

# ### This notebook consist of code for creating the html files for the website each time data is updated.

# ##### Set-up

# In[191]:


# Change the working directory to the desired location
# temporary, only for local
import os
#os.chdir("/home/bumblebealu/groupwebsite_generator/")
os.chdir("/Users/harshul/website clone/harshul/test/groupwebsite_generator")
os.getcwd()


# In[192]:


#Importing classes from the Jinja2 library to load and render templates.
import json
import os
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import UndefinedError


# In[193]:


#Function for creating proper html file names
def page_link(a):
    if ' ' in a:
        return a.replace(' ', '_')
    else:
        return a


# In[194]:


import os
import json

class MemberData:
    def __init__(self, member_id):
        self.member_id = member_id
        self.jsons_path, self.member_dir = self._find_jsons_path_and_member_dir(member_id)

    def _find_jsons_path_and_member_dir(self, member_id):
        members_dir = "../group-data/members/"

        for dir_name in os.listdir(members_dir):
            dir_path = os.path.join(members_dir, dir_name)
            if os.path.isdir(dir_path):
                jsons_dir = os.path.join(dir_path, "jsons")
                info_file = os.path.join(dir_path, "info.json")
                if os.path.isfile(info_file):
                    with open(info_file, "r") as f:
                        info = json.load(f)
                    if info.get("id") == member_id:
                        return jsons_dir, dir_path
        return "Couldn't find {member_id}", None

    def _load_json(self, json_file):
        file_path = os.path.join(self.jsons_path, json_file)
        with open(file_path, "r") as f:
            data = json.load(f)
        return data

    def info(self):
        info_file = os.path.join(self.member_dir, "info.json")
        with open(info_file, "r") as f:
            data = json.load(f)
        return data

    def __getattr__(self, name):
        if name in ["awards", "education", "experiences", "outreach", "projects", "roles", "social_links", "website_media", "publications"]:
            def method():
                return self._load_json(name + ".json")
            return method
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


# In[216]:


member=MemberData("harshul_gupta")
basic=member.experiences()
basic


# In[196]:


class ContentData:
    def __init__(self, article_id):
        self.article_id = article_id
        self.json_path = self._find_jsons_path(article_id)

    def _find_jsons_path(self, article_id):
        content_dir = "../group-data/website_data/content/"
        for file_name in os.listdir(content_dir):
            file_path = os.path.join(content_dir, file_name)
            if os.path.isfile(file_path):
                with open(file_path, "r") as f:
                    content_data = json.load(f)
                if content_data.get("article_id") == article_id:
                    return file_path

        raise ValueError(f"Article ID '{article_id}' not found.")

    def load_json(self):
        with open(self.json_path, "r") as f:
            data = json.load(f)
        return data


# In[197]:


#Creating an instance of the Environment class that looks for templates. Page_link is set to the global variable so that it can be accessed by all templates
environment = Environment(loader=FileSystemLoader('templates/'),extensions=['jinja2.ext.loopcontrols'])
environment.globals['page_link'] = page_link
environment.globals['MemberData'] = MemberData
environment.globals['ContentData'] = ContentData


# In[198]:


people_id_data = {"id": [], "category": []}
non_mem_data = {"id": [], "category": []}
members_directory = '../group-data/members/'

for member_dir in os.listdir(members_directory):
    member_path = os.path.join(members_directory, member_dir)
    if os.path.isdir(member_path):
        jsons_directory = os.path.join(member_path, 'jsons')
        if os.path.isdir(jsons_directory):
            for json_file in os.listdir(jsons_directory):
                if json_file == 'info.json':
                    json_path = os.path.join(jsons_directory, json_file)
                    with open(json_path, 'r') as file:
                        info = json.load(file)
                        if info.get('display') and info['display'].get('kg'):
                            if info['display']['kg']:
                                people_id_data['id'].append(info.get('id'))
                                people_id_data['category'].append(info.get('category'))
                        else:
                            non_mem_data['id'].append(info.get('id'))
                            non_mem_data['category'].append(info.get('category'))

people_df = pd.DataFrame(people_id_data)
non_mem_df = pd.DataFrame(non_mem_data)

sorting_order = [
    "Faculty", "Postdoctoral Researchers", "Graduate Students",
    "Undergraduate Students", "Researchers", "Research Software Engineers"
]

people_df['sorting_order'] = people_df['category'].apply(lambda x: sorting_order.index(x) if x in sorting_order else -1)
people_df = people_df.sort_values(['sorting_order', 'id'], ascending=[True, True])
people_df.drop('sorting_order', axis=1, inplace=True)


# In[199]:


content_id_data = {"article_id": [], "category": [], "date": [], "tags": []}
content_directory = '../group-data/website_data/content'

for json_file in os.listdir(content_directory):
    if json_file.endswith('.json'):
        json_path = os.path.join(content_directory, json_file)
        with open(json_path, 'r') as file:
            info = json.load(file)
            if info.get('display'):
                content_id_data['article_id'].append(info.get('article_id'))
                content_id_data['category'].append(info.get('category'))
                content_id_data['date'].append(info.get('article_date'))
                content_id_data['tags'].append(info.get('tags'))

content_df = pd.DataFrame(content_id_data)
content_df['date'] = pd.to_datetime(content_df['date'], format='%m-%d-%Y')
content_df = content_df.groupby('category').apply(lambda x: x.sort_values('date', ascending=False)).reset_index(drop=True)


# In[200]:


research_content_unsorted = content_df[content_df['tags'].apply(lambda x: any('research' in tag for tag in x))]
research_content = research_content_unsorted.groupby('category').apply(lambda x: x.sort_values('date', ascending=False)).reset_index(drop=True)


# In[201]:


news_content_unsorted = content_df[content_df['tags'].apply(lambda x: any('news' in tag for tag in x))]
news_content = news_content_unsorted.sort_values(by="date", ascending=False)


# In[202]:


latest_content_df = pd.DataFrame()

for category in content_df.category.unique():
    latest_data = pd.Series(content_df[content_df.category == category].iloc[0])
    latest_content_df = latest_content_df._append(latest_data, ignore_index=True)

latest_content_df['date'] = pd.to_datetime(latest_content_df['date'], format='%m-%d-%Y')
latest_content_df = latest_content_df.sort_values(by='date', ascending=False)


# In[203]:


json_files = ['general', 'homepage', 'research', 'support', 'contact']
data = {}

for json_file in json_files:
    try:
        with open(f"../group-data/website_data/{json_file}.json") as json_var:
            data[json_file] = json.load(json_var)
    except (FileNotFoundError, json.JSONDecodeError):
        pass


# ##### Homepage

# In[204]:


homepage_template = environment.get_template('homepage.html.j2')


# In[205]:


homepage_content = \
    homepage_template.render(general=data['general'],
                             homepage=data['homepage'],
                             recent_content=latest_content_df.to_dict(orient='records'))


# In[206]:


with open('../kerzendorf-group.github.io/index.html', mode='w', encoding='utf-8') as Homepage:
    Homepage.write(homepage_content)


# ##### People Page

# In[207]:


people_template = environment.get_template("people.html.j2")


# In[208]:


people_content = people_template.render(general=data["general"], 
                                        members=people_df['id'])


# In[209]:


with open("../kerzendorf-group.github.io/People.html", mode="w", encoding="utf-8") as people:
    people.write(people_content)


# ##### Individual People Page

# In[210]:


ind_person_template = environment.get_template("individual_person.html.j2")


# In[211]:


for person in people_df['id']:
            filename = f"../kerzendorf-group.github.io/members/{ person }/{ person }.html"
            ind_person_content = ind_person_template.render(general=data["general"], 
                                                            member_id=person, 
                                                            content=content_df.to_dict(orient='records'))
            with open(filename, mode="w", encoding="utf-8") as page:
                page.write(ind_person_content)


# ##### Research Page

# In[212]:


research_template = environment.get_template("research.html.j2")


# In[213]:


main_page_research_content = research_template.render(general=data["general"],
                                            content=research_content)


# In[ ]:


with open("../kerzendorf-group.github.io/Research.html", mode="w", encoding="utf-8") as research:
        research.write(main_page_research_content)


# In[ ]:


sub_research_template = environment.get_template("sub_research_frontpage.html.j2")


# In[ ]:


for category in content_df.loc[content_df.category != "News", "category"].unique():
        sub_research_content = sub_research_template.render(general=data["general"], 
                                                            research_general=data["research"], 
                                                            content = research_content,
                                                            category = category
                                                            )
        folder_path = f"../kerzendorf-group.github.io/sub_research/{page_link(category.lower())}"
        os.makedirs(folder_path, exist_ok=True)
        with open(f"../kerzendorf-group.github.io/sub_research/{page_link(category.lower())}.html", mode="w", encoding="utf-8") as sub_research:
            sub_research.write(sub_research_content)


# ##### Individual Research Page

# In[ ]:


template_no_twitter = environment.get_template("research_page_no_twitter.html.j2")


# In[ ]:


for ind_research_keys, ind_research_values in research_content.iterrows():
    if "news" not in ind_research_values.category.lower():
        ind_research_content = template_no_twitter.render(general=data["general"], 
                                                          member_ids = people_df['id'],
                                                          nonmem_ids = non_mem_df['id'],
                                                          content = ind_research_values
                                                          
                                                            )
        folder_path = f"../kerzendorf-group.github.io/sub_research/{page_link(ind_research_values.category.lower())}"
        os.makedirs(folder_path, exist_ok=True)
        with open(f"{ folder_path }/{page_link(ind_research_values.article_id.lower())}.html", mode="w", encoding="utf-8") as ind_research_page:
            ind_research_page.write(ind_research_content)


# ##### News Page

# In[ ]:


news_content


# In[ ]:


news_template = environment.get_template("news.html.j2")


# In[ ]:


news_page_content = news_template.render(general=data["general"],
                                         content=news_content,
                                         member_ids=people_df['id'],
                                         nonmem_ids = non_mem_df['id'],
                                         category="News")


# In[ ]:


with open("../kerzendorf-group.github.io/News.html", mode="w", encoding="utf-8") as news:
        news.write(news_page_content)


# ##### Individual News Pages

# In[ ]:


news_template_no_twitter = environment.get_template("news_page_no_twitter.html.j2")
#news_template_twitter = environment.get_template("news_page_twitter.html.j2")


# In[ ]:


for ind_news_keys, ind_news_values in news_content.iterrows():
        ind_news_content = news_template_no_twitter.render(general=data["general"], 
                                                          member_ids = people_df['id'],
                                                          nonmem_ids = non_mem_df['id'],
                                                          content = ind_news_values
                                                            )
        folder_path = f"../kerzendorf-group.github.io/news/"
        os.makedirs(folder_path, exist_ok=True)
        with open(f"{ folder_path }/{page_link(ind_news_values.article_id.lower())}.html", mode="w", encoding="utf-8") as ind_news_page:
            ind_news_page.write(ind_news_content)


# ##### Support Page

# In[ ]:


support_template = environment.get_template('support.html.j2')


# In[ ]:


support_content = support_template.render(general=data["general"], support=data["support"])


# In[ ]:


with open('../kerzendorf-group.github.io/Support.html', mode='w', encoding='utf-8') as support:
    support.write(support_content)


# ##### Contact

# In[ ]:


contact_template = environment.get_template('contact.html.j2')


# In[ ]:


contact_content = contact_template.render(general=data["general"], contact=data["contact"])


# In[ ]:


with open('../kerzendorf-group.github.io/Contact.html', mode='w', encoding='utf-8') as contact:
    contact.write(contact_content)

