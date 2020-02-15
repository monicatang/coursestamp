import sys
import json

youtube = "https://youtu.be/"

def find_occurances(phrase, filename):
  with open(filename) as file:
    data = json.load(file)
    for video_code in data:
      video_data = data[video_code]
      timestamps = list(video_data.keys())
      for index in range(len(timestamps)):
          if phrase in video_data[timestamps[index]]:
            timestamp = video_data[timestamps[index]] if index == 0 else timestamps[index - 1]
            print(youtube + video_code + "?t=" + timestamp)

if __name__ == '__main__':
  args = sys.argv
  assert len(args) == 3, "Must provide string and file"
  find_occurances(args[1], args[2])
