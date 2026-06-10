#!/usr/bin/env python3
import os
import json
import re
import subprocess
import sys

# Color formatting helpers using ANSI escape sequences
def print_success(message):
    print(f"\033[92m[OK] {message}\033[0m")

def print_info(message):
    print(f"\033[94m[*] {message}\033[0m")

def print_warning(message):
    print(f"\033[93m[!] {message}\033[0m")

def print_error(message):
    print(f"\033[91m[ERROR] {message}\033[0m")

def print_header(message):
    print(f"\n\033[95m=== {message} ===\033[0m")

# Helper functions for URL conversion
def extract_youtube_id(url):
    pattern = r'(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def extract_google_drive_id(url):
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'[?&]id=([a-zA-Z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def convert_gdrive_url(url, to_type="download"):
    file_id = extract_google_drive_id(url)
    if not file_id:
        return url
    if to_type == "image":
        return f"https://drive.usercontent.com/download?id={file_id}&authuser=0"
    else:  # dataJsonUrl / download
        return f"https://drive.google.com/uc?id={file_id}"

# Function to load a JSON file
def load_json(filepath):
    if not os.path.exists(filepath):
        print_error(f"File not found: {filepath}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Error reading {filepath}: {e}")
        return None

# Function to save a JSON file
def save_json(filepath, data):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print_success(f"Saved {filepath} successfully.")
        return True
    except Exception as e:
        print_error(f"Error writing to {filepath}: {e}")
        return False

# Function to auto-increment version in version.json
def increment_version(version_key):
    version_file = "version.json"
    data = load_json(version_file)
    if not data:
        print_warning("Could not read version.json, skipping version bump.")
        return False
    
    if version_key not in data:
        print_warning(f"Key '{version_key}' not found in version.json.")
        create_key = input(f"Would you like to add the '{version_key}' key to version.json? (y/n) [y]: ").strip().lower()
        if create_key == 'n':
            return False
        data[version_key] = "0"
        
    try:
        curr_ver = int(data[version_key])
        next_ver = curr_ver + 1
        data[version_key] = str(next_ver)
        if save_json(version_file, data):
            print_success(f"Bumped version of '{version_key}' from {curr_ver} to {next_ver}.")
            return True
    except ValueError:
        print_error(f"Version value for '{version_key}' in version.json is not an integer: {data[version_key]}")
    return False

# Auto ID Generation logic
def get_next_id(items, prefix, is_padded=False):
    max_num = 0
    pattern = re.compile(rf"^{prefix}_(\d+)$")
    for item in items:
        item_id = item.get("id")
        if item_id:
            match = pattern.match(item_id)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
    
    next_num = max_num + 1
    if is_padded:
        return f"{prefix}_{next_num:03d}"
    else:
        return f"{prefix}_{next_num}"

# Git utility functions
def git_commit_and_push(files_modified, commit_message):
    try:
        # Run git add
        print_info("Staging modified files...")
        subprocess.run(["git", "add"] + files_modified, check=True)
        
        # Run git commit
        print_info(f"Committing changes with message: '{commit_message}'")
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Run git push
        print_info("Pushing changes to remote...")
        subprocess.run(["git", "push"], check=True)
        
        print_success("Changes committed and pushed to remote successfully!")
    except subprocess.CalledProcessError as e:
        print_error(f"Git command failed: {e}")
    except FileNotFoundError:
        print_error("Git executable not found in PATH.")

