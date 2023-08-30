import os
import re
import time
import threading
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

subtitles_to_download = []
files_skipped_exist = 0
files_skipped_error = 0
files_downloaded = 0
lock = threading.Lock()


def sanitize_filename(filename):
    sanitized_name = re.sub(r'[^\w\s.-]', '', filename)
    sanitized_name = re.sub(r'\s+', '_', sanitized_name)
    return sanitized_name


def download_subtitles(sub_file_url, save_path):
    global files_downloaded, files_skipped_error
    response = requests.get(sub_file_url)
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            file.write(response.content)
            files_downloaded += 1
    else:
        files_skipped_error += 1


def print_message(message):
    with lock:
        print("\r" + message, end="")


def scan_and_populate_subtitles(subdir_url, ago, subdir_name):
    global files_downloaded, files_skipped_exist, files_skipped_error
    try:
        response = requests.get(subdir_url)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        files_skipped_error += 1
        return []
    subdir_soup = BeautifulSoup(response.content, "html.parser")
    subtitles = []
    for sub_row in subdir_soup.select("#flisttable tr"):
        sub_link = sub_row.select_one("a")
        sub_date_cell = sub_row.select_one(".tdright")
        if sub_link and sub_date_cell:
            sub_file_name = sub_link.text.strip()
            sub_file_url = urljoin(subdir_url, sub_link.get("href"))
            sub_upload_date_str = sub_date_cell.get("title")
            sub_upload_date = datetime.strptime(sub_upload_date_str, "%b %d %Y %I:%M:%S %p")
            if sub_file_url.endswith(('.zip', '.7z', '.rar', '.ass', '.srt')) and sub_upload_date >= ago:
                sanitized_sub_file_name = sanitize_filename(sub_file_name)
                save_dir = os.path.join("downloaded_files", sanitize_filename(subdir_name))
                os.makedirs(save_dir, exist_ok=True)
                file_path = os.path.join(save_dir, sanitized_sub_file_name)
                if not os.path.exists(file_path):
                    message = f"Worker {threading.get_ident()} - Downloading: {sanitize_filename(subdir_name)}/{sanitized_sub_file_name}"
                    print_message(message)
                    subtitles.append((sub_file_url, file_path))
                else:
                    message = f"Worker {threading.get_ident()} - Skipped (Already downloaded): {sanitize_filename(subdir_name)}/{sanitized_sub_file_name}"
                    files_skipped_exist += 1
                    print_message(message)
    return subtitles


def get_days_input(has_previous_run):
    options = ["Full download"]
    if has_previous_run:
        options.append("Since last download")
    options.append("Custom")
    for idx, option in enumerate(options, start=1):
        print(f"{idx}. {option}")
    while True:
        try:
            choice = int(input("Enter your choice: "))
            if 1 <= choice <= len(options):
                return choice
            else:
                print("Invalid choice. Please select a valid option.")
        except ValueError:
            print("Invalid input. Please enter a valid option number.")


def save_last_run_date(last_run_datetime):
    with open("last_run_date.txt", "w") as file:
        file.write(last_run_datetime.strftime("%Y-%m-%d %H:%M:%S"))


def get_last_run_date():
    try:
        with open("last_run_date.txt", "r") as file:
            return datetime.strptime(file.read().strip(), "%Y-%m-%d %H:%M:%S")
    except FileNotFoundError:
        return None


def format_time_difference(time_difference):
    days, seconds = time_difference.days, time_difference.seconds
    if days > 0:
        return f"{days} {'day' if days == 1 else 'days'} ago"
    elif seconds >= 3600:  # More than an hour
        hours = seconds // 3600
        return f"{hours} {'hour' if hours == 1 else 'hours'} ago"
    elif seconds >= 60:  # More than a minute
        minutes = seconds // 60
        return f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
    elif seconds > 0:  # Less than a minute
        return f"{seconds} {'second' if seconds == 1 else 'seconds'} ago"
    else:
        return "Just now"


def main():
    last_run_date = get_last_run_date()
    if last_run_date:
        has_previous_run = True
        time_difference = datetime.now() - last_run_date
        time_ago = format_time_difference(time_difference)
        print(f"Last run was {time_ago}.")
    else:
        has_previous_run = False
        print("First run, a full scrape is recommended")

    choice = get_days_input(has_previous_run)
    if choice == 1:
        days_to_check = 99999  # Full download
    elif choice == 2:
        if has_previous_run:
            days_to_check = (datetime.now() - last_run_date).days  # Since last download
        else:
            while True:
                try:
                    days_to_check = int(input("Enter the number of days to check: "))
                    if days_to_check <= 0:
                        print("Please enter a positive integer.")
                    else:
                        break
                except ValueError:
                    print("Invalid input. Please enter a valid positive integer.")
    elif choice == 3:
        while True:
            try:
                days_to_check = int(input("Enter the number of days to check: "))
                if days_to_check <= 0:
                    print("Please enter a positive integer.")
                else:
                    break
            except ValueError:
                print("Invalid input. Please enter a valid positive integer.")
    else:
        print("Invalid choice.")
        return

    ago = datetime.now() - timedelta(days=days_to_check)
    base_url = "https://kitsunekko.net/dirlist.php?dir=subtitles%2Fjapanese%2F"
    response = requests.get(base_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    start_time = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        index = 0
        for row in soup.select("#flisttable tr"):
            index += 1
            print("\r" + f"Indexing entry {index}", end="")
            link = row.select_one("a")
            if link:
                subdir_name = link.text.strip()
                subdir_url = urljoin(base_url, link.get("href"))
                upload_date_str = row.select_one(".tdright").get("title")
                upload_date = datetime.strptime(upload_date_str, "%b %d %Y %I:%M:%S %p")
                if upload_date >= ago:
                    futures.append(executor.submit(scan_and_populate_subtitles, subdir_url, ago, subdir_name))
        for future in futures:
            subtitles_to_download.extend(future.result())
        for sub_file_url, file_path in subtitles_to_download:
            executor.submit(download_subtitles, sub_file_url, file_path)
    end_time = time.time()
    runtime = end_time - start_time
    print("\nDownload completed.")
    print(f"Files skipped because they already existed: {files_skipped_exist}")
    print(f"Files skipped because of an invalid download link: {files_skipped_error}")
    print(f"Files downloaded: {files_downloaded}")
    print(f"Script runtime: {runtime:.2f} seconds")
    save_last_run_date(datetime.now())
    print("Last run date saved.")


if __name__ == "__main__":
    main()
