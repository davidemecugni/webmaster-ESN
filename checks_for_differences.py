# Parameters
from parameters import parameters
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from termcolor import colored
from dateutil.easter import easter
import requests
import pandas

def get_italian_joke(subtype=None):
    """
    Recupera una battuta dall'API Italian Jokes.
    
    Parametri:
      subtype (str, opzionale): specifica il sottotipo di battuta da ottenere.
         I sottotipi disponibili sono: All, One-liner, Observational, Stereotype, Wordplay, Long.
         Ad esempio: subtype="One-liner"
         
    Restituisce:
      Il testo della battuta, oppure un messaggio d'errore in caso di problemi.
    """
    base_url = "https://italian-jokes.vercel.app/api/jokes"
    params = {}
    if subtype:
        params["subtype"] = subtype

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        # La risposta JSON ha il seguente formato:
        # {
        #    "id": 1,
        #    "joke": "Why did the Mafia cross the road? Forget about it.",
        #    "type": "Italian",
        #    "subtype": "One-liner"
        # }
        data = response.json()
        joke = data.get("joke", "Nessuna battuta trovata.")
        return joke
    except requests.RequestException as e:
        return f"Errore durante il recupero della battuta: {e}"

    
def prGreen(skk): print("\033[92m {}\033[00m" .format(skk))
def prRed(skk): print("\033[91m {}\033[00m" .format(skk))


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
    url = parameters["website"] + 'about-us'
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
        section = soup.find('h2', string=section_title)
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
    # Find the most recent file in the members directory
    members_dir = './members/'
    files = [f for f in os.listdir(members_dir) if f.startswith('ESN ENEA Modena_complete') and f.endswith('.xlsx')]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(members_dir, x)), reverse=True)
    path = os.path.join(members_dir, files[0])

    # Calculate the file's age
    file_mod_time = datetime.fromtimestamp(os.path.getmtime(path))
    file_age = datetime.now() - file_mod_time

    # Print the file's age in green if less than 15 days old, otherwise in red
    if file_age < timedelta(days=15):
        print(colored(f"The file is {file_age.days} days old.", "green"))
    else:
        print(colored(f"The file is {file_age.days} days old.", "red"))
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

def find_differences_website_not_in_xlsx(members_from_website, members_from_xlsx):
    differences = {
        "esners": set(),
        "alumni": set(),
    }
    # Puts missing members, that are in the xlsx but not in the website, in the differences set
    # Members from the website are considered the source of truth
    for category in ["esners", "alumni"]:
        for member in members_from_website[category]:
            found = False
            for xlsx_member in members_from_xlsx[category]:
                if equal_names(member, xlsx_member):
                    found = True
                    break
            if not found:
                differences[category].add(member)
    return differences

# Generate message for WhatsApp
def generate_message(differences, board):
    festivity = nearest_festivity()
    message = f"Siete stati visitati dal 🧙‍♂️ webmaster🧙‍♂️\n"
    # Add welcome message in italian based on the daytime
    hour = datetime.now().hour
    if 8 < hour < 14:
        message += "Buongiorno🌞! \n"
    elif 14 <= hour < 18:
        message += "Buon pomeriggio🌞! \n"
    elif 19 <= hour < 22:
        message += "Buona sera🌜! \n"
    else:
        message += "Buona notte🌚! \n"
    if festivity:
        message += f"Buon{festivity}!\n"
    message += f"Battuta dal sapore italico: {get_italian_joke('One-liner')}\n"
    message += "Ai nuovi membri, se desiderate essere sul sito di ESN More nella page About https://modena.esn.it/?q=about-us\n"
    message += "Fornitemi una foto📸(possibilmente 640px640p, croppabile tipo con https://ucsc.github.io/web-tools/images/)\n"
    message += "Il webmaster tende a croppare☐ e stretchare i malcapitati che forniscono una foto non conforme 😈\n"
    message += "\nEcco i membri mancanti:\n"
    for category in differences:
        for member in differences[category]:
            if member in board:
                message += f"{member} board member\n"
            else:
                message += f"➡️ {member}\n"
    differences = differences["esners"].union(differences["alumni"])
    # Check if missing members from log file are present
    missing_members = get_last_log()
    if missing_members != "No log found.":
        good_members = [member for member in missing_members if member not in differences]
        print(missing_members)
        print(differences)
        if good_members:
            message += f"Sii un buon esner che manda le foto come {', '.join(good_members)}"
    message += "\nWebmaster🧙‍♂️\n"
    message += "email: webmaster@esnmore.it\n"
    message += "_messaggio assolutamente non autogenerato_\n"
    # Append missing members to log
    if differences:
        add_missing_members_to_log_file(differences)
    return message

