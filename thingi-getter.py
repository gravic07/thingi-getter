"""
A BS4 web scraper for downloading Thingiverse files with details and images.
"""

import argparse
import pathlib
import requests

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

parser = argparse.ArgumentParser(
  description='Thingiverse web scraper given a url and destination.'
)

parser.add_argument(
  'id',  # Name of the flag, doubles as 'dest' value
  type=str,
  help='the Thingiverse numerical id to scrape'
)

parser.add_argument(
  # '-d',
  # '--dir',
  'dir',
  type=pathlib.Path,
  # dest='dir',
  help='the directory to save the scraped files'
)

args = parser.parse_args()


def create_directories(base_dir):
  """Makes necessary directories for saving Thingiverse files."""
  base_dir.mkdir(parents=True, exist_ok=True)
  images_dir = base_dir / "images"
  images_dir.mkdir(parents=True, exist_ok=True)
  files_dir = base_dir / "files"
  files_dir.mkdir(parents=True, exist_ok=True)


def save_slides(slides):
  "Extract and save images from Thingiverse slides"
  for slide in slides:
    img = slide.find("img")
    source = img['src']
    file_name = source.split("/")[-1]
    img_data = requests.get(source).content
    img_path = base_dir / "images" / file_name
    with open(img_path, 'wb') as handler:
      handler.write(img_data)


def save_files(file_list):
  "Extract and save files from Thingiverse file list."
  file_anchors = file_list.find_all("a")
  for anchor in file_anchors:
    href = anchor['href']
    file_data = requests.get(href).content
    file_path = base_dir / "files" / anchor['download']
    with open(file_path, 'wb') as handler:
      handler.write(file_data)


def save_description(desc_parent):
  """Extract and save the description to a README.txt file."""
  # TODO currently not grabbing images or video links in the description
  # TODO Also no real formatting of sections.

  desc_elements = desc_parent.select("p, div[class^=ThingPage__blockTitle]")
  description = ""
  for el in desc_elements:
    # Add Spacing before section headers (div elements)
    if el.name == "div" and description != "":
      description += "\n\n"
    # Add the text from child element to the final description
    description += el.get_text() + "\n"

  # Write the readme file
  readme_path = base_dir / "README.txt"
  with open(readme_path, 'w') as handler:
    handler.write(description)  
  return description


def save_comments(comment_container):
  """Extract and save the comments from a Thingiverse page."""
  content = ""
  comments = comment_container.select("div[class^=ThingComment__commentBody]")
  for comment in comments:
    if content != "":
      content += "\n\n"
    content += comment.get_text()

  # Write the comments file
  comments_path = base_dir / "COMMENTS.txt"
  with open(comments_path, 'w') as handler:
    handler.write(content)

  return content


# Establish URLs for specific Thing
base_url = f"https://www.thingiverse.com/thing:{args.id}/"  # 3364860
files_url = base_url + "files"
comments_url = base_url + "comments"

# Setup the Selenium browser
options = Options()
options.add_argument("--headless")
browser = webdriver.Chrome("./chromedriver", options=options)

# Get the URL and load BS object
print(f"Attempting to get content from {base_url}...")
browser.get(base_url)
html = BeautifulSoup(browser.page_source, 'html.parser')
# print(html.prettify())

# Wait for objects to load
print("Waiting for page to load...")
_ = WebDriverWait(browser, 30).until(
  EC.presence_of_element_located((By.CLASS_NAME, 'slide'))
)

# Use the title to name the parent dir.
title = "untitled_thing"
title_div = html.select_one("div[class^=ThingPage__modelName]")
if title_div:
  title = title_div.string
print(f"The title has been set to: {title}")

# Create parent and child directories
base_dir = args.dir / title
create_directories(base_dir)
print(f"Directories were created at: {base_dir}")

# Save the images
slides = html.select('li.slide')
print(f"{len(slides)} Slides found...")
save_slides(slides)

# Save the description and top comments as README.txt
desc_parent = html.select_one("div[class^=ThingPage__mainColumn]")
description = save_description(desc_parent)

# Navigate to the files page
print("Waiting for files page to load...")
browser.get(files_url)
html = BeautifulSoup(browser.page_source, 'html.parser')
# Wait for objects to load
_ = WebDriverWait(browser, 30).until(
  EC.presence_of_element_located((By.CLASS_NAME, 'carousel-slider'))
)

# Save files
file_list = html.select_one("div[class^=ThingFilesList__fileList]")
save_files(file_list)

# Navigate to the comments page and wait for it to load
print("Waiting for comments page to load...")
browser.get(comments_url)
html = BeautifulSoup(browser.page_source, 'html.parser')
_ = WebDriverWait(browser, 30).until(
  EC.presence_of_element_located(
    (By.CSS_SELECTOR, 'div[class^=ThingCommentsList__thingCommentsContainer]')
  )
)

comment_container = html.select_one(
  "div[class^=ThingCommentsList__thingCommentsContainer]"
)
save_comments(comment_container)

browser.quit()

print(f"{title} has been saved from Thingiverse.")
