import os
import hashlib
import zlib
import struct
import collections
import difflib
import operator
import time
import urllib

IndexEntry = collections.namedtuple('IndexEntry', [
    'ctime_s', 'ctime_n', 'mtime_s', 'mtime_n', 'dev', 'ino', 'mode', 'uid',
    'gid', 'size', 'sha1', 'flags', 'path',
])


def read_file(path):

    with open(path, 'rb') as f:
        return f.read()


def write_file(path, data):

    with open(path, 'wb') as f:
        f.write(data)


def init(repo):

    try:
        os.mkdir(repo)
    except OSError:
        print(
            f"""This {repo} already exists. Try a different repository path""")
        return

    os.mkdir(os.path.join(repo, '.git'))
    for name in ['objects', 'refs', 'refs/heads']:
        os.mkdir(os.path.join(repo, '.git', name))
    write_file(os.path.join(repo, '.git', 'HEAD'),
               b'ref: refs/heads/main')
    print(f"""initialized empty repository: {repo}""")


def hash_object(data, obj_type, write=True):

    header = f"""{obj_type} {len(data)}""".encode()
    full_data = header + b'\x00' + data
    sha1 = hashlib.sha1(full_data).hexdigest()
    if write:
        path = os.path.join('.git', 'objects', sha1[:2], sha1[2:])
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            write_file(path, zlib.compress(full_data))

    return sha1


def find_object(sha1_prefix):

    if len(sha1_prefix) < 2:
        raise ValueError("hash prefix must be 2 or more characters")

    obj_dir = os.path.join('.git', 'objects', sha1_prefix[:2])
    rest = sha1_prefix[2:]
    objects = [name for name in os.listdir(obj_dir) if name.startswith(rest)]

    if not objects:
        raise ValueError(f"""object {sha1_prefix} not found""")
    if len(objects) >= 2:
        raise ValueError(
            f"""multiple objects ({len(objects)}) with prefix {sha1_prefix}""")

    return os.path.join(obj_dir, objects[0])


def read_object(sha1_prefix):

    path = find_object(sha1_prefix)
    full_data = zlib.decompress(read_file(path))
    nul_index = full_data.index(b'\x00')
    header = full_data[:nul_index]
    obj_type, size_str = header.decode().split()
    size = int(size_str)
    data = full_data[nul_index + 1:]

    assert size == len(
        data), f"""expected size -> {size} , got {len(data)} bytes"""

    return (obj_type, data)


def read_index():

    try:
        data = read_file(os.path.join('.git', 'index'))
    except FileNotFoundError:
        return []

    digest = hashlib.sha1(data[:-20]).digest()

    assert digest == data[-20:], f"""invalid index checksum"""

    signature, version, num_entries = struct.unpack('!4sLL', data[:12])

    assert signature == b'DIRC', f"""invalid index signature {signature}"""
    assert version == 2, f"""unknown index version {version}"""

    entry_data = data[12:-20]
    entries = []
    i = 0
    while i + 62 < len(entry_data):
        fields_end = i + 62
        fields = struct.unpack('!LLLLLLLLLL20sH', entry_data[i:fields_end])
        path_end = entry_data.index(b'\x00', fields_end)
        path = entry_data[fields_end:path_end]
        entry = IndexEntry(*(fields + (path.decode(),)))
        entries.append(entry)
        entry_len = ((62 + len(path) + 8) // 8) * 8
        i += entry_len

    assert len(entries) == num_entries

    return entries


def ls_files(details=False):

    for entry in read_index():
        if details:
            stage = (entry.flags >> 12) & 3
            print('{:6o} {} {:}\t{}'.format(
                entry.mode, entry.sha1.hex(), stage, entry.path))
        else:
            print(entry.path)


def get_status():

    paths = set()
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d != '.git']
        for file in files:
            path = os.path.join(root, file)
            path = path.replace('\\', '/')
            if path.startswith('./'):
                path = path[2:]
            paths.add(path)
    entries_by_path = {e.path: e for e in read_index()}
    entry_paths = set(entries_by_path)
    changed = {p for p in (paths & entry_paths)
               if hash_object(read_file(p), 'blob', write=False) !=
               entries_by_path[p].sha1.hex()}
    new = paths - entry_paths
    deleted = entry_paths - paths

    return (sorted(changed), sorted(new), sorted(deleted))


def status():

    changed, new, deleted = get_status()
    if changed:
        print('changed files:')
        for path in changed:
            print('   ', path)
    if new:
        print('new files:')
        for path in new:
            print('   ', path)
    if deleted:
        print('deleted files:')
        for path in deleted:
            print('   ', path)


