import os
import sys

"""
Combines playlist_to_subtitles.py and subtitle_parser.py
to create a directory structure in examples with subtitles and json.
"""
def json_generator(link):
  os.mkdir("../examples/new")
  os.mkdir("../examples/new/raw_subtitles/")
  os.system("cp playlist_to_subtitles.py ../examples/new/raw_subtitles/playlist_to_subtitles.py")
  os.chdir("../examples/new/raw_subtitles/")
  os.system("python playlist_to_subtitles.py " + link)
  os.system("rm playlist_to_subtitles.py")
  os.system("cp ../../../scripts/subtitle_parser.py subtitle_parser.py")
  os.system("python subtitle_parser.py > ../new.json")
  os.system("rm subtitle_parser.py")

if __name__ == '__main__':
  args = sys.argv
  assert len(args) == 2, "Must provide playlist"
  json_generator(args[1])