def add_missing_members_to_log_file(differences):
    with open('./data/log_missing.txt', 'a') as f:
        f.write(f"{datetime.now()}: {differences}\n")

def get_last_log():
    with open('./data/log_missing.txt', 'r') as f:
        lines = f.readlines()
        if lines:
            last_log = lines[-1]
            # Convert the string representation of the set back to a list
            last_log_set = eval(last_log.split(": ", 1)[1])
            return list(last_log_set)
        else:
            return "No log found."

def nearest_festivity():
    today = datetime.today().date()
    festivities = {
        " Natale🎄": datetime(today.year, 12, 25),
        "a Pasqua🐣": easter(today.year),
        " Anno Nuovo🎆": datetime(today.year, 1, 1),
        " Capodanno🎉": datetime(today.year + 1, 1, 1),
        "a Epifania👑": datetime(today.year, 1, 6),
        "a Festa della Liberazione🇮🇹": datetime(today.year, 4, 25),
        "a Festa dei Lavoratori👷": datetime(today.year, 5, 1),
        "a Festa della Repubblica🇮🇹": datetime(today.year, 6, 2),
        "a Assunzione di Maria👼": datetime(today.year, 8, 15),
        " Ognissanti🕯️": datetime(today.year, 11, 1),
        "a Immacolata Concezione🙏": datetime(today.year, 12, 8),
        " ESN Day🌍": datetime(today.year, 10, 16),
        " Halloween🎃": datetime(today.year, 10, 31),
        " San Valentino❤️": datetime(today.year, 2, 14),
        "a Festa della Donna🌸": datetime(today.year, 3, 8),
        "a Festa del Papà👨": datetime(today.year, 3, 19),
        "a Festa della Mamma👩": datetime(today.year, 5, 9),
        "a Festa dei Nonni👴👵": datetime(today.year, 10, 2),
        "a Festa dei Bambini👶": datetime(today.year, 11, 20),
        "a Festa del Gatto🐱": datetime(today.year, 2, 17),
        "a Festa del Cane🐶": datetime(today.year, 10, 10),
    }

    min_festivity, delta = calculate_min_distance(today, festivities)
    print()
    return min_festivity if delta < 1 else min_festivity + "(circa)"

def calculate_min_distance(today_date, festivities):
    # Print type of today_date
    
    # Ensure today_date is a date object
    if isinstance(today_date, datetime):
        today_date = today_date.date()
    
    distances = {}
    for name, date in festivities.items():
        # Ensure date is a date object
        if isinstance(date, datetime):
            date = date.date()
        distances[name] = abs((date - today_date).days)
    
    nearest_festivity = min(distances, key=distances.get)
    return nearest_festivity, distances[nearest_festivity]


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
                prGreen(f"{member} (board member)")
            else:
                prGreen(f"{member}")
        print()

    differences_website_not_in_xlsx = find_differences_website_not_in_xlsx(members_from_website, members_from_xlsx)
    for category in differences_website_not_in_xlsx:
        print(f"{category}:")
        for member in differences_website_not_in_xlsx[category]:
            if member in board:
                prRed(f"{member} (board member)")
            else:
                prRed(f"{member}")
        print()

    # Save all data in json file
    with open('./data/differences.json', 'w') as f:
        json.dump(convert_sets_to_lists(differences), f, indent=4)
    with open('./data/members_from_website.json', 'w') as f:
        json.dump(convert_sets_to_lists(members_from_website), f, indent=4)
    with open('./data/members_from_xlsx.json', 'w') as f:
        json.dump(convert_sets_to_lists(members_from_xlsx), f, indent=4)

    print("WhatsApp message:")
    print(generate_message(differences, board))

    

