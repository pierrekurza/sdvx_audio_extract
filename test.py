import glob
import os
import pathlib

import requests
import re
import subprocess
from PIL import Image

URL_GET_MUSIC_INFOS = "https://fairyjoke.net/api/games/sdvx/musics/{0}"

GAME_VERSIONS = {
    1: "SOUND VOLTEX BOOTH",
    2: "SOUND VOLTEX II -infinite infection-",
    3: "SOUND VOLTEX III GRAVITY WARS",
    4: "SOUND VOLTEX IV HEAVENLY HAVEN",
    5: "SOUND VOLTEX V VIVID WAVE",
    6: "SOUND VOLTEX VI EXCEED GEAR"
}

DIFF_LIST = ["NOVICE", "ADVANCED", "EXHAUST", "MAXIMUM", "INFINITE", "GRAVITY", "HEAVENLY", "VIVID", "EXCEED"]
URL_GET_MUSIC_COVER = "https://fairyjoke.net/api/games/sdvx/musics/{0}/{1}.png"
URL_GET_DEFAULT_COVER = "https://fairyjoke.net/api/games/sdvx/assets/jacket/version.png"


def get_folder_number(folder_name) -> int:
    folder_number = re.search(r"[^\\]+(?=\\$|$)", folder_name)
    if folder_number:
        found_number_in_string = re.search(r'^[^_]+(?=_)', folder_number.group())
        if len(found_number_in_string.group()) == 4:
            return int(found_number_in_string.group()[0:4].lstrip('0'))
        else:
            return int(found_number_in_string.group()[0:5].lstrip('0'))
    else:
        raise NameError("Nothing found.")


def get_music_infos_from_api(music_id: int):
    response_api = requests.get(URL_GET_MUSIC_INFOS.format(music_id))
    if response_api.status_code == 404:
        return
    data = response_api.json()
    music_name = data["title"]
    artist_name = data["artist"]
    album_artist = "Various Artists"
    album_name = GAME_VERSIONS[data["version"]] + " GST"
    max_diff = ""
    simple_name = data["ascii"]
    # Value can be : "EXHAUST"
    if len(data["difficulties"]) == 3:
        max_diff = data["difficulties"][2]['diff']
    # Values can be : "MAXIMUM", "INFINITE", "GRAVITY", "HEAVENLY", "VIVID", "EXCEED"
    elif len(data["difficulties"]) == 4:
        max_diff = data["difficulties"][3]['diff']
    print(music_name, artist_name, album_artist, album_name, max_diff, simple_name)


def clean_covers_folders_and_delete(covers_path: str):
    covers_dir = glob.glob(covers_path + "\\covers" + "\\*")
    for i in covers_dir:
        os.remove(i)
    if os.path.isdir(os.path.join(covers_path, "covers")):
        os.rmdir(covers_path + "\\covers")


def get_music_cover_from_api(music_id: int, diff_name: str, extract_folder: str):
    if diff_name.upper() in DIFF_LIST:
        image = ""
        response_api = requests.get(URL_GET_MUSIC_COVER.format(music_id, diff_name), stream=True)
        if response_api.status_code == 404:
            default_sdvx_cover_response = requests.get(URL_GET_DEFAULT_COVER, stream=True)
            image = Image.open(default_sdvx_cover_response.raw)
        else:
            image = Image.open(response_api.raw)

        if not os.path.isdir(os.path.join(extract_folder, "covers")):
            pathlib.Path(os.path.join(extract_folder, "covers")).mkdir(parents=True, exist_ok=False)
            os.chdir(os.path.join(extract_folder, "covers"))
            os.chdir(os.path.join(extract_folder, "covers"))
            final_cover_path = f"{os.path.join(extract_folder, "covers")}" + "\\{0}.png".format(str(music_id))
            if not os.path.isfile(final_cover_path):
                image.save(f"{final_cover_path}")
            return os.getcwd() + "\\{0}.png".format(str(music_id))
        return os.path.join(extract_folder, "covers") + "\\{0}.png".format(str(music_id))
    else:
        raise NameError("Cover not found.")


def convert_audio_and_move_file(folder_path: str, folder_number: int, output_path: str, music_name: str,
                                artist_name: str, album_artist: str, album_name: str, ascii_name: str, diff_name: str):
    list_of_files = glob.glob(folder_path + '\\*.s3v', recursive=True)
    if len(list_of_files) == 0:
        return
    if not music_name.strip():
        return
    music_path: str = ""

    cover_path = get_music_cover_from_api(folder_number, diff_name, output_path)
    for music in list_of_files:
        if not re.search("(_pre.s3v$)", music):
            music_path = music
    # Launch extract
    output_path_final = os.path.join(output_path, album_name, str(folder_number) + f"_{ascii_name}.mp3")

    #Code pour créer les dossiers finaux de jeux
    for name in GAME_VERSIONS.values():
        if not os.path.exists(os.path.join(output_path, name)):
            os.makedirs(os.path.join(output_path, name))

    command_line = '''C:\\TOOLS\\ffmpeg.exe -i "%s" -i "%s" -map 0:0 -map 1:0 -ab 320k -c copy -acodec libmp3lame 
    -id3v2_version 3 -metadata:s:v title="Album cover" -metadata:s:v comment="Cover (front)" -metadata title="%s" 
    -metadata artist="%s" -metadata album_artist="%s" -metadata album="%s" -q:a 0 "%s"'''
    process = subprocess.Popen(command_line % (
        music_path,
        cover_path,
        music_name,
        artist_name,
        album_artist,
        album_name + " GST",
        output_path_final
    ), shell=True)
    if process:
        return True
    else:
        return False


if __name__ == '__main__':
    # number_song = get_folder_number("0025_rebellious_stage_dios")
    # get_music_infos_from_api(number_song)
    # get_music_cover_from_api(number_song, "INFINITE", "E:\\Torrents\\Musique")
    convert_audio_and_move_file("C:\\BEMANI\\SDVX\\SDVX EXCEED GEAR (DATA)\\2023_09_12\\data\\music\\0025_rebellious_stage_dios",
                                25, "E:\\Torrents\\Musique", "Rebellious stage Dios", "シグナルP",
                                "Various Artists", "SOUND VOLTEX BOOTH GST", "rebellious_stage_dios",
                                "INFINITE")

