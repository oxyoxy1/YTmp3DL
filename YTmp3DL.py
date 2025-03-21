import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import yt_dlp
import os
import subprocess
import threading
import sys
import re

def show_error(error_message):
    """Display an error in a new window with selectable text."""
    error_window = tk.Toplevel()
    error_window.title("Error")

    error_text = tk.Text(error_window, wrap='word', width=50, height=10)
    error_text.insert(tk.END, error_message)
    error_text.config(state='disabled')
    error_text.pack(padx=10, pady=10)

    close_button = tk.Button(error_window, text="Close", command=error_window.destroy)
    close_button.pack(pady=5)

    error_window.mainloop()

def sanitize_filename(filename):
    """Remove or replace characters that may cause issues in filenames."""
    return re.sub(r'[<>:"/\\|?*\[\],]', '_', filename)

def download_audio_thread():
    """Download audio and convert it safely."""
    url = url_entry.get()
    format_choice = format_var.get()

    if not url:
        show_error("Please provide a YouTube URL.")
        return

    current_directory = os.getcwd()

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(current_directory, '%(title)s.%(ext)s'),
        'progress_hooks': [update_progress],
        'quiet': True
    }

    try:
        print(f"Attempting download from: {url}")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info_dict)

        sanitized_video_file = os.path.abspath(video_file)
        if not os.path.exists(sanitized_video_file):
            show_error("Download failed, file doesn't exist.")
            return

        print(f"Download successful: {sanitized_video_file}")

        # **Sanitize output filename**
        sanitized_title = sanitize_filename(info_dict['title'])
        output_file = os.path.join(current_directory, f"{sanitized_title}.{format_choice}")
        output_file = os.path.abspath(output_file)

        print(f"Sanitized output file: {output_file}")

        ffmpeg_command = [
            'ffmpeg', '-i', sanitized_video_file,
            '-vn', '-acodec', 'libmp3lame' if format_choice == 'mp3' else 'pcm_s16le',
            '-ar', '44100', '-ac', '2', '-b:a', '192k', '-y', output_file
        ]

        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=creationflags)

        if result.returncode != 0:
            show_error(f"FFmpeg failed:\n{result.stderr}")
            print(f"FFmpeg error: {result.stderr}")
            return

        os.remove(sanitized_video_file)
        messagebox.showinfo("Success", f"Download/conversion complete! File saved to:\n{output_file}")
    except Exception as e:
        show_error(f"An error occurred: {str(e)}")

def update_progress(d):
    """Progress hook for yt-dlp to update the progress bar."""
    if d['status'] == 'downloading':
        if 'downloaded_bytes' in d and 'total_bytes' in d:
            progress = int(d['downloaded_bytes'] / d['total_bytes'] * 100)
            progress_bar['value'] = progress
            window.update_idletasks()
    elif d['status'] == 'finished':
        progress_bar['value'] = 100
        window.update_idletasks()

def start_download():
    """Start the download process in a separate thread."""
    progress_bar['value'] = 0
    threading.Thread(target=download_audio_thread, daemon=True).start()

# Creating the main window
window = tk.Tk()
window.title("YTmp3DL - oxy")

# URL input
url_label = tk.Label(window, text="Enter YouTube URL:")
url_label.pack(pady=5)
url_entry = tk.Entry(window, width=50)
url_entry.pack(pady=5)

# Formatting
format_label = tk.Label(window, text="Audio Format:")
format_label.pack(pady=5)
format_var = tk.StringVar()
format_var.set('mp3')  # Default format

mp3_button = tk.Radiobutton(window, text="MP3", variable=format_var, value='mp3')
mp3_button.pack(pady=5)
wav_button = tk.Radiobutton(window, text="WAV", variable=format_var, value='wav')
wav_button.pack(pady=5)

# Download button
download_button = tk.Button(window, text="Download Audio", command=start_download)
download_button.pack(pady=20)

# Progress bar
progress_bar = ttk.Progressbar(window, orient='horizontal', length=300, mode='determinate')
progress_bar.pack(pady=10)

# Start the Tkinter event loop
window.mainloop()
