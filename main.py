import glob
import os
import pprint

import requests
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

URL_GET_MUSIC_INFOS = "https://fairyjoke.net/api/games/sdvx/musics/{0}"


# Get all the folder inside the provided file path
# Returns the list of all folders names inside the provided path
def get_folders_name(sound_path: str):
    sub_folders = [f.path for f in os.scandir(sound_path) if f.is_dir()]
    for dir_name in list(sub_folders):
        sub_folders.extend(get_folders_name(dir_name))
    return sub_folders


def get_music_infos(music_id: int):
    response_api = requests.get(URL_GET_MUSIC_INFOS.format(music_id))
    pprint.pprint((response_api.json()), sort_dicts=False)


# Reads the current folder name
# Returns the number associated with the current folder
def get_folder_number(folder_name) -> int:
    folder_number = re.search(r"[^\\]+(?=\\$|$)", folder_name)
    if folder_number:
        found_number_in_string = re.search(r'^[^_]+(?=_)', folder_number.group())
        if len(found_number_in_string.group()) == 4:
            return int(found_number_in_string.group()[0:4].lstrip('0'))
        else:
            return int(found_number_in_string.group()[0:5].lstrip('0'))
    else:
        raise NameError("Nothing found")


# Opens and reads the XML File provided
# Returns the XML file as a file
def read_music_xml(music_xml_file_path: str) -> ET.Element:
    with open(music_xml_file_path, 'r', encoding="cp932") as file:
        xml_string = file.read()
        tree = ET.fromstring(xml_string)
        return tree


# Get music name, artist name from the XML File.
# Returns music_name, artist_name, album_artist, album_name in this order.
def get_music_infos_from_xml(song_id: int, music_xml_file_path: str):
    music_name = ""
    artist_name = ""
    album_artist = "Various Artists"
    album_name = "SOUND VOLTEX GST"
    xml = read_music_xml(music_xml_file_path)
    for music_info in xml.findall(".//music[@id='{0}']/info".format(song_id)):
        if len(music_info.find('title_name').text) > 0:
            music_name = music_info.find('title_name').text
            artist_name = music_info.find('artist_name').text
    return music_name, artist_name, album_artist, album_name


# Retrieves the best resolution cover for a given folder name
# Returns the path of the best resolution cover
def get_music_cover(music_folder_path: str) -> str:
    list_of_covers = glob.glob(music_folder_path + '\\*.png', recursive=True)
    if len(list_of_covers) == 12:
        other_pattern_available = "(_4_b.png$)"
        first_try = browse_and_get_cover(list_of_covers, "(_5_b.png$)")
        if first_try is None:
            return browse_and_get_cover(list_of_covers, other_pattern_available)
        return first_try
    # 2 types of covers available
    elif len(list_of_covers) == 6:
        other_pattern_available = "(_4_b.png$)"
        first_try = browse_and_get_cover(list_of_covers, "(_5_b.png$)")
        # No cover found for the first try
        if first_try is None:
            return browse_and_get_cover(list_of_covers, other_pattern_available)
        return first_try
    # 1 cover available
    elif len(list_of_covers) == 3:
        other_pattern_available = "(_4_b.png$)"
        first_try = browse_and_get_cover(list_of_covers, "(_1_b.png$)")
        if first_try is None:
            return browse_and_get_cover(list_of_covers, other_pattern_available)
        return first_try
    # 3 covers available
    elif len(list_of_covers) == 9:
        return browse_and_get_cover(list_of_covers, "(_3_b.png$)")


def browse_and_get_cover(list_of_covers: list[str], search_pattern: str):
    for cover in list_of_covers:
        if re.search(search_pattern, cover):
            return cover


def convert_audio_and_move_file(folder_path: str, folder_number: int, output_path: str, music_name: str,
                                artist_name: str, album_artist: str, album_name: str):
    list_of_files = glob.glob(folder_path + '\\*.s3v', recursive=True)
    if len(list_of_files) == 0:
        return
    if not music_name.strip():
        return
    music_path: str = ""
    cover_path = get_music_cover(folder_path)
    for music in list_of_files:
        if not re.search("(_pre.s3v$)", music):
            music_path = music
    # Launch extract
    output_path_final = output_path + "\\" + str(folder_number) + ' - ' + music_name + ".mp3"
    command_line = '''C:\\TOOLS\\ffmpeg.exe -i "%s" -i "%s" -map 0:0 -map 1:0 -c copy -acodec libmp3lame -id3v2_version 3 -metadata:s:v title="Album cover" -metadata:s:v comment="Cover (front)" -metadata title="%s" -metadata artist="%s" -metadata album_artist="%s" -metadata album="%s" -q:a 0 "%s"'''
    process = subprocess.Popen(command_line % (
        music_path,
        cover_path,
        music_name,
        artist_name.replace("\"", "\\\""),
        album_artist,
        album_name,
        output_path_final
    ), shell=True)
    if process:
        return True
    else:
        return False


def main():
    get_music_infos(1773)
    # args = sys.argv[1:]
    # if len(args) == 4 and args[0] == '-audiopath' and args[2] == '-musicxmlpath':
    #     # specify the path for the output folder
    #     output_folder = "G:\\DEV_SDVX"
    #     # rename SDVX_SONG to whatever you like
    #     output_folder_name = "\\" + "SDVX_SONGS_2"
    #     final_output_folder_name = output_folder + output_folder_name
    #     if not os.path.exists(final_output_folder_name):
    #         os.makedirs(final_output_folder_name)
    #     audio_path = args[1]
    #     xml_path = args[3]
    #     folders = get_folders_name(audio_path)
    #     for folder in folders:
    #         folder_number = get_folder_number(folder)
    #         music_name, artist_name, album_artist, album_name = get_music_infos_from_xml(folder_number, xml_path)
    #         convert_audio_and_move_file(folder, folder_number, final_output_folder_name, music_name, artist_name,
    #                                     album_artist, album_name)


if __name__ == '__main__':
    main()
