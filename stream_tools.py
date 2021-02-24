import os
import re
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions


#! EDIT THESE
YTDL_PATH = R'C:\Python37-32\Scripts\youtube-dl.exe'
FFMPEG_PATH = R'C:\ffmpeg\bin\ffmpeg.exe'
FIREFOX_PATH = R'C:\Program Files (x86)\Mozilla Firefox\firefox.exe'


# Check if channel is streaming
def channel_is_streaming(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content,features="html.parser")
    return "{\"text\":\" watching\"}" in soup.text

# Grab list of current streams
# Each list item should be [title, id]
# Input: Videos -> Uploads -> Live now page
def list_channel_streams(url):
    # Use selenium to get page source after javascript execution
    options = FirefoxOptions()
    options.add_argument('--headless')
    browser = webdriver.Firefox(firefox_binary=FIREFOX_PATH,options=options)
    browser.get(url)
    soup = BeautifulSoup(browser.page_source,"html.parser")
    browser.quit()

    stream_list = []
    for tag in soup.find_all('a',{'id':'video-title'},href=True):
        stream = []
        title = tag.text
        link = re.sub("/watch\?v=(.*)","\\1",tag.get('href'))
        stream.append(title)
        stream.append(link)
        stream_list.append(stream)
    return stream_list

# Receive youtube watch ID (or full URL), return live m3u8 link
def get_livestream_url(url):
    stream = os.popen(f'\"{YTDL_PATH}\" -g -f best "{url}"')
    live_url = stream.read().strip()
    if "m3u8" in live_url: # Weak verification of valid link
        return live_url
    else:
        return ""

# Receive m3u8 link, capture screenshot and return filename
def get_stream_screenshot(url):
    current_time = int(time.time())
    stream_img_outname = f"{current_time}.jpg" # Filename of output image
    stream = os.popen(f'\"{FFMPEG_PATH}\" -hide_banner -loglevel error -i "{url}" -f image2 -frames:v 1 "{stream_img_outname}"') # -loglevel error 
    stream.read() # Forces a wait for os.popen command to finish before moving on
    if os.path.isfile(stream_img_outname): # Verify screenshot was taken
        return stream_img_outname
    else:
        return ""

# Combines above two methods
def get_screen_from_yt_link(url):
    stream_url = get_livestream_url(url)
    if stream_url != "":
        screenshot = get_stream_screenshot(stream_url)
        if screenshot != "": return screenshot
    else:
        return ""
