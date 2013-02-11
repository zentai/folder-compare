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

class FileMeta(object):
    """ a structure to handle file meta and build up the file snapshot(sha-1). """
    def __init__(self, path, filename):
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(hdlr)
        self.full = path + os.sep + filename
        # TODO: enhance the performance by sha-1(atime + mtime + ctime + size)
        # (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(self.full)
        with open(self.full,'rb') as f:
            content = f.read()
        f.close()
        self.hash = hashlib.sha1(content).hexdigest()

class FolderScanner(object):
    """ scan specify folder and calc each file sha-1. """
    def __init__(self, folder):
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(hdlr)
        self.folder = folder
        if not os.path.exists(folder):
            msg = "folder: %s not found" % folder
            self.logger.error(msg)
            raise FolderNotExistsException(msg)
        self.logger.info("scan folder: %s" % folder)

    def _build_snapshot(self):
        self.logger.debug("folder: %s , build snapshot" % self.folder)
        file_hash = {}
        # recursive to calc all files sha-1, return a dict and write into snapshot
        for base, dirs, files in os.walk(self.folder):
            for filename in files:
                file_meta = FileMeta(base, filename)
                file_hash[base.replace(self.folder, '') + filename ] = file_meta.hash
        # build files.snapshot after scan
        with open(self.folder + SNAPSHOT, 'w') as f:
            f.write(str(file_hash))
        f.close()
        return file_hash

    def scan(self, snapshot = True):
        """ scan folder recursive

        Keyworkd arguments:
        snapshot
            True - lookup files.snapshot before rescan all files.
            False - rescan all file and rebuild files.snapshot

        Return:
        a dict contains relative_path, hash

        """

        file_hash = {}
        rootlen = len(self.folder)

        # lookup snapshot before scan
        if snapshot:
            if os.path.exists(self.folder + SNAPSHOT):
                fmeta = open(self.folder + SNAPSHOT, 'r')
                file_version = ast.literal_eval(fmeta.read())
                fmeta.close()
                self.logger.debug("folder: %s , read Snapshot" % self.folder)
                return file_version
            else:
                self.logger.debug('Snapshot not found.')
        file_hash = self._build_snapshot()
        return file_hash

class DiffScanner(object):
    """ compare 2 version folder, look up difference. """
    def __init__(self, new_version, old_version, snapshot = True):
        try:
            self.logger = logging.getLogger(__name__)
            self.logger.addHandler(hdlr)
            self.logger.info("Compare: %s, %s" % (new_version, old_version))
            self.new_version = FolderScanner(new_version).scan(snapshot)
            self.old_version = FolderScanner(old_version).scan(snapshot)
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