# Main Interactive Workflows
def handle_links_and_test_links(is_test=False):
    target_filename = "links_test.json" if is_test else "links.json"
    other_filename = "links.json" if is_test else "links_test.json"
    version_key = "test_links" if is_test else "links"
    
    print_header(f"Adding to {target_filename}")
    
    data = load_json(target_filename)
    if data is None:
        return
    
    # 1. Content Type Choice
    print("Select Content Type:")
    print("1. BOOK")
    print("2. PDF")
    print("3. YOUTUBE")
    print("4. AUDIO")
    print("5. VIDEO")
    
    content_type_map = {
        "1": "BOOK",
        "2": "PDF",
        "3": "YOUTUBE",
        "4": "AUDIO",
        "5": "VIDEO"
    }
    
    choice = input("Enter choice (1-5): ").strip()
    content_type = content_type_map.get(choice)
    if not content_type:
        print_error("Invalid content type choice.")
        return
    
    # 2. Auto Generate ID
    prefix = "RB" if content_type in ["BOOK", "PDF"] else "RM"
    new_id = get_next_id(data.get("items", []), prefix, is_padded=False)
    print_info(f"Auto-generated ID: {new_id}")
    
    # 3. Titles
    title = input("Enter English Title: ").strip()
    odia_title = input("Enter Odia Title (optional): ").strip()
    hindi_title = input("Enter Hindi Title (optional): ").strip()
    
    # 4. URLs
    external_url = ""
    data_json_url = ""
    audio_path = ""
    video_path = ""
    image_url = ""
    
    # Specific inputs based on Content Type
    if content_type in ["BOOK", "PDF"]:
        raw_json_url = input("Enter Data JSON URL (Google Drive/etc.): ").strip()
        data_json_url = convert_gdrive_url(raw_json_url, to_type="download")
        if raw_json_url != data_json_url:
            print_info(f"Converted Google Drive link to direct link: {data_json_url}")
            
    elif content_type == "YOUTUBE":
        external_url = input("Enter YouTube Link: ").strip()
        
    elif content_type == "AUDIO":
        raw_audio = input("Enter audio path or audio filename (under mp3/): ").strip()
        if not raw_audio.startswith("http") and not raw_audio.startswith("raw.github"):
            audio_path = f"https://raw.githubusercontent.com/mak-cell/hindumania_assets/master/mp3/{raw_audio}"
            print_info(f"Derived audio path: {audio_path}")
        else:
            audio_path = raw_audio
            
    elif content_type == "VIDEO":
        raw_video = input("Enter video path or video filename (under mp4/): ").strip()
        if not raw_video.startswith("http") and not raw_video.startswith("raw.github"):
            video_path = f"https://raw.githubusercontent.com/mak-cell/hindumania_assets/master/mp4/{raw_video}"
            print_info(f"Derived video path: {video_path}")
        else:
            video_path = raw_video

    # 5. Image URL (with YouTube derivation and Google Drive conversion)
    auto_image = "n"
    yt_id = None
    if content_type == "YOUTUBE" and external_url:
        yt_id = extract_youtube_id(external_url)
    
    if yt_id:
        auto_image = input(f"Auto-derive YouTube thumbnail for image URL? (y/n) [y]: ").strip().lower() or "y"
        if auto_image == "y":
            image_url = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg"
            print_info(f"Derived thumbnail URL: {image_url}")
            
    if not image_url:
        raw_image_url = input("Enter Image URL (optional): ").strip()
        if raw_image_url:
            image_url = convert_gdrive_url(raw_image_url, to_type="image")
            if raw_image_url != image_url:
                print_info(f"Converted Google Drive link to image direct link: {image_url}")

    # 6. Category
    # Suggest existing categories
    categories = sorted(list(set(item.get("category") for item in data.get("items", []) if item.get("category"))))
    if categories:
        print_info(f"Existing categories: {', '.join(categories)}")
    category = input("Enter Category (optional): ").strip()
    
    # 7. Construct Item
    item = {
        "id": new_id,
        "title": title,
        "odiaTitle": odia_title,
        "hindiTitle": hindi_title,
        "imageUrl": image_url,
        "contentType": content_type
    }
    
    if category:
        item["category"] = category
    if data_json_url:
        item["dataJsonUrl"] = data_json_url
    if external_url:
        item["externalUrl"] = external_url
    if audio_path:
        item["audioPath"] = audio_path
    if video_path:
        item["videoPath"] = video_path
        
    print_info(f"Constructed Item: {json.dumps(item, indent=2, ensure_ascii=False)}")
    
    confirm = input("Save item? (y/n) [y]: ").strip().lower() or "y"
    if confirm != 'y':
        print_warning("Cancelled saving.")
        return
        
    data["items"].append(item)
    if save_json(target_filename, data):
        modified_files = [target_filename]
        increment_version(version_key)
        
        # 8. Sync Option
        sync_other = input(f"Would you also like to add this item to {other_filename}? (y/n) [n]: ").strip().lower() or "n"
        if sync_other == 'y':
            other_data = load_json(other_filename)
            if other_data is not None:
                # Check if item with this ID already exists
                existing_ids = [it.get("id") for it in other_data.get("items", [])]
                if new_id in existing_ids:
                    print_warning(f"Item ID {new_id} already exists in {other_filename}. Prompting to regenerate ID for {other_filename}.")
                    other_prefix = prefix
                    other_new_id = get_next_id(other_data.get("items", []), other_prefix, is_padded=False)
                    item_copy = item.copy()
                    item_copy["id"] = other_new_id
                    print_info(f"Regenerated ID for {other_filename}: {other_new_id}")
                else:
                    item_copy = item
                    
                other_data["items"].append(item_copy)
                if save_json(other_filename, other_data):
                    modified_files.append(other_filename)
                    other_version_key = "links" if is_test else "test_links"
                    increment_version(other_version_key)
        
        # Ask for Git push
        modified_files.append("version.json")
        git_push_confirm = input("Would you like to commit and push changes to Git remote? (y/n) [y]: ").strip().lower() or "y"
        if git_push_confirm == 'y':
            commit_msg = f"Auto-update: Added {new_id} to {target_filename}"
            git_commit_and_push(modified_files, commit_msg)


