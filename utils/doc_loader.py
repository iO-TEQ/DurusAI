import glob

def load_docs():
    texts = []
    for path in sorted(glob.glob("docs/*.txt")):
        with open(path, "r", encoding="utf-8") as f:
            texts.append(f.read())
    return texts

ALL_DOCS = load_docs()

def load_hmi_docs():
    hmi_docs = ["docs/02_hmi.txt", "docs/04_hmi_views.txt"]
    texts = []
    for path in sorted(hmi_docs):
        with open(path, "r", encoding="utf-8") as f:
            texts.append(f.read())
    return texts

ALL_HMI_DOCS = load_hmi_docs()