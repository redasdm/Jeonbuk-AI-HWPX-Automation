import json
import os

JSON_PATH = r"C:\Users\redas\.gemini\antigravity\brain\48219d81-e4d8-4230-8f36-af86eb7d8050\scratch\desktop_files_info.json"
TXT_PATH = r"C:\Users\redas\.gemini\antigravity\brain\48219d81-e4d8-4230-8f36-af86eb7d8050\scratch\desktop_files_readable.txt"

def main():
    if not os.path.exists(JSON_PATH):
        print("JSON not found")
        return
        
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    with open(TXT_PATH, "w", encoding="utf-8") as out:
        out.write(f"Total files: {len(data)}\n")
        out.write("=" * 80 + "\n\n")
        
        for idx, item in enumerate(data, start=1):
            out.write(f"[{idx}] FILENAME: {item['filename']}\n")
            out.write(f"    PATH: {item['path']}\n")
            # Clean content from double newlines or long spaces
            content = item['content']
            snippet = content[:800].strip()
            out.write(f"    CONTENT SNIPPET:\n{snippet}\n")
            out.write("\n" + "-" * 80 + "\n\n")
            
    print(f"Readable summary written to {TXT_PATH}")

if __name__ == "__main__":
    main()