def handle_podcast():
    target_filename = "podcast.json"
    version_key = "podcast"
    
    print_header(f"Adding to {target_filename}")
    
    data = load_json(target_filename)
    if data is None:
        return
        
    # 1. Select Language
    print("Select Language:")
    print("1. Hindi (PODHI)")
    print("2. English (PODEN)")
    print("3. Odia (PODOD)")
    
    lang_map = {
        "1": ("Hindi", "PODHI"),
        "2": ("English", "PODEN"),
        "3": ("Odia", "PODOD")
    }
    
    lang_choice = input("Enter choice (1-3): ").strip()
    if lang_choice not in lang_map:
        print_error("Invalid language choice.")
        return
        
    lang_name, prefix = lang_map[lang_choice]
    
    # 2. Auto Generate ID
    new_id = get_next_id(data.get("items", []), prefix, is_padded=True)
    print_info(f"Auto-generated ID: {new_id}")
    
    # 3. Titles
    title = input("Enter English Title: ").strip()
    odia_title = input("Enter Odia Title (optional): ").strip()
    hindi_title = input("Enter Hindi Title (optional): ").strip()
    
    # 4. External URL
    external_url = input("Enter YouTube Link: ").strip()
    
    # 5. Image URL (auto derive or custom)
    image_url = ""
    yt_id = extract_youtube_id(external_url)
    if yt_id:
        auto_image = input(f"Auto-derive YouTube thumbnail for image URL? (y/n) [y]: ").strip().lower() or "y"
        if auto_image == "y":
            image_url = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg"
            print_info(f"Derived thumbnail URL: {image_url}")
            
    if not image_url:
        raw_image_url = input("Enter Image URL (optional): ").strip()
        if raw_image_url:
            image_url = convert_gdrive_url(raw_image_url, to_type="image")
            
    # 6. Item construction
    item = {
        "id": new_id,
        "title": title,
        "odiaTitle": odia_title,
        "hindiTitle": hindi_title,
        "imageUrl": image_url,
        "contentType": "VIDEO",
        "category": "PODCAST",
        "language": lang_name,
        "externalUrl": external_url
    }
    
    print_info(f"Constructed Item: {json.dumps(item, indent=2, ensure_ascii=False)}")
    
    confirm = input("Save item? (y/n) [y]: ").strip().lower() or "y"
    if confirm != 'y':
        print_warning("Cancelled saving.")
        return
        
    data["items"].append(item)
    if save_json(target_filename, data):
        increment_version(version_key)
        
        # Git Push
        git_push_confirm = input("Would you like to commit and push changes to Git remote? (y/n) [y]: ").strip().lower() or "y"
        if git_push_confirm == 'y':
            modified_files = [target_filename, "version.json"]
            commit_msg = f"Auto-update: Added podcast {new_id}"
            git_commit_and_push(modified_files, commit_msg)


