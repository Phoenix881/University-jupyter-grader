def clean(folder_path: str) -> None:
    """
    Cleans up the specified folder by removing all files and subdirectories.

    Args:
        folder_path (str): The path to the folder to be cleaned.
    """
    import os
    import shutil

    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} does not exist.")
        return

    try:
        # Remove all files and subdirectories in the folder
        # Except for .gitkeep files
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                if not item.endswith('.gitkeep'):
                    os.remove(item_path)
        print(f"Folder {folder_path} has been cleaned.")
    except Exception as e:
        print(f"An error occurred while cleaning the folder: {e}")

def removeDuplicates(folder_path: str) -> None:
    # Go to the directory "app/uploaded" and delete any duplicate files
    import os
    seen_files = set()
    for filename in os.listdir(folder_path):
        if filename in seen_files:
            os.remove(os.path.join(folder_path, filename))
        else:
            seen_files.add(filename)