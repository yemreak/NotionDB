"""Notion'ı database olarak kullanmayı sağlar"""

from datetime import datetime
from typing import Any, Generator, Literal, cast

from notion_client import Client
from notion_client.helpers import iterate_paginated_api

Property = Literal["title", "rich_text", "number", "select", "multi_select", "date", "people", "files", "checkbox", "url",
                   "email", "phone_number", "formula", "relation", "rollup", "created_time", "created_by",
                   "last_edited_time", "last_edited_by", "status"]


def create_property(name: str, type_: Property, value: Any) -> dict[str, dict[str, Any]]:
    """Property paramteresini oluşturur

        - Oluşturulan verileri birleştirmek için `|` kullanın
            - `create_property("Name", "title", "Test3")`
            - ` | create_property("Price", "number", 100)`
        """
    if name == "Name": params = [{"text": {"content": value}}]
    elif type_ == "select": params = {"name": value}
    elif type_ == "multi_select": params = [{"name": val} for val in value]
    elif type_ == "relation":
        if isinstance(value, (list, set)): params = [{"id": val} for val in value]
        else: params = [{"id": value}]
    elif type_ == "rich_text": params = [{"text": {"content": value}}]
    else: params = value
    return {name: {type_: params}}


def get_property(record: dict[str, Any], name: str) -> Any:
    """Özellik değerini döndürür
    
    - `title` için `"Name"` verilir ve `str` döndürür
    - `relation` için `page_uid` tutan `str` veya `list[str]` döndürür
    - `rich_text` için `str` döndürür
    - `select` için `str` döndürür
    - `multi_select` için `list[str]` döndürür
    """
    type_: Property = record["properties"][name]["type"]
    property_ = record["properties"][name][type_]
    if name == "Name": return "".join([val["text"]["content"] for val in property_])
    elif type_ == "rich_text": return "".join([val["plain_text"] for val in property_])
    elif type_ == "select": return property_["name"] if property_ else None
    elif type_ == "multi_select": return [val["name"] for val in property_] if property_ else []
    elif type_ == "relation":
        if not record["properties"][name]["has_more"]:
            return property_[0]["id"]
        return [page["id"] for page in property_]
    elif type_ == "last_edited_time":
        return datetime.strptime(property_, '%Y-%m-%dT%H:%M:%S.%fZ')
    return property_


def set_property(notion: Client, record: dict[str, Any], name: str, value: Any) -> None:
    """Özelliğin değerini değiştirir ve sayfanın güncel içerik bilgilerini günceller

        - `title` için `"Name"` verilir ve `str` alır
        - `multi_select` için `list[str]` alır
        - `select` için `str` alır
        - `relation` için `page_uid` tutan `str` veya `list[str]` alır
        """
    if get_property(record, name) == value: return  # Zaten aynı ise değiştirme
    type_: Property = record["properties"][name]["type"]
    property_ = create_property(name, type_, value)
    page = notion.pages.update(record["id"], properties=property_)
    record.update(cast(dict[str, Any], page))


def insert(notion: Client, uid: str, properties: list[tuple[str, Property, Any]]) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        notion.pages.create(
            parent={"database_id": uid},
            properties={k: v
                        for p in properties for k, v in create_property(*p).items()},
        )
    )


def read(notion: Client, uid: str) -> Generator[list[dict[str, Any]], None, None]:
    """Notion API 100'er 100'er verdiği için generator olarak döndürür"""
    yield from iterate_paginated_api(notion.databases.query, database_id=uid)


def delete(notion: Client, page_uid: str):
    """Veritabanından kayıt siler"""
    return notion.pages.update(page_uid, archived=True)


def update(notion: Client, uid: str, properties: list[tuple[str, Property, Any]]) -> dict[str, Any]:
    """Veritabanındaki kaydı günceller"""
    return cast(
        dict[str, Any],
        notion.pages.update(uid, properties={k: v
                                             for p in properties for k, v in create_property(*p).items()})
    )


if __name__ == "__main__":
    NOTION = ""
    DB_UID = ""

    notion = Client(auth=NOTION)
    database: dict[str, Any] = {}

    # Data load
    database.clear()
    for pages in read(notion, DB_UID):
        for page in pages:
            if get_property(page, "ID") is None: continue
            account = Any(
                id=get_property(page, "ID"),
                uid=page["id"],
                status=get_property(page, "Status"),
                date=get_property(page, "Last edited time"),
                exists=get_property(page, "Exists"),
                assing=get_property(page, "Assing"),
            )
            database.update({account.id: account})

    # Data save | update
    data: Any = {}
    properties: list[tuple[str, Property, Any]] = [
        ("Name", "title", str(data.id)),
        # ("Last edited time", "date", data.date), can't be updated
        ("ID", "number", data.id),
        ("Status", "select", data.status),
        ("Exists", "checkbox", data.phone_verification),
        ("Assing", "multi_select", data.assing),
    ]
    if data.id in database:
        data = data[data.id]
        assert data.uid, "Account UID is not defined"
        update(notion, data.uid, properties)
        # f"{self.game} hesabı güncellendi: {data.id}"
    else:
        page = insert(notion, DB_UID, properties)
        data.uid = page["id"]
        # f"{self.game} hesabı kaydedildi: {data.id}"
    database.update({data.id: data})

    # Data deletion
    delete(notion, data.uid)
