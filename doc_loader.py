import glob

def load_docs():
    texts = []
    for path in sorted(glob.glob("docs/*.txt")):
        with open(path, "r", encoding="utf-8") as f:
            texts.append(f.read())
    return texts

ALL_DOCS = load_docs()