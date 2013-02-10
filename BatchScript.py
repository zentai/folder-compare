import sys, os
import time
import filecmp
import hashlib
import ast
import logging
from filemonitor import *

class BatchScript(object):
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def _build_folders(self, diff):
        folders = []
        for file in diff:
            dir = os.path.dirname(file)
            if dir in folders:
                continue
            folders.append(dir)
        return folders

    def copy(self, diff):
        folders = self._build_folders(diff)

        str_copy = "copy %(source_base)s%(relativepath)s %(target_base)s%(relativepath)s \n"
        str_mkdir = "mkdir %(target_base)s%(relativepath)s \n"
        str_rddir = "RD /S %(target_base)s /Q  \n"

        clean = str_rddir % {'source_base' : self.source, 'target_base' : self.target, 'relativepath': ''}

        mkdirs = ''
        for folder in folders:
            mkdirs += str_mkdir % {'source_base' : self.source, 'target_base' : self.target, 'relativepath': folder}

        copy = ''
        for file, change in diff.items():
            if change == '-':
                continue
            copy += str_copy % {'source_base' : self.source, 'target_base' : self.target, 'relativepath': file}

        release_bat = open('release.bat', 'w')
        release_bat.write(clean)
        release_bat.write(mkdirs)
        release_bat.write(copy)
        release_bat.close()

def BuildUpdateFile(release_version, diff):
    command = ''
    for key, value in diff.items():
        #print "size: %(size)s \t reason: %(reason)s \t %(file)s \t folder: %(folder)s" % {'file': key , 'size': value.size, 'folder': value.base, 'reason': value.reason}
        st = value.save(release_version)
        folder_list[value.base] = value
        command += st+'\n'

    mkdirs = ''
    for key in folder_list:
        mkdirs += 'mkdir %s \n' % key

    update_bat = file('update.bat', 'w')
    update_bat.write(mkdirs)
    update_bat.write(command)
    update_bat.close()

import sys
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s():%(lineno)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

hdlr = logging.FileHandler('info.log')
format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s():%(lineno)s %(message)s',
format = '%(asctime)s %(levelname)s %(message)s'
formatter = logging.Formatter(format)
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "========================================="
        print "= Usage: d:\\filemonitor.py new_version_path old_version_path"
        print "= Default: 3.0.26 D:\\python_project\\FingerPrint\\release D:\\python_project\\FingerPrint\\Genecodev3.0.25"
        print "========================================="
        release_version = "3.0.26"
        new_path = 'D:\\python_project\\ReleaseRepository\\Genecodev3.0.31'
        old_path = 'D:\\python_project\\ReleaseRepository\\Genecodev3.0.30'
    else:
        release_version = sys.argv[1]
        new_path = sys.argv[2]
        old_path = sys.argv[3]
    x = DiffScanner(new_path, old_path, snapshot = True)
    diff = x.scan()

    bs = BatchScript(new_path, "release_pack")
    bs.copy(diff)
