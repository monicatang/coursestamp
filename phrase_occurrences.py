import sys
import json
import re

youtube = "https://www.youtube.com/embed/"
title_matcher = re.compile("Title=(.*)_Id=(.*)") # YouTube code only

"""
Searches the given formatted json file for key phrases
and out puts the youtube timestamped link.

Returns previous phrase to allow for prepadding and post padding of phrase.
"""
def find_occurrences(phrase, filename):
  titles = []
  urls = []
  phrases = []
  with open(filename) as file:
    data = json.load(file)
    for video_title in data:
      title_obj = title_matcher.match(video_title)
      title, youtube_id = title_obj.group(1), title_obj.group(2)
      video_data = data[video_title]
      timestamps = list(video_data.keys())
      for index in range(len(timestamps)):
          if phrase in video_data[timestamps[index]]:
            timestamp = timestamps[index] if index == 0 else timestamps[index - 1]
            titles.append(title)
            urls.append(youtube + video_code + "?start=" + timestamp)
            context = ""
            if(index >0):
              context+=video_data[timestamps[index-1]]
            context+=video_data[timestamps[index]]
            if(index <len(timestamps)-1):
              context+=video_data[timestamps[index+1]]
            phrases.append(context)
  return titles, urls, phrases

if __name__ == '__main__':
  args = sys.argv
  assert len(args) == 3, "Must provide string and file"
  find_occurrences(args[1], args[2])