def diff():

    changed, _, _ = get_status()
    entries_by_path = {e.path: e for e in read_index()}
    for i, path in enumerate(changed):
        sha1 = entries_by_path[path].sha1.hex()
        obj_type, data = read_object(sha1)
        assert obj_type == 'blob'
        index_lines = data.decode().splitlines()
        working_lines = read_file(path).decode().splitlines()
        diff_lines = difflib.unified_diff(
            index_lines, working_lines,
            '{} (index)'.format(path),
            '{} (working copy)'.format(path),
            lineterm='')
        for line in diff_lines:
            print(line)
        if i < len(changed) - 1:
            print('-' * 70)


def write_index(entries):

    packed_entries = []
    for entry in entries:
        entry_head = struct.pack('!LLLLLLLLLL20sH',
                                 entry.ctime_s, entry.ctime_n, entry.mtime_s,
                                 entry.mtime_n, entry.dev, entry.ino,
                                 entry.mode, entry.uid, entry.gid,
                                 entry.size, entry.sha1, entry.flags)

        path = entry.path.encode()
        length = ((62 + len(path) + 8) // 8) * 8
        packed_entry = entry_head + path + b'\x00' * (length - 62 - len(path))
        packed_entries.append(packed_entry)

    header = struct.pack('!4sLL', b'DIRC', 2, len(entries))
    all_data = header + b''.join(packed_entries)
    digest = hashlib.sha1(all_data).digest()
    write_file(os.path.join('.git', 'index'), all_data + digest)


def add(paths):

    paths = [p.replace('\\', '/') for p in paths]
    all_entries = read_index()
    entries = [e for e in all_entries if e.path not in paths]

    for path in paths:
        sha1 = hash_object(read_file(path), 'blob')
        st = os.stat(path)
        flags = len(path.encode())

        assert flags < (1 << 12)

        entry = IndexEntry(
            int(st.st_ctime), 0, int(st.st_mtime), 0, st.st_dev,
            st.st_ino, st.st_mode, st.st_uid, st.st_gid, st.st_size,
            bytes.fromhex(sha1), flags, path)
        entries.append(entry)

    entries.sort(key=operator.attrgetter('path'))
    write_index(entries)


def write_tree():
    tree_entries = []
    for entry in read_index():
        assert '/' not in entry.path, \
            'currently only supports a single, top-level directory'
        mode_path = '{:o} {}'.format(entry.mode, entry.path).encode()
        tree_entry = mode_path + b'\x00' + entry.sha1
        tree_entries.append(tree_entry)

    return hash_object(b''.join(tree_entries), 'tree')


def get_local_main_hash():
    main_path = os.path.join('.git', 'refs', 'heads', 'main')
    try:
        return read_file(main_path).decode().strip()
    except FileNotFoundError:
        return None


def commit(message, author=None):
    tree = write_tree()
    parent = get_local_main_hash()
    gan = os.environ['GIT_AUTHOR_NAME']
    gae = os.environ['GIT_AUTHOR_EMAIL']
    if author is None:
        author = f"""{gan} <{gae}>"""
    timestamp = int(time.mktime(time.localtime()))
    utc_offset = -time.timezone
    author_time = '{} {}{:02}{:02}'.format(
        timestamp,
        '+' if utc_offset > 0 else '-',
        abs(utc_offset) // 3600,
        (abs(utc_offset) // 60) % 60)
    lines = ['tree ' + tree]
    if parent:
        lines.append("parent " + parent)
    lines.append(f"""author {author} {author_time}""")
    lines.append(f"""committer {author} {author_time}""")
    lines.append("")
    lines.append(message)
    lines.append("")
    data = "\n".join(lines).encode()
    sha1 = hash_object(data, "commit")
    main_path = os.path.join(".git", "refs", "heads", "main")
    write_file(main_path, (sha1 + "\n").encode())
    print('committed to main: {:7}'.format(sha1))
    return sha1


def extract_lines(data):
    lines = []
    i = 0
    for _ in range(1000):
        line_length = int(data[i:i + 4], 16)
        line = data[i + 4:i + line_length]
        lines.append(line)
        if line_length == 0:
            i += 4
        else:
            i += line_length
        if i >= len(data):
            break
    return lines


def build_lines_data(lines):
    result = []
    for line in lines:
        result.append('{:04x}'.format(len(line) + 5).encode())
        result.append(line)
        result.append(b'\n')
    result.append(b'0000')
    return b''.join(result)


def http_request(url, username, password, data=None):
    password_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_manager.add_password(None, url, username, password)
    auth_handler = urllib.request.HTTPBasicAuthHandler(password_manager)
    opener = urllib.request.build_opener(auth_handler)
    f = opener.open(url, data=data)
    return f.read()


def get_remote_main_hash(git_url, username, password):
    url = git_url + '/info/refs?service=git-receive-pack'
    response = http_request(url, username, password)
    lines = extract_lines(response)
    assert lines[0] == b'# service=git-receive-pack\n'
    assert lines[1] == b''
    if lines[2][:40] == b'0' * 40:
        return None
    main_sha1, main_ref = lines[2].split(b'\x00')[0].split()
    assert main_ref == b'refs/heads/main'
    assert len(main_sha1) == 40
    return main_sha1.decode()
