import json
import re
import os

# regex parsers
#lecture_matcher = re.compile("Lecture (\\d+.\\d).*-(.*)\\.en") # for Andrew Ng specifically
lecture_matcher = re.compile(".*-(.*)\\.en") # YouTube code only
timestamp_matcher = re.compile("(\\d\\d):(\\d\\d):(\\d\\d).\\d\\d\\d --> \\d\\d:\\d\\d:\\d\\d.\\d\\d\\d")

def parse():
  subtitle_dict = {}
  for filename in os.listdir(os.getcwd()):
    if filename == "subtitle_parser.py": # ignore self
      continue
    lecture_obj = lecture_matcher.match(filename)
#    lecture_number = lecture_obj.group()
    lecture_code = lecture_obj.group(1)
    file_dict = {}
    with open(filename) as file:
      last_time = None
      found_subtitle = False
      for line in file:
        if found_subtitle:
          file_dict[last_time] = line
          found_subtitle = False
        else:
          timestamp_obj = timestamp_matcher.match(line)
          if timestamp_obj:
            hours = timestamp_obj.group(1)
            minutes = timestamp_obj.group(2)
            seconds = timestamp_obj.group(3)
            total_seconds = 60*60*int(hours) + 60*int(minutes) + int(seconds)
            if total_seconds == last_time:
              continue
            found_subtitle = True
            last_time = total_seconds
#      subtitle_dict[lecture_number + " " + lecture_code] = file_dict
      subtitle_dict[lecture_code] = file_dict
  return subtitle_dict

if __name__ == '__main__':
  print(json.dumps(parse(), indent = 4, sort_keys=True))