def handle_youtube():
    target_filename = "youtube.json"
    version_key = "youtube"  # note: might not exist in version.json yet, we handle creation
    
    print_header(f"Adding to {target_filename}")
    
    data = load_json(target_filename)
    if data is None:
        return
        
    # 1. Select Language
    print("Select Language:")
    print("1. Hindi (YTHI)")
    print("2. Odia (YTOD)")
    
    lang_map = {
        "1": ("Hindi", "YTHI"),
        "2": ("Odia", "YTOD")
    }
    
    lang_choice = input("Enter choice (1-2): ").strip()
    if lang_choice not in lang_map:
        print_error("Invalid language choice.")
        return
        
    lang_name, prefix = lang_map[lang_choice]
    
    # 2. Auto Generate ID
    new_id = get_next_id(data.get("items", []), prefix, is_padded=True)
    print_info(f"Auto-generated ID: {new_id}")
    
    # 3. Titles
    title = input("Enter English Title (optional): ").strip()
    odia_title = input("Enter Odia Title (optional): ").strip()
    hindi_title = input("Enter Hindi Title (optional): ").strip()
    
    # If it's Hindi, default the Title to Hindi Title if English is empty
    if lang_name == "Hindi" and hindi_title and not title:
        title = hindi_title
    elif lang_name == "Odia" and odia_title and not title:
        title = odia_title
        
    # 4. External URL
    external_url = input("Enter YouTube Link: ").strip()
    
    # 5. Image URL (auto derive or custom)
    image_url = ""
    yt_id = extract_youtube_id(external_url)
    if yt_id:
        auto_image = input(f"Auto-derive YouTube thumbnail for image URL? (y/n) [y]: ").strip().lower() or "y"
        if auto_image == "y":
            image_url = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg"
            print_info(f"Derived thumbnail URL: {image_url}")
            
    if not image_url:
        raw_image_url = input("Enter Image URL (optional): ").strip()
        if raw_image_url:
            image_url = convert_gdrive_url(raw_image_url, to_type="image")
            
    # 6. Item construction
    item = {
        "id": new_id,
        "title": title,
        "odiaTitle": odia_title,
        "hindiTitle": hindi_title,
        "imageUrl": image_url,
        "contentType": "YOUTUBE",
        "category": "MEDIA",
        "externalUrl": external_url
    }
    
    print_info(f"Constructed Item: {json.dumps(item, indent=2, ensure_ascii=False)}")
    
    confirm = input("Save item? (y/n) [y]: ").strip().lower() or "y"
    if confirm != 'y':
        print_warning("Cancelled saving.")
        return
        
    data["items"].append(item)
    if save_json(target_filename, data):
        increment_version(version_key)
        
        # Git Push
        git_push_confirm = input("Would you like to commit and push changes to Git remote? (y/n) [y]: ").strip().lower() or "y"
        if git_push_confirm == 'y':
            modified_files = [target_filename, "version.json"]
            commit_msg = f"Auto-update: Added youtube item {new_id}"
            git_commit_and_push(modified_files, commit_msg)


