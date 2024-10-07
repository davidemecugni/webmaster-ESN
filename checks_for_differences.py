# Parameters
from parameters import parameters
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json



def convert_sets_to_lists(data):
    if isinstance(data, dict):
        return {key: convert_sets_to_lists(value) for key, value in data.items()}
    elif isinstance(data, set):
        return list(data)
    elif isinstance(data, list):
        return [convert_sets_to_lists(element) for element in data]
    else:
        return data
    
def replace_multiple_spaces_with_single_space(string):
    """Replace multiple spaces with a single space and capitalize the first letter of each word."""
    string = string.strip().encode('utf-8').decode('utf-8')
    return ' '.join([word.capitalize() for word in string.split()])

def fix_names(d):
    """Fix the names in the dictionary."""
    for category in d:
        d[category] = [replace_multiple_spaces_with_single_space(name) for name in d[category] if "ESN" not in name.upper()]
    return d

def equal_names(name1, name2):
    """Check if two names are different. Consider 2 names equal if they share 2 names out of 3."""
    name1 = name1.split()
    name2 = name2.split()
    if len(name1) != 2 or len(name2) != 2:
        shared_names = 0
        for name in name1:
            if name in name2:
                shared_names += 1
        return shared_names >= 2
    else:
        return name1 == name2

def fetch_members_from_website():
    url = parameters["website"]
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    members = {
        "board": [],
        "esners": [],
        "alumni": []
    }

    sections = {
        f"Board {parameters['year']}-{parameters['year']+1}": "board",
        "Membri attivi": "esners",
        "Alumni": "alumni"
    }

    for section_title, key in sections.items():
        section = soup.find('h2', text=section_title)
        if section:
            divs = section.find_next_siblings('div', style=True)
            for div in divs:
                name_tag = div.find('h3')
                if name_tag:
                    name = name_tag.contents[0].strip()
                    members[key].append(name)
                name_tag = div.find('h4')
                if name_tag:
                    name = name_tag.contents[0].strip()
                    members[key].append(name)

    added_members = set()
    unique_members_dict = {
        "board": [],
        "esners": [],
        "alumni": []
    }
    # Iterate through categories in order of priority
    for category in ["alumni", "esners", "board"]:
        for member in members[category]:
            if member not in added_members:
                unique_members_dict[category].append(member)
                added_members.add(member)

    return fix_names(unique_members_dict)

def fetch_members_from_xlsx():
    path = './members/members.xlsx'
    # Read the Excel file
    xls = pd.ExcelFile(path)
    
    # Read the ESNER and ALUMNI sheets
    esner_df = pd.read_excel(xls, sheet_name='ESNER')
    alumni_df = pd.read_excel(xls, sheet_name='ALUMNO')
    
    members = {
        "esners": [],
        "alumni": []
    }
    
    # Extract names from ESNER table
    for index, row in esner_df.iterrows():
        full_name = f"{row['First Name']} {row['Last Name']}"
        members["esners"].append(full_name)
    
    # Extract names from ALUMNI table
    for index, row in alumni_df.iterrows():
        full_name = f"{row['First Name']} {row['Last Name']}"
        members["alumni"].append(full_name)
    
    return fix_names(members)

def find_differences(members_from_website, members_from_xlsx):
    differences = {
        "esners": set(),
        "alumni": set(),
    }

    # Puts missing members, that are in the website but not in the xlsx, in the differences set
    # Members from the xlsx are considered the source of truth
    
    for category in ["esners", "alumni"]:
        for member in members_from_xlsx[category]:
            found = False
            for website_member in members_from_website[category]:
                if equal_names(member, website_member):
                    found = True
                    break
            if not found:
                differences[category].add(member)

    return differences
    
if __name__ == '__main__':
    """Compare the members from Jupiter(through excel) with the members from the website.
    .xlsx IS THE SOURCE OF TRUTH.
    Save the differences in a json file."""
    members_from_website = fetch_members_from_website()
    members_from_xlsx = fetch_members_from_xlsx()

    # Add board members to esners
    members_from_website["esners"].extend(members_from_website["board"])
    board = members_from_website["board"]
    del members_from_website["board"]

    differences = find_differences(members_from_website, members_from_xlsx)
    for category in differences:
        print(f"{category}:")
        for member in differences[category]:
            if member in board:
                print(f"{member} (board member)")
            else:
                print(f"{member}")
        print()

    # Save all data in json file
    with open('./data/differences.json', 'w') as f:
        json.dump(convert_sets_to_lists(differences), f, indent=4)
    with open('./data/members_from_website.json', 'w') as f:
        json.dump(convert_sets_to_lists(members_from_website), f, indent=4)
    with open('./data/members_from_xlsx.json', 'w') as f:
        json.dump(convert_sets_to_lists(members_from_xlsx), f, indent=4)

    

