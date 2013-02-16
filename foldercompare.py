import sys
import os
import hashlib
import ast
import logging

SNAPSHOT = os.sep + "files.snapshot"
CHANGELOG = "change_list.log"

class FolderNotExistsException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def _calc_hash(path, filename):
    """ the algo build up the file snapshot(sha-1). """
    full = path + os.sep + filename
    with open(full,'rb') as f:
        content = f.read()
    f.close()
    return hashlib.sha1(content).hexdigest()
    # TODO: enhance the performance by sha-1(atime + mtime + ctime + size)
    # (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(full)
    # self.hash = hashlib.sha1(str(mtime) + str(size)).hexdigest()

def _build_snapshot(folder):
    """ iterative all files and build snapshot dict, format: { relative path: hash }
        we are using relative path to identifier the file in difference base folder.
        ex:
        c:\the_new_version_folder\src\core\logic\shoppingcart\calc.py
        c:\the_old_version_folder\src\core\logic\shoppingcart\calc.py
        |<------- base --------->| <------ relative_path ----------->|
    """
    logger.debug("folder: %s , build snapshot" % folder)
    file_hash = {}
    for base, dirs, files in os.walk(folder):
        for filename in files:
            file_hash[base.replace(folder, '') + filename ] = _calc_hash(base, filename)

    # build files.snapshot after scan
    with open(folder + SNAPSHOT, 'w') as f:
        f.write(str(file_hash))
    f.close()

    return file_hash

def _scan_folder(folder, snapshot = True):
    # check folder exists
    if not os.path.exists(folder):
        raise FolderNotExistsException("folder: %s not found" % folder)

    logger.info("scan folder: %s" % folder)
    file_hash = {}
    # lookup snapshot before scan
    if snapshot:
        if os.path.exists(folder + SNAPSHOT):
            fmeta = open(folder + SNAPSHOT, 'r')
            file_version = ast.literal_eval(fmeta.read())
            fmeta.close()
            logger.debug("folder: %s , read Snapshot" % folder)
            return file_version
        else:
            logger.debug('Snapshot not found.')
    file_hash = _build_snapshot(folder)
    return file_hash

class DiffScanner(object):
    """ compare 2 version folder, look up difference. """
    def __init__(self, new_version, old_version, snapshot = True):
        try:
            self.logger = logging.getLogger(__name__)
            self.logger.addHandler(hdlr)
            self.logger.info("Compare: %s, %s" % (new_version, old_version))
            self.new_version = _scan_folder(new_version, snapshot)
            self.old_version = _scan_folder(old_version, snapshot)
        except FolderNotExistsException as e:
            raise e

    def scan(self):
        """DiffScanner.scan()
        compare two folder file's sha-1
        return:
        dist = {${relative_path}, ${status}}
        ${status} = [U|+|-]
        U = update
        + = new files
        - = remove files
        """
        diff = {}
        for key, new_file_hash in sorted(self.new_version.items()):
            try:
                # Updated file
                if new_file_hash != self.old_version[key]:
                    diff[key] = "U"
                    self.logger.debug("%s %s \n" % ('[U]', key))
                # Non-update file
                else:
                    pass
            except KeyError:
                # New File
                diff[key] = "+"
                self.logger.debug("%s %s \n" % ('[+]', key))

        for key in sorted(self.old_version):
            # removed file
            if not key in self.new_version:
                diff[key] = "-"
                self.logger.debug("%s %s \n" % ('[-]', key))
        self.logger.info("Compare completed")
        return diff

# logging configuration
logging.basicConfig(level = logging.INFO)
hdlr = logging.FileHandler('info.log')
format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s():%(lineno)s %(message)s'
formatter = logging.Formatter(format)
hdlr.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(hdlr)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "========================================="
        print "= Usage: $ python foldercompare.py ${new_version_path} ${old_version_path}"
        print "========================================="
    else:
        new_path = sys.argv[1]
        old_path = sys.argv[2]
        x = DiffScanner(new_path, old_path, snapshot = False)
        changelist = x.scan()
        f = open(CHANGELOG, 'w')
        for filename, status in changelist.items():
            f.write("[%s] %s \n" % (status, filename))
        f.close()