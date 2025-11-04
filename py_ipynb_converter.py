from pathlib import Path
import nbformat
import sys

def normalize_path_input(raw):
    raw = raw.strip()
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        raw = raw[1:-1]
    return Path(raw).expanduser()

def py_to_ipynb(py_path: Path, out_path: Path):
    text = py_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    blocks = []
    cur = []
    for ln in lines:
        if ln.strip() == "":
            if cur:
                blocks.append("".join(cur).rstrip("\n") + "\n")
                cur = []
        else:
            cur.append(ln)
    if cur:
        blocks.append("".join(cur))

    nb = nbformat.v4.new_notebook()
    nb.cells = [nbformat.v4.new_code_cell(source=b) for b in blocks] if blocks else []
    nbformat.write(nb, str(out_path))
    print(f"wrote {len(nb.cells)} cells to {out_path}")

def ipynb_to_py(nb_path: Path, out_path: Path):
    nb = nbformat.read(str(nb_path), as_version=4)
    parts = []
    for cell in nb.cells:
        if cell.get("cell_type") == "markdown":
            src = cell.get("source", "")
            if isinstance(src, list):
                src = "".join(src)
            commented = "\n".join(("# " + l) if l.strip() else "#" for l in src.splitlines())
            parts.append(commented.rstrip())
        elif cell.get("cell_type") == "code":
            src = cell.get("source", "")
            if isinstance(src, list):
                src = "".join(src)
            parts.append(src.rstrip("\n") + "\n")
        else:
            src = str(cell.get("source", ""))
            parts.append("# [unknown cell type]\n" + src.rstrip("\n") + "\n")
    combined = "\n\n".join(p.rstrip() for p in parts).rstrip() + "\n"
    out_path.write_text(combined, encoding="utf-8")
    print(f"wrote {len(nb.cells)} cells to {out_path}")

def ask(prompt, default=None):
    res = input(prompt).strip()
    if res == "" and default is not None:
        return default
    return res

def convert_file(file_path: Path, mode: str):
    # Only process the correct file types
    if mode == "1" and file_path.suffix != ".ipynb":
        print(f"skipping non-ipynb file: {file_path}")
        return
    if mode == "2" and file_path.suffix != ".py":
        print(f"skipping non-py file: {file_path}")
        return

    out_path = file_path.with_suffix(".py" if mode == "1" else ".ipynb")
    try:
        if mode == "1":
            ipynb_to_py(file_path, out_path)
        else:
            py_to_ipynb(file_path, out_path)
    except Exception as e:
        print(f"conversion failed for {file_path}: {e}")
        return

    # Ask if user wants to delete original file
    delete_orig = ask(f"Do you want to delete the original file ({file_path})? (y/n): ", default="n").lower()
    if delete_orig in ("y", "yes"):
        try:
            file_path.unlink()
            print(f"deleted {file_path}")
        except Exception as e:
            print(f"failed to delete {file_path}: {e}")
    else:
        print(f"original file left: {file_path}")

def main():
    print("convert_py_ipynb - simple converter (py <-> ipynb)")

    # 1. Kind of transformation
    mode = ask("Choose transformation: 1) ipynb -> py   2) py -> ipynb: ")
    if mode not in ("1", "2"):
        print("invalid choice. exiting.")
        sys.exit(1)

    # 2. Path of the file or folder
    raw = ask("Enter the path to the file or folder (quotes accepted): ")
    path = normalize_path_input(raw)
    if not path.exists():
        print(f"path not found: {path}")
        sys.exit(1)

    if path.is_dir():
        # process all files in folder and subfolders recursively
        pattern = "*.ipynb" if mode == "1" else "*.py"
        files = list(path.rglob(pattern))  # rglob for recursive search
        if not files:
            print(f"No matching files ({pattern}) found in folder {path}")
            sys.exit(1)
        for f in files:
            convert_file(f, mode)
    else:
        # single file
        convert_file(path, mode)

if __name__ == "__main__":
    main()