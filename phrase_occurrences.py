import sys
import json

youtube = "https://youtu.be/"

"""
Searches the given formatted json file for key phrases
and out puts the youtube timestamped link.

Returns previous phrase to allow for prepadding and post padding of phrase.
"""
def find_occurrences(phrase, filename):
  ret = []
  with open(filename) as file:
    data = json.load(file)
    for video_code in data:
      video_data = data[video_code]
      timestamps = list(video_data.keys())
      for index in range(len(timestamps)):
          if phrase in video_data[timestamps[index]]:
            timestamp = timestamps[index] if index == 0 else timestamps[index - 1]
            ret.append(youtube + video_code + "?t=" + timestamp)
  return ret

if __name__ == '__main__':
  args = sys.argv
  assert len(args) == 3, "Must provide string and file"
  find_occurrences(args[1], args[2])
