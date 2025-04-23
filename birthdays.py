from checks_for_differences import replace_multiple_spaces_with_single_space, colored
import os
import pandas as pd
from datetime import datetime, timedelta
from ics import Calendar, Event

def fetch_members_from_xlsx():
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
        full_name = replace_multiple_spaces_with_single_space(full_name)
        birthday = datetime.strptime(row['Birthdate'], '%d/%m/%Y') if isinstance(row['Birthdate'], str) else row['Birthdate']
        members["esners"].append({full_name: birthday})
    
    # Extract names from ALUMNI table
    for index, row in alumni_df.iterrows():
        full_name = f"{row['First Name']} {row['Last Name']}"
        full_name = replace_multiple_spaces_with_single_space(full_name)
        birthday = datetime.strptime(row['Birthdate'], '%d/%m/%Y') if isinstance(row['Birthdate'], str) else row['Birthdate']
        members["alumni"].append({full_name: birthday})
    
    return members

def generate_message(sorted_members):
    # Generate message of NAME SURNAME : BIRTHDAY
    # Name and surname are of fixed lenght based on the longest name
    max_length = max(len(name) for member in members["esners"] + members["alumni"] for name in member.keys())
    message = ""


    for member in sorted_members:
        for name, birthday in member.items():
            message += f"{name.ljust(max_length)} : {birthday.strftime('%d/%m')}\n"
    # Print the message
    print(message.strip())

def filter_members(members):
    # Filter members containing "esn"
    members["esners"] = [member for member in members["esners"] if "esn" not in list(member.keys())[0].lower()]
    members["alumni"] = [member for member in members["alumni"] if "esn" not in list(member.keys())[0].lower()]
    sorted_members = sorted(
        members["esners"] + members["alumni"], 
        key=lambda member: list(member.values())[0].strftime('%m%d')
    )

    return sorted_members

from datetime import datetime

from datetime import datetime

def generate_google_calendar_link(sorted_members, year):
    base_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    event_title = "ESN Birthday Calendar"
    event_location = "Modena, Italy"
    
    rdates = []
    description_lines = ["🎉 Birthdays of ESN ENEA Modena members:\n"]

    for member in sorted_members:
        for name, birthday in member.items():
            rdate = f"{year}{birthday.strftime('%m')}{birthday.strftime('%d')}T000000Z"
            rdates.append(rdate)
            description_lines.append(f"• {name}: {birthday.strftime('%B %d')}")

    rrule_dates = ",".join(rdates)
    description = "\n".join(description_lines)
    encoded_description = description.replace(' ', '%20').replace('\n', '%0A')

    # Use the first birthday as the anchor date
    first_date = rdates[0] if rdates else f"{current_year}0101T000000Z"
    end_date = first_date[:8] + "T235900Z"

    url = (
        f"{base_url}&text={event_title}"
        f"&dates={first_date}/{end_date}"
        f"&details={encoded_description}"
        f"&location={event_location}"
        f"&recur=RDATE;TZID=UTC:{rrule_dates}"
    )
    
    return url



def generate_birthday_ics(sorted_members, year, filename="birthdays.ics"):
    calendar = Calendar()

    for member in sorted_members:
        for name, birthday in member.items():
            event = Event()
            event.name = f"Compleanno {name}"
            event.begin = f"{year}-{birthday.strftime('%m')}-{birthday.strftime('%d')}"
            event.make_all_day()
            event.location = "Modena, Italy"
            event.description = f"Compleanno di {name} - ESN ENEA Modena 🎉"
            calendar.events.add(event)

    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(calendar)


if __name__ == "__main__":
    year = datetime.now().year
    members = fetch_members_from_xlsx()
    sorted_members = filter_members(members)
    generate_message(sorted_members)
    print(len(sorted_members))
    print(generate_google_calendar_link(sorted_members, year))
    generate_birthday_ics(sorted_members, year)