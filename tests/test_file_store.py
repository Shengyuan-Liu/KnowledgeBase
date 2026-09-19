from knowledgebase.storage.file_store import FileStore


def test_save_creates_upload_directory_and_preserves_utf8_bytes(tmp_path):
    upload_dir = tmp_path / "data" / "uploads"
    store = FileStore(upload_dir)
    text = "  café 🙂\r\nSecond line.\rLast line.\n\t"

    store.save_text("file-1", text)

    assert (upload_dir / "file-1.txt").read_bytes() == text.encode("utf-8")


def test_read_existing_text_preserves_whitespace_and_line_endings(tmp_path):
    text = "  café 🙂\r\nSecond line.\rLast line.\n\t"
    (tmp_path / "file-1.txt").write_bytes(text.encode("utf-8"))
    store = FileStore(str(tmp_path))

    assert store.read_text("file-1") == text


def test_save_same_id_replaces_text_and_can_be_read_by_new_store(tmp_path):
    store = FileStore(tmp_path)
    store.save_text("file-1", "Original text is longer.")

    store.save_text("file-1", "Updated.")

    assert FileStore(tmp_path).read_text("file-1") == "Updated."
    assert [path.name for path in tmp_path.iterdir()] == ["file-1.txt"]


def test_delete_removes_only_requested_file(tmp_path):
    store = FileStore(tmp_path)
    store.save_text("file-1", "First.")
    store.save_text("file-2", "Second.")

    store.delete_text("file-1")

    assert not (tmp_path / "file-1.txt").exists()
    assert store.read_text("file-2") == "Second."
