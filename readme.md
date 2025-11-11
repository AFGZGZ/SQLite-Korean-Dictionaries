# SQLite Korean Dictionaries

This repository contains a JSON to SQLite converter scripts & prebuilt SQLite dictionaries using the [KRDict](https://krdict.korean.go.kr/) dictionary from the Korean Language Institute.

The simplified JSON extractions are made by [RicBent](https://github.com/RicBent/KRDict-Converter/releases/tag/2.1.0)

RUN: node buildDictionaryDB.js

The full versions can be downloaded directly from https://krdict.korean.go.kr/download/downloadPopup

Modify:

if **name** == "**main**":
json_folder_to_sqlite(
folder_path="./fullDict",
db_path="english.db",
target_language="영어"
)

RUN: python/py json_to_sqlite.py
