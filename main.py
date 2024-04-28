from fuzzywuzzy import fuzz
import os, re, datetime
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip

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

def get_text_line_dimensions(text_string, font):
    ascent, descent = font.getmetrics()

    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent

    return (text_width, text_height)

def get_text_dimensions(text_string, font):
    print(repr(text_string))
    lines = text_string.split('\n')
    
    max_width = 0
    total_height = 0

    for line in lines:
        width, height = get_text_line_dimensions(line, font)
        max_width = max(max_width, width)
        total_height += height

    return (max_width, total_height)

def time_string_to_seconds(time_str):
    # Parse the time string into a datetime object
    time_obj = datetime.datetime.strptime(time_str, "%H:%M:%S,%f")
    
    # Calculate the total time in seconds
    total_seconds = (time_obj.hour * 3600) + (time_obj.minute * 60) + time_obj.second + (time_obj.microsecond / 1000000)
    
    return total_seconds

def remove_markers(text):
    # Remove text enclosed within <...>
    text = re.sub(r'<[^>]*>', '', text)
    # Remove words within square brackets []
    text = re.sub(r'\[.*?\]', '', text)
    return text

def split_user_input_string(string):
    pattern = r'(\".*?\")'
    quoted_texts = re.findall(pattern, string)
    non_quoted_text = re.sub(pattern, '', string)

    return non_quoted_text.strip(), quoted_texts[0]

def search_srt_for_quote(srt_file, quote, threshold=90):
    start_time, end_time = None, None
    found_quote = None
    
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
                subtitle_text_lines = []
                while i < len(lines) and lines[i].strip() != '':
                    subtitle_text_lines.append(lines[i].strip())
                    if i < len(lines) - 1 and lines[i + 1].strip() != '':
                        subtitle_text_lines.append('\n')  # Append newline if next line is not empty
                    i += 1
                subtitle_text = ' '.join(subtitle_text_lines)  # Join lines into a single string
                
                similarity_score = fuzz.partial_ratio(quote.lower(), subtitle_text.lower())
                if similarity_score >= threshold:
                    start_time = start_time_str
                    end_time = end_time_str
                    found_quote = subtitle_text
                    break
                
            i += 1
            
    return start_time, end_time, found_quote

def find_video_files(directory, extensions=['.mp4', '.avi', '.mov', '.mkv']):
    """
    Find video files with specified extensions in a directory.

    Args:
        directory (str): Directory to search for video files.
        extensions (list): List of video file extensions to search for.
                           Default is ['.mp4', '.avi', '.mov', '.mkv'].

    Returns:
        list: List of paths to video files found in the directory.
    """
    video_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in extensions:
                video_files.append(os.path.join(root, file))
    return video_files

def create_gif(video_path, start_time, end_time, output_dir, target_size=(640, 360)):
    # Load the video clip
    clip = VideoFileClip(video_path)
    
    # Set start and end times
    start_time = min(clip.duration, start_time)
    end_time = min(clip.duration, end_time)
    
    # Extract subclip
    subclip = clip.subclip(start_time, end_time)
    
    # Get original dimensions
    original_size = subclip.size
    
    # Calculate new dimensions while preserving aspect ratio
    target_width, target_height = target_size
    aspect_ratio = original_size[0] / original_size[1]
    new_width = min(target_width, int(target_height * aspect_ratio))
    new_height = min(target_height, int(target_width / aspect_ratio))
    
    # Resize the clip
    resized_clip = subclip.resize((new_width, new_height))
    
    # Get frame rate of the video
    fps = resized_clip.fps
    
    # Write GIF
    output_filename = 'output.gif'
    output_path = os.path.join(output_dir, output_filename)
    resized_clip.write_gif(output_path, fps=fps)
    
    # Close the clips
    clip.close()
    resized_clip.close()

def add_text_to_gif(input_gif_path, output_gif_path, text):
    """
    Add text overlay to an existing GIF.

    Args:
        input_gif_path (str): Path to the input GIF file.
        output_gif_path (str): Path to save the output GIF file with text overlay.
        text (str): Text to be added to the GIF.

    Returns:
        None
    """
    #remove markups from srt files
    text = remove_markers(text)
    # Open the input GIF file
    with Image.open(input_gif_path) as gif:
        frames = []

        # Create a drawing context
        draw = ImageDraw.Draw(gif)

        # Load a font file (replace 'arial.ttf' with the path to your font file)
        font = ImageFont.truetype('arial.ttf', size=24)  

        # Get the size of the text
        text_width, text_height = get_text_dimensions(text, font=font)

        # Calculate the text position
        text_position = ((gif.width - text_width) // 2, (gif.height - text_height-10))
        shadow_postion = (text_position[0]-2, text_position[1]+2)

        # Add text overlay to each frame
        for frame in range(gif.n_frames):
            gif.seek(frame)  # Go to the current frame
            frame_rgb = gif.convert("RGB")  # Convert to RGB mode for drawing

            draw = ImageDraw.Draw(frame_rgb)  # Create a drawing context for the current frame
            
            draw.multiline_text(shadow_postion, text, fill="black", font=font, spacing=8, align="center")
            draw.multiline_text(text_position, text, fill="white", font=font, spacing=8, align="center")

            frames.append(frame_rgb)

        # Save the modified GIF
        frames[0].save(output_gif_path, save_all=True, append_images=frames[1:], loop=0)

def main():
    directory = './Movies'
    output = './Output'
    strict_threshold = 80
    wider_threshold = 60

    while True:
        movie = ""
        quote = ""
        start_time = ""
        end_time = ""
        while movie == "":
            print("What quote would you like to find? ")
            quote_string = input("""Format: Movie Title "Movie Quote": """)
            movie_title, quote = split_user_input_string(quote_string)
            print(f"{movie_title} : {quote}")
            movie_search = fuzzy_search_files_in_directory(directory, movie_title, strict_threshold, wider_threshold)

            if len(movie_search) == 0:
                    print("Movie not found: ", movie_title)
            elif len(movie_search) > 1:
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
                movie = movie_search[0]

        directory = directory + "/" + movie
        srt_file = directory + "/" + find_srt_file(directory)
        
        if srt_file:
            start_time, end_time, quote = search_srt_for_quote(srt_file, quote)
            if start_time and end_time:
                print("Start time:", start_time)
                print("End time:", end_time)
            else:
                print("Quote not found in subtitle file.")
        else:
            print(f"No SRT file present in: {directory}")
        
        if start_time:
            video_files = find_video_files(directory)
            if len(video_files) == 1:
                start_time = time_string_to_seconds(start_time)
                end_time = time_string_to_seconds(end_time)
                create_gif(video_files[0], start_time, end_time, output)
                add_text_to_gif(output+"\\output.gif",output+"\\with_text.gif", quote)
        else:
            print("whomp whomp")
        break
    
if __name__ == "__main__":
    main()