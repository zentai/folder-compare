import sys
import os
import filecmp
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
    def __init__(self, full, base, file, size):
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(hdlr)
        self.full = full + os.sep + file
        self.base = base
        self.file = file
        self.relative_path = base + os.sep + file
        self.size = size
        self.reason = ''
        self.hash = self._hash()

    def _hash(self):
        filepath = self.full
        sha1 = hashlib.sha1()
        f = open(filepath, 'rb')
        try:
            sha1.update(f.read())
        finally:
            f.close()
        self.logger.debug("%s - %s" % (sha1.hexdigest(), filepath))
        return sha1.hexdigest()

class FolderScanner(object):
    """ scan specify folder and calc each file sha-1. """
    def __init__(self, folder):
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(hdlr)
        self.folder = folder
        if not os.path.exists(folder):
            msg = "%s not found" % folder
            self.logger.error(msg)
            raise FolderNotExistsException(msg)
        self.logger.info("scan folder: %s" % folder)

    def scan(self, snapshot = True):
        """ scan folder recursive

        Keyworkd arguments:
        snapshot
            True - lookup files.snapshot before rescan all files.
            False - rescan all file and rebuild files.snapshot

        Return:
        a dict contains relative_path, hash

        """

        file_versions = {}
        rootlen = len(self.folder)

        # lookup snapshot before scan
        if snapshot:
            if os.path.exists(self.folder + SNAPSHOT):
                fmeta = open(self.folder + SNAPSHOT, 'r')
                file_version = ast.literal_eval(fmeta.read())
                fmeta.close()
                self.logger.debug("folder: %s , scan mode: %s" % (self.folder, "snapshot"))
                return file_version
        self.logger.debug("folder: %s , scan mode: %s" % (self.folder, "deep"))
        i = 0
        for base, dirs, files in os.walk(self.folder):
            for f in files:
                file_meta = FileMeta(base, base.replace(self.folder, ''), f, size)
                file_versions[file_meta.relative_path] = file_meta.hash
        # build files.snapshot after scan
        fmeta = open(self.folder + SNAPSHOT, 'w')
        fmeta.write(str(file_versions))
        fmeta.close()
        self.logger.info("scan folder: %s completed" % self.folder)
        return file_versions

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
        diff = {}
        for key, value in sorted(self.new_version.items()):
            new_file_hash = value
            try:
                old_file_hash = self.old_version[key]
                # Updated file
                if new_file_hash != old_file_hash:
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

import sys
logging.basicConfig(level = logging.INFO)

# Get an instance of a logger
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
        x = DiffScanner(new_path, old_path, snapshot = True)
        changelist = x.scan()
        f = open(CHANGELOG, 'w')
        for filename, status in changelist.items():
            f.write("[%s] %s \n" % (status, filename))
        f.close()