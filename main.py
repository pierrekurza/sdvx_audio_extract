import glob
import os
import requests
import re
import subprocess
import static_ffmpeg
from PIL import Image

# 0 : Music ID
URL_GET_MUSIC_INFOS = "https://fairyjoke.net/api/games/sdvx/musics/{0}"

# 0 : Music ID
# 1 : Difficulty name
URL_GET_MUSIC_COVER = "https://fairyjoke.net/api/games/sdvx/musics/{0}/{1}.png"

URL_GET_DEFAULT_COVER = "https://fairyjoke.net/api/games/sdvx/assets/jacket/version.png"

DIFF_LIST = ["NOVICE", "ADVANCED", "EXHAUST", "MAXIMUM", "INFINITE", "GRAVITY", "HEAVENLY", "VIVID", "EXCEED"]

SDVX_NAME = "SOUND VOLTEX"

GAME_VERSIONS = {
    1: "SOUND VOLTEX BOOTH",
    2: "SOUND VOLTEX II -infinite infection-",
    3: "SOUND VOLTEX III GRAVITY WARS",
    4: "SOUND VOLTEX IV HEAVENLY HAVEN",
    5: "SOUND VOLTEX V VIVID WAVE",
    6: "SOUND VOLTEX VI EXCEED GEAR"
}


# Get all the folder inside the provided file path
# Returns the list of all folders names inside the provided path
def get_folders_name(sound_path: str):
    sub_folders = [f.path for f in os.scandir(sound_path) if f.is_dir()]
    for dir_name in list(sub_folders):
        sub_folders.extend(get_folders_name(dir_name))
    return sub_folders


# Reads the current folder name
# Returns the number associated with the current folder
def get_folder_number(folder_name: str) -> int:
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
    album_name = GAME_VERSIONS[data["version"]]
    max_diff = ""
    simple_name = data["ascii"]
    # Value can be : "EXHAUST"
    if len(data["difficulties"]) == 3:
        max_diff = data["difficulties"][2]['diff']
    # Values can be : "MAXIMUM", "INFINITE", "GRAVITY", "HEAVENLY", "VIVID", "EXCEED"
    elif len(data["difficulties"]) == 4:
        max_diff = data["difficulties"][3]['diff']
    return music_name, artist_name, album_artist, album_name, max_diff, simple_name


def get_music_cover_from_api(music_id: int, diff_name: str, extract_folder: str):
    if diff_name.upper() in DIFF_LIST:
        image = ""
        response_api = requests.get(URL_GET_MUSIC_COVER.format(music_id, diff_name), stream=True)
        if response_api.status_code == 404:
            default_sdvx_cover_response = requests.get(URL_GET_DEFAULT_COVER, stream=True)
            image = Image.open(default_sdvx_cover_response.raw)
        else:
            image = Image.open(response_api.raw)
        cover_path = os.path.join(extract_folder, "covers")
        final_cover_path = os.path.join(cover_path + "\\{0}.png".format(music_id))
        if not os.path.isdir(os.path.join(extract_folder, "covers")):
            os.makedirs(os.path.join(extract_folder, "covers"))
            os.chdir(os.path.join(extract_folder, "covers"))
            if not os.path.exists(final_cover_path):
                image.save(f"{final_cover_path}")
                return os.getcwd() + "\\{0}.png".format(str(music_id))
        else:
            image.save(final_cover_path)
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
        if not re.search("(_pre.s3v$)", music) and not re.search("(_fx.s3v$)", music):
            music_path = music
    # Launch extract
    output_path_final = os.path.join(output_path, album_name, str(folder_number) + f"_{ascii_name}.mp3")
    # Create folders for each game
    for name in GAME_VERSIONS.values():
        if not os.path.exists(os.path.join(output_path, name)):
            os.makedirs(os.path.join(output_path, name))

    command_line = '''static_ffmpeg -y -i "%s" -i "%s" -map 0:0 -map 1:0 -ab 320k -metadata:s:v title="Album cover" -metadata:s:v comment="Cover (front)" -metadata title="%s" -metadata artist="%s" -metadata album_artist="%s" -metadata album="%s" "%s"'''
    process = subprocess.Popen(command_line % (
        music_path,
        cover_path,
        music_name,
        artist_name,
        album_artist,
        f"{album_name} GST",
        output_path_final
    ), shell=True)
    print(process.args)
    if process:
        return True
    else:
        return False


def introduction_cli():
    print("SDVX Songs Extraction Tool")
    while True:
        game_folder = input("Please provide the SDVX game path > ")
        if os.path.exists(game_folder) and "soundvoltex.dll" in os.listdir(game_folder + "\\modules"):
            print("Continue")
            break
        else:
            print("soundvoltex.dll is not present...")
    while True:
        extract_folder = input("Please provide the path where musics have to be extracted (the folder will be created "
                               "if it doesn't exist) > ")
        break
    return game_folder, extract_folder


def clean_covers_folders_and_delete(covers_path: str):
    covers_dir = glob.glob(covers_path + "\\covers" + "\\*")
    for i in covers_dir:
        os.remove(i)
    if os.path.isdir(os.path.join(covers_path, "covers")):
        os.rmdir(covers_path + "\\covers")


def main():
    folder_number: int
    game_folder, extract_folder = introduction_cli()
    clean_covers_folders_and_delete(extract_folder)
    music_folder = os.path.join(game_folder, "data", "music")
    folders = get_folders_name(music_folder)
    static_ffmpeg.add_paths()
    for folder in folders:
        folder_number = get_folder_number(folder)
        music_name, artist_name, album_artist, album_name, max_diff, simple_name = get_music_infos_from_api(folder_number)
        convert_audio_and_move_file(folder,
                                    folder_number,
                                    extract_folder,
                                    music_name,
                                    artist_name,
                                    album_artist,
                                    album_name,
                                    simple_name,
                                    max_diff)


if __name__ == '__main__':
    main()
