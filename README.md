Tools to make my life as Webmaster of Modena and Reggio Emilia ESN(Erasmus Student Network) section easier!

# checks_for_differences.py 
This is a tool that uses a recent .xlsx file downloadable from Jupiter with all the members
to provide all the missing members on the ESN MoRe About Us section of the website. 
It also considers missing middle names and tries to avoid UTF-8 to ASCII errors.
Might not work if the name is saved differently on Jupiter.

Quick guide:
1. Download the .xlsx file from Jupiter and save it under members as members.xlsx.
2. Run the script.
3. Check the output for missing members(accents and missing or mispelled members on Jupiter could be
outputted but can be ignored).
4. Add the missing members to the website(use members_from_photos.py).
5. Run the script again to check if everything is correct.
6. Enjoy!

# members_from_photos.py
Given the pictures saved as NAME_SURNAME.EXT under the photos folder, it modifies the photos 
to be 640x640 pixels and generates the HTML to be added on the website.
Default role for a new picture is "Active Member".

Quick guide:
1. Save the pictures as NAME_SURNAME.EXT under the photos folder.
2. Run the script.
3. Copy the generated HTML for each member and paste it on the website(role could be wrong).
4. Upload the pictures to the website and refresh cache.
5. Enjoy!
