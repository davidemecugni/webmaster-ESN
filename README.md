Tools to make my life as Webmaster of Modena and Reggio Emilia ESN(Erasmus Student Network) section easier!

## checks_for_differences.py 
This is a tool that uses a recent .xlsx file downloadable from Jupiter with all the members
to provide all the missing members on the ESN MoRe About Us section of the website. 
It also considers missing middle names and tries to avoid UTF-8 to ASCII errors.
Might not work if the name is saved differently on Jupiter.

## members_from_photos.py
Given the pictures saved as NAME_SURNAME.EXT under the photos folder, it modifies the photos 
to be 640x640 pixels and generates the HTML to be added on the website.
Default role for a new picture is "Active Member".
