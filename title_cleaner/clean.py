#!/usr/bin/python3

import argparse
import logging
import os
from pathlib import Path
import re
import shutil
import sys


def is_correct_directory(directory_path):
    """
        Returns True if directory exists else False
    """

    return os.path.isdir(directory_path)


def get_file_extension(filename):
    """
        Returns the extension of the file
    """

    _, file_extension = os.path.splitext(filename)

    return file_extension


def create_root_directory(root_path):
    """
        Creates a root directory for the movie 
        if it doesnt exists
    """
    try:
        os.makedirs(root_path)
    except FileExistsError as ex:
        print(f"Folder already exists in {root_path}")




def sanitize_name(name, year_pattern, quality_pattern):
    """
        Returns a sanitized name that will convert this type of names 
            28.Weeks.Later.2007.1080p.BluRay.x264-CiNEFiLE
            Absolutely.Anything.2015.1080p.BluRay.x265-RARBG
            2001 A Space Odyssey (1968) [BluRay] [1080p] [YTS.AM]
        into
            28 Weeks Later (2007) [1080p]
            Absolutely Anything (2015) [1080p]
            2001 A Space Odyssey (1968) [1080p]

    regex -- r"(\(?19[0-9]{2}\)?|\(?20[0-9]{2}\)?)"
    """
    
    movie_name_sanitized = ""
    movie_year = ""
    movie_quality = ""
    common_separators = ['.', '_'] # NOTE - Update this list if the pattern changes


    # Find the movie year with regular expressions
    year_pattern = re.compile(year_pattern)
    movie_year = year_pattern.findall(name)

    if len(movie_year) > 0:
        movie_name_sanitized = name.split(movie_year[-1])[0].strip() # -1 will always take the last item, if only one item, it will take that
        movie_year = movie_year[-1]
        movie_year = movie_year.replace("(", "").replace(")", "")
        movie_year = f" ({movie_year.strip()})" # In case there is only one parenthesis

    # Find the movie quality with regular expressions
    quality_pattern = re.compile(quality_pattern)
    movie_quality_found = quality_pattern.search(name)
    if movie_quality_found:
        movie_quality = movie_quality_found.group(0)
        movie_quality = movie_quality.replace("[", "").replace("]", "")
        movie_quality = f" [{movie_quality.strip()}]"
    
    
    # Replace common separators like ['.', '_'] with space, only if it has more than 3 of them
    for separator in common_separators:
        if name.count(separator) > 3:
            # print(f"Found more {separator}")
            movie_name_sanitized = movie_name_sanitized.replace(separator, " ")
            # print(f"Movie sanitized {movie_name_sanitized}")

    return f"{movie_name_sanitized.title()}{movie_year}{movie_quality}"
    


def remove_rubbish(directory_path, approved_extensions=['.mkv', '.avi', '.mp4']):
    """
        Loops through directories/subdirectories recursively, removing empty directories
        and files that are not video files
    """

    size_cleaned = 0
    video_files = []

    # Get the list of directories in current working directory
    directory_list = [direct for direct in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, direct))]
    
    # Get the list of files in current working directory
    file_list = [file for file in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, file))]

    for file in file_list:
        if get_file_extension(file) not in approved_extensions:
            logging.debug(f'File to remove {os.path.join(directory_path, file)}')
            size_cleaned += Path(os.path.join(directory_path, file)).stat().st_size
            os.remove(os.path.join(directory_path, file))
            # print(f"Removing {os.path.join(directory_path, file)}")

    if len(directory_list) > 0:
        for directory in directory_list:
            if len(os.listdir(os.path.join(directory_path, directory))) == 0:
                logging.debug(f'Directory to remove {os.path.join(directory_path, directory)}')
                os.removedirs(os.path.join(directory_path, directory))
                # print(f"Removing {os.path.join(directory_path, directory)}")

            else: # If directory is not empty, do recursive
                remove_rubbish(os.path.join(directory_path, directory))
    else:
        if len(os.listdir(directory_path)) == 0:
            logging.debug(f'Directory to remove {directory_path}')
            # Remove empty directory
            os.removedirs(directory_path)
            # print(f"Removing {directory_path}")


    return size_cleaned



def main():

    # Setting up logging
    # If you standalone file replace strea=sys.stdout with filename='filename.txt'
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                        stream=sys.stdout,
                        level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S')

    # Setting up the argument parser
    parser = argparse.ArgumentParser(description='Process configuration needed')
    parser.add_argument('path', help='Path to the folder', type=str, metavar='path')
    args = parser.parse_args()

    approved_extensions = ['.mkv', '.mp4', '.avi']

    if is_correct_directory(args.path):
        
        # filter those that are stand alone files
        standalone_movies = [movie for movie in os.listdir(args.path) if movie[-4:] in approved_extensions]
        movie_folder_list = [movie for movie in os.listdir(args.path) if is_correct_directory(os.path.join(args.path, movie))]

    else:
        logging.error(f"Incorrect path {args.path}")
        # print(f"Incorrect path {args.path}")
        exit()

    
    for standalone_movie in standalone_movies:
        sanitized_name = sanitize_name(standalone_movie, 
                                        year_pattern=r"(\(?19[0-9]{2}\)?|\(?20[0-9]{2}\)?)",
                                        quality_pattern=r"(\[?[0-9]+p\]?)")
        
        create_root_directory(os.path.join(args.path, sanitized_name))

        file_extension = get_file_extension(standalone_movie)
        shutil.move(os.path.join(args.path, standalone_movie), os.path.join(args.path, sanitized_name ,sanitized_name+file_extension))



    for movie in movie_folder_list:
        video_files = []

        for root, dirs, files in os.walk(os.path.join(args.path, movie)):

            for f in files:
                file_extension = get_file_extension(f)
                if file_extension in approved_extensions:
                    video_files.append({ 
                        "file_name": f, 
                        "file_path": os.path.join(root, f), 
                        "file_extension": file_extension,
                        "file_size": Path(os.path.join(root, f)).stat().st_size
                        })

        logging.debug(f'Video files found in {movie} #{len(video_files)}')

        sanitized_name = sanitize_name(movie, 
                                        year_pattern=r"(\(?19[0-9]{2}\)?|\(?20[0-9]{2}\)?)",
                                        quality_pattern=r"(\[?[0-9]+p\]?)") # Sanitize from Movie folder not video file

        if len(video_files) == 1:
            
            # print(f"Sanitized name is {sanitized_name}")
            # Rename movie file
            shutil.move(video_files[0]['file_path'], os.path.join(args.path, movie, sanitized_name+video_files[0]['file_extension']))
            # Rename root folder
            shutil.move(os.path.join(args.path, movie), os.path.join(args.path, sanitized_name))

        elif len(video_files) > 1:
            # print("More than 1 video file, checking sizes...")
            video_files.sort(reverse=True, key=lambda video:video['file_size'])
            logging.debug(f'Video files sorted  {video_files}')

            for file_sorted in video_files[1:]:
                logging.debug(f"Removing {file_sorted['file_path']}")
                os.remove(file_sorted['file_path'])

            # Rename movie file
            shutil.move(video_files[0]['file_path'], os.path.join(args.path, movie, sanitized_name+video_files[0]['file_extension']))
            # Rename root folder
            shutil.move(os.path.join(args.path, movie), os.path.join(args.path, sanitized_name))
        


        remove_rubbish(args.path)

if __name__ == "__main__":
    main()




