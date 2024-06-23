import glob
import os
import music_tag


def get_sub_folders_name(folder_name: str) -> list:
    try:
        elements = os.listdir(folder_name)
    except FileNotFoundError:
        print(f"The directory {folder_name} doesn't exist.")
        return []
    except PermissionError:
        print(f"Not allowed to access this directory {folder_name}.")
        return []

    sub_folder = [os.path.abspath(os.path.join(folder_name, element)) for element in elements if
                  os.path.isdir(os.path.join(folder_name, element))]

    return sub_folder


def get_audio_files_list(folder_name: str) -> list:
    pattern = os.path.join(folder_name, '*.mp3')
    audio_files = glob.glob(pattern)

    audio_files = [os.path.abspath(audio_file) for audio_file in audio_files]
    return audio_files


def get_metadatas(files_list: list) -> list:
    audios_metadatas = []
    for audio in files_list:
        audio_file = music_tag.load_file(audio)
        metadata = {
            'title': audio_file['title']
        }
        audios_metadatas.append((audio, metadata))
    return sorted(audios_metadatas, key=lambda x: str(x[1]['title']).casefold())


def apply_metadata_sort_by_title_on_list(files_with_metadatas: list):
    counter = 1
    for file, metadata in files_with_metadatas:
        current_audio = music_tag.load_file(file)
        current_audio['tracknumber'] = counter
        current_audio.save()
        counter += 1


def set_track_number_metadata(folders_list: list):
    for folder in folders_list:
        audios = get_audio_files_list(folder)
        metadatas_list = get_metadatas(audios)
        apply_metadata_sort_by_title_on_list(metadatas_list)


def introduction_cli():
    print("Just sorting files after an extract")
    while True:
        extract_folder = input("Please provide the path where musics have been extracted  > ")
        if os.path.exists(extract_folder):
            print("Extract folder is found.")
        else:
            print("Folder " + extract_folder + " is not found.")
        break
    return extract_folder


def main():
    extract_folder = introduction_cli()
    sub_folders = get_sub_folders_name(extract_folder)
    set_track_number_metadata(sub_folders)


if __name__ == '__main__':
    main()