def handle_notifications():
    target_filename = "notifications.json"
    version_key = "notifications"
    
    print_header(f"Adding to {target_filename}")
    
    data = load_json(target_filename)
    if data is None:
        return
        
    # 1. Auto Generate ID
    new_id = get_next_id(data.get("notifications", []), "notification", is_padded=True)
    print_info(f"Auto-generated ID: {new_id}")
    
    # 2. Select Notification Type
    print("Select Notification Type:")
    print("1. custom (Custom push message)")
    print("2. welcome (Welcome message)")
    print("3. daily_calendar (Daily calendar alarm/reminder)")
    
    type_map = {
        "1": "custom",
        "2": "welcome",
        "3": "daily_calendar"
    }
    
    type_choice = input("Enter choice (1-3): ").strip()
    notif_type = type_map.get(type_choice, "custom")
    
    # 3. Inputs based on type
    item = {
        "id": new_id,
        "notificationType": notif_type
    }
    
    if notif_type == "daily_calendar":
        time_val = input("Enter trigger time (HH:MM) [07:00]: ").strip() or "07:00"
        enabled_val = input("Enabled by default? (y/n) [y]: ").strip().lower() or "y"
        item["time"] = time_val
        item["type"] = "text_only"
        item["enabled"] = True if enabled_val == 'y' else False
    else:
        # Multilingual Titles
        title_en = input("Enter Title (English): ").strip()
        title_hi = input("Enter Title (Hindi) (optional): ").strip()
        title_or = input("Enter Title (Odia) (optional): ").strip()
        
        # Multilingual Messages
        msg_en = input("Enter Message (English): ").strip()
        msg_hi = input("Enter Message (Hindi) (optional): ").strip()
        msg_or = input("Enter Message (Odia) (optional): ").strip()
        
        item["title"] = {
            "en": title_en,
            "hi": title_hi,
            "or": title_or
        }
        item["message"] = {
            "en": msg_en,
            "hi": msg_hi,
            "or": msg_or
        }
        
        # Frequency / Delay
        try:
            delay = int(input("Enter delay in days after install [0]: ").strip() or "0")
        except ValueError:
            delay = 0
            
        freq = input("Enter frequency (once/daily/etc.) [once]: ").strip() or "once"
        
        item["startAfterInstallDays"] = delay
        item["frequency"] = freq
        item["type"] = "text_only"
        
    print_info(f"Constructed Notification: {json.dumps(item, indent=2, ensure_ascii=False)}")
    
    confirm = input("Save notification? (y/n) [y]: ").strip().lower() or "y"
    if confirm != 'y':
        print_warning("Cancelled saving.")
        return
        
    data["notifications"].append(item)
    if save_json(target_filename, data):
        increment_version(version_key)
        
        # Git Push
        git_push_confirm = input("Would you like to commit and push changes to Git remote? (y/n) [y]: ").strip().lower() or "y"
        if git_push_confirm == 'y':
            modified_files = [target_filename, "version.json"]
            commit_msg = f"Auto-update: Added notification {new_id}"
            git_commit_and_push(modified_files, commit_msg)


def main():
    while True:
        print_header("Asset Automation Manager")
        print("1. Add Link to links.json (Main links)")
        print("2. Add Link to links_test.json (Test links)")
        print("3. Add Podcast Episode (podcast.json)")
        print("4. Add YouTube Video (youtube.json)")
        print("5. Add App Notification (notifications.json)")
        print("6. Exit")
        
        choice = input("Enter your choice (1-6): ").strip()
        
        if choice == "1":
            handle_links_and_test_links(is_test=False)
        elif choice == "2":
            handle_links_and_test_links(is_test=True)
        elif choice == "3":
            handle_podcast()
        elif choice == "4":
            handle_youtube()
        elif choice == "5":
            handle_notifications()
        elif choice == "6":
            print_info("Exiting Asset Automation Manager. Goodbye!")
            break
        else:
            print_error("Invalid selection. Please enter a number between 1 and 6.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print_info("Execution interrupted by user. Exiting.")
        sys.exit(0)
