# Parameters
from parameters import parameters

import os
from PIL import Image


def other_formats_to_jpg(path):
    for file in os.listdir(path):
        if file.endswith('.png') or file.endswith('.jpeg'):
            img = Image.open(os.path.join(path, file))
            img.save(os.path.join(path, file.replace('png', 'jpg').replace('jpeg', 'jpg')))
            os.remove(os.path.join(path, file))

def make_image_640_640(path):
    for file in os.listdir(path):
        if file.endswith('.jpg'):
            img = Image.open(os.path.join(path, file))
            img = img.resize((640, 640))
            img.save(os.path.join(path, file))

def generate_html_from_photos(path):
    html_content = ""
    for file in os.listdir(path):
        if file.endswith('.jpg'):
            name, surname = file.replace('.jpg', '').split('_')
            full_name = f"{name.capitalize()} {surname.capitalize()}"
            tag = "h3"
            # If the full name is too long, use a smaller tag
            if len(full_name) >= 19:
                tag = "h4"
            
            html_content += f"""
    <div style="display: inline-block; overflow: hidden; margin-bottom: 25px; width: 160px; text-align: center; color: #00aaf5;">
        <img
            style="border-radius: 50%;max-width: 100px; border: 2px solid rgba(0, 0, 0, 0.1);"
            src="{parameters["url_to_members_files"]}/{file}"
        />
        <div style="margin-top: 2px; position: relative">
            <{tag} style="margin: 0; font-weight: 400; padding-bottom: 4px">
                {full_name}
                <span style="display: block; font-size: 11px; color: #aaaaaa; line-height: 1.6;">{parameters["default_role"]}</span>
            </{tag}>
        </div>
    </div>
            """
    with open('./photos/index.html', 'w') as f:
        f.write(html_content)

if __name__ == '__main__':
    """Generates a HTML file with the photos of the members"""
    path = './photos'
    other_formats_to_jpg(path)
    print('All images in the directory have been converted to jpg format.')
    make_image_640_640(path)
    print('All images in the directory have been resized to 640x640 pixels.')
    generate_html_from_photos(path)
    print('HTML file has been generated from the photos.')