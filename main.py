from fuzzywuzzy import fuzz
import os
import re

def fuzzy_search_files_in_directory(directory, target, strict_threshold=90, wider_threshold=70):
    """
    Search for files in the specified directory based on fuzzy matching with the target string.

    Args:
        directory (str): The path to the directory to search for files.
        target (str): The target string to match against file names.
        strict_threshold (int, optional): The threshold for strict matching. Files with a similarity score
            greater than or equal to this threshold will be considered as matching. Defaults to 90.
        wider_threshold (int, optional): The threshold for wider matching. If no matches are found with
            the strict threshold, files with a similarity score greater than or equal to this threshold
            will be considered as matching. Defaults to 70.

    Returns:
        list: A list of file names that match the target string based on fuzzy matching criteria.
    """
    matching_files = []
    for filename in os.listdir(directory):
        similarity_score = fuzz.partial_ratio(target.lower(), filename.lower())
        if similarity_score >= strict_threshold:
            matching_files.append(filename)
            
    if not matching_files:
        for filename in os.listdir(directory):
            similarity_score = fuzz.partial_ratio(target.lower(), filename.lower())
            if similarity_score >= wider_threshold:
                matching_files.append(filename)
    return matching_files

def find_srt_file(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.srt'):
                return file
    return None

def split_user_input_string(string):
    pattern = r'(\".*?\")'
    quoted_texts = re.findall(pattern, string)
    non_quoted_text = re.sub(pattern, '', string)

    return non_quoted_text.strip(), quoted_texts[0]

def search_srt_for_quote(srt_file, quote, threshold=90):
    start_time, end_time = None, None
    
    with open(srt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if re.search(r'\d', line):  # Check if the line contains any digit
                i += 1
                timecode_line = lines[i].strip()
                time_parts = timecode_line.split(' --> ')
                start_time_str, end_time_str = time_parts[0], time_parts[1]
                
                i += 1
                subtitle_text = ''
                while i < len(lines) and lines[i].strip() != '':
                    subtitle_text += lines[i].strip() + ' '
                    i += 1
                subtitle_text = subtitle_text.strip()  # Convert the list of lines into a single string

                similarity_score = fuzz.partial_ratio(quote.lower(), subtitle_text.lower())
                if similarity_score >= threshold:
                    start_time = start_time_str
                    end_time = end_time_str
                    break
                
            i += 1
            
    return start_time, end_time


def main():
    directory = './Movies'
    strict_threshold = 80
    wider_threshold = 60

    while True:
        movie = ""
        quote = ""
        while movie == "":
            print("What quote would you like to find? ")
            quote_string = input("""Format: Movie Title "Movie Quote": """)
            movie_title, quote = split_user_input_string(quote_string)
            print(f"{movie_title} : {quote}")
            movie_search = fuzzy_search_files_in_directory(directory, movie_title, strict_threshold, wider_threshold)

            if len(movie_search) == 0:
                    print("bizz")
                    print("Movie not found: ", movie_title)
            elif len(movie_search) > 1:
                print("bazz")
                print("Several Movies match your search:")
                for index, item in enumerate(movie_search):
                    print(index+1, " : ", item)
                while True:
                    choice = input("Selection: ")
                    if choice.isdigit():
                        choice = int(choice)
                        if choice > 0 and choice <= len(movie_search):
                            movie = movie_search[choice-1]
                            break
            else:
                print("buzz")
                movie = movie_search[0]

        directory = directory + "/" + movie
        srt_file = directory + "/" + find_srt_file(directory)
        
        # add try catch
        if srt_file:
            start_time, end_time = search_srt_for_quote(srt_file, quote)
            if start_time and end_time:
                print("Start time:", start_time)
                print("End time:", end_time)
            else:
                print("Quote not found in subtitle file.")
        else:
            print(f"No SRT file present in: {directory}")
        break
    
if __name__ == "__main__":
    main()