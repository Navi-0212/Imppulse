import os
import json

conversations = [
    "06209a58-b397-4306-80da-44298c6f39f0",
    "1e2bb72a-e26b-42cf-a3b3-952565c8ae4a",
    "2b9128df-efa5-4ae0-9ffb-b12890e00552",
    "49935776-3b45-43dd-bdf2-edcdbefd5bb9",
    "4bddcb45-38a5-4283-99ce-c2c839d5ea12",
    "4f7890d4-1336-4953-86c1-3e63c62443c1",
    "4f8a2859-0861-44ca-9fa8-91929abe1222",
    "6668f24b-465b-4ac3-aecf-8fed3c504673",
    "70eef2e6-3ac4-4ac8-8ba0-8563119de77b",
    "7209b96c-b1b3-44ee-b999-8c366af8d870",
    "7a67a940-4ad4-442d-a46d-75cf56e7f45e",
    "8717e0ee-bacd-47b8-b04e-6f036d1309d0",
    "8d7c6440-0f2a-4254-afae-f09725f12ae8",
    "8dca4c1e-2d1b-4ba9-bbb3-3c44b4640b11",
    "a87db807-a4fd-4e81-a7c8-253caf6f0a73",
    "c8ed3bc7-0d90-46d6-9752-9d4beea0a5d3",
    "cd6bf2e5-8898-477b-9daf-1c842c975dc8",
    "d94a1e62-0f85-45c2-a0eb-d98560f5d248",
    "e221a959-cf41-4da9-a8f2-9896b2e78734",
    "ed9b1da4-0741-4523-9b21-8def87b64865",
    "f006b27d-165d-48cf-bf06-1b75626ba355",
    "f4c61355-1b2e-496e-b43d-938ccb90b3e8"
]

brain_dir = r"C:\Users\smita\.gemini\antigravity-ide\brain"

found_any = False
for cid in conversations:
    log_path = os.path.join(brain_dir, cid, ".system_generated", "logs", "transcript.jsonl")
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if "impullse" in line.lower() or "impulse" in line.lower():
                        print(f"Found match in conversation {cid}!")
                        found_any = True
                        break
        except Exception as e:
            print(f"Error reading {log_path}: {e}")
    else:
        pass

if not found_any:
    print("No matches for impullse/impulse in any past conversation logs.")
