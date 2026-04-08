import os
import zipfile

source_dir = 'cv_macro'
dest_file = 'JBStudy_Macro_v2.zip'

def should_exclude(path):
    exclusions = ['.venv', '__pycache__', '.git', 'build_dist.py']
    for ex in exclusions:
        if ex in path:
            return True
    return False

print(f"Creating {dest_file}...")
with zipfile.ZipFile(dest_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(source_dir):
        if should_exclude(root):
            continue
            
        for file in files:
            if file.endswith('.zip') or file == 'build_dist.py':
                continue
                
            file_path = os.path.join(root, file)
            if should_exclude(file_path):
                continue
                
            # Create a nice top-level folder inside the zip
            arcname = os.path.join('JBStudy_Macro', os.path.relpath(file_path, source_dir))
            print(f"Adding: {arcname}")
            zipf.write(file_path, arcname)

print("Done! You can distribute JBStudy_Macro_v2.zip")
