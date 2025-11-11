import json
import sqlite3
import os
from glob import glob
from tqdm import tqdm

def to_list(item):
    if isinstance(item, list):
        return item
    elif item is None:
        return []
    else:
        return [item]

def safe_get(obj, key, default=None):
    """
    Safely get the value from obj[key] if obj is a dict.
    If obj is a list, return default (can't get by key).
    """
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default

def json_folder_to_sqlite(folder_path, db_path, target_language):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS dictionary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            korean TEXT,
            pronunciation TEXT,
            sound_url TEXT,
            part_of_speech TEXT,
            origin TEXT,
            vocabulary_level TEXT,
            related_forms TEXT,
            korean_definition TEXT,
            examples TEXT,
            target_language TEXT,
            translated_word TEXT,
            translated_definition TEXT,
            UNIQUE(korean, korean_definition, target_language)
        )
    """)

    json_files = glob(os.path.join(folder_path, "*.json"))
    print(f"Found {len(json_files)} JSON files in {folder_path}\n")

    total_inserted = 0
    total_skipped = 0

    for json_file in tqdm(json_files, desc="Importing dictionary files", unit="file"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            tqdm.write(f"Failed to load {os.path.basename(json_file)}: {e}")
            continue

        # Navigate safely through nested keys
        lexical_resource = safe_get(data, "LexicalResource", {})
        lexicon = safe_get(lexical_resource, "Lexicon", {})
        entries = safe_get(lexicon, "LexicalEntry", [])
        entries = to_list(entries)

        for entry in entries:
            lemma = safe_get(entry, "Lemma", {})

            # lemma may be a list, take first if so
            if isinstance(lemma, list):
                lemma = lemma[0] if lemma else {}

            lemma_feats = to_list(safe_get(lemma, "feat", []))
            korean_word = None
            for lf in lemma_feats:
                if safe_get(lf, "att") == "writtenForm":
                    korean_word = safe_get(lf, "val")
                    break
            if not korean_word:
                continue

            wordforms = to_list(safe_get(entry, "WordForm", []))
            pronunciation = None
            sound_url = None
            for wf in wordforms:
                wf_feats = to_list(safe_get(wf, "feat", []))
                for feat in wf_feats:
                    if safe_get(feat, "att") == "pronunciation":
                        pronunciation = safe_get(feat, "val")
                    elif safe_get(feat, "att") == "sound":
                        sound_url = safe_get(feat, "val")

            feats = to_list(safe_get(entry, "feat", []))
            pos = origin = vocab_level = None
            for f in feats:
                att = safe_get(f, "att")
                val = safe_get(f, "val")
                if att == "partOfSpeech":
                    pos = val
                elif att == "origin":
                    origin = val
                elif att == "vocabularyLevel":
                    vocab_level = val

            related = to_list(safe_get(entry, "RelatedForm", []))
            related_forms_list = []
            for r in related:
                r_feats = to_list(safe_get(r, "feat", []))
                for rf in r_feats:
                    if safe_get(rf, "att") == "writtenForm":
                        val = safe_get(rf, "val")
                        if val is not None:
                            related_forms_list.append(val)
            related_forms = ", ".join(related_forms_list) if related_forms_list else None

            senses = to_list(safe_get(entry, "Sense", []))
            for sense in senses:
                sense_feats = to_list(safe_get(sense, "feat", []))
                korean_def = None
                for sf in sense_feats:
                    att = safe_get(sf, "att")
                    if att == "definition" or att == "gloss":
                        korean_def = safe_get(sf, "val")
                        break

                examples = to_list(safe_get(sense, "SenseExample", []))
                example_texts = []
                for ex in examples:
                    ex_feats = to_list(safe_get(ex, "feat", []))
                    for ef in ex_feats:
                        if safe_get(ef, "att") == "example":
                            val = safe_get(ef, "val")
                            if val is not None:
                                example_texts.append(val)
                examples_joined = "\n".join(example_texts) if example_texts else None

                equivalents = to_list(safe_get(sense, "Equivalent", []))

                translated_word = None
                translated_def = None
                for eq in equivalents:
                    eq_feats = to_list(safe_get(eq, "feat", []))
                    lang = lemma_eq = definition = None
                    for ef in eq_feats:
                        att = safe_get(ef, "att")
                        val = safe_get(ef, "val")
                        if att == "language":
                            lang = val
                        elif att == "lemma":
                            lemma_eq = val
                        elif att == "definition":
                            definition = val
                    if lang == target_language:
                        translated_word = lemma_eq
                        translated_def = definition
                        break

                try:
                    cur.execute("""
                        INSERT OR IGNORE INTO dictionary (
                            korean, pronunciation, sound_url, part_of_speech,
                            origin, vocabulary_level, related_forms,
                            korean_definition, examples,
                            target_language, translated_word, translated_definition
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        korean_word, pronunciation, sound_url, pos, origin,
                        vocab_level, related_forms, korean_def, examples_joined,
                        target_language, translated_word, translated_def
                    ))
                    if cur.rowcount:
                        total_inserted += 1
                    else:
                        total_skipped += 1
                except Exception as e:
                    tqdm.write(f"Error inserting {korean_word}: {e}")
                    continue

    conn.commit()
    conn.close()
    print(f"\n Finished inserting {total_inserted} entries into {db_path}")
    print(f"Skipped {total_skipped} duplicates")
    print("\n Import complete!")

if __name__ == "__main__":
    json_folder_to_sqlite(
        folder_path="./fullDict",
        db_path="english.db",
        target_language="영어"
    )
