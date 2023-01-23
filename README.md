# 🗃️ NotionDB

Notion'ı database olarak yönetmek için wrapper ([notion_client](https://github.com/ramnes/notion-sdk-py)'i kullanır)

## ⭐ Örnek Kullanım

- `main.py` içerisinde örnek verilmiştir

```py
from datetime import datetime
from typing import Any, Generator, Literal, cast

from notion_client import Client
from notion_client.helpers import iterate_paginated_api

Property = Literal["title", "rich_text", "number", "select", "multi_select", "date", "people", "files", "checkbox", "url",
                   "email", "phone_number", "formula", "relation", "rollup", "created_time", "created_by",
                   "last_edited_time", "last_edited_by", "status"]

NOTION = ""
DB_UID = ""

notion = Client(auth=NOTION)
database: dict[str, Any] = {}

# Data load
database.clear()
for pages in read(notion, DB_UID):
    for page in pages:
        if get_property(page, "ID") is None: continue
        data = Any(
            id=get_property(page, "ID"),
            uid=page["id"],
            status=get_property(page, "Status"),
            date=get_property(page, "Last edited time"),
            exists=get_property(page, "Exists"),
            assing=get_property(page, "Assing"),
        )
        database.update({data.id: data})

# Data save | update
data: Any = {}
properties: list[tuple[str, Property, Any]] = [
    ("Name", "title", str(data.id)),
    # ("Last edited time", "date", data.date), can't be updated
    ("ID", "number", data.id),
    ("Status", "select", data.status),
    ("Exists", "checkbox", data.exists),
    ("Assing", "multi_select", data.assing),
]
if data.id in database:
    data = data[data.id]
    assert data.uid, "UID is not defined"
    update(notion, data.uid, properties)
    # f"{self.game} hesabı güncellendi: {data.id}"
else:
    page = insert(notion, DB_UID, properties)
    data.uid = page["id"]
    # f"{self.game} hesabı kaydedildi: {data.id}"
database.update({data.id: data})

# Data deletion
delete(notion, data.uid)
```

## 🪪 License

Copyright 2023 Yunus Emre Ak ~ YEmreAk.com

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.a
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
