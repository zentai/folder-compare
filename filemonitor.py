import sys, os
import time
import filecmp
import hashlib
import ast
SNAPSHOT = "\\files.snapshot"

class FileMeta(object):
    """
    FileMeta - store the file information.
    """
    def __init__(self, full, base, file, size):
        self.full = full + '\\' + file
        self.base = base
        self.file = file
        self.relative_path = base + '\\' + file
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
        return sha1.hexdigest()

        
def scan(folder='.'):
    file_versions = {}
    rootlen = len(folder)
    
    # lookup snapshot before scan
    if os.path.exists(folder + SNAPSHOT):
        fmeta = open(folder + SNAPSHOT, 'r')
        file_version = ast.literal_eval(fmeta.read())
        fmeta.close()
        return file_version
    
    i = 0
    for base, dirs, files in os.walk(folder):
        for file in files:
            (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(base+'/'+file)
            file_meta = FileMeta(base, base.replace(folder+'\\', ''), file, size)
            file_versions[file_meta.relative_path] = file_meta.hash
    
    # store snapshot after scan
    fmeta = open(folder + SNAPSHOT, 'w')            
    fmeta.write(str(file_versions))
    fmeta.close()
    
    return file_versions
    
def diff_list(version_old, version_new):
    f = open('change_list.txt', 'w')
    diff = {}
    for key, value in sorted(version_new.items()):
        new_file_hash = value
        try:
            old_file_hash = version_old[key]
            if new_file_hash != old_file_hash:
                diff[key] = value
                s = "%s \t %s \n" % (key, ' changed')
                f.write(s)
            else:
                s = "%s \t %s \n" % (key, '')
                f.write(s)
        except KeyError:
            diff[key] = value
            s = "%s \t %s \n" % (key, ' new file')
            f.write(s)
    f.close()
    return diff

def Release(diff):    
    command = ''
    for key, value in diff.items():
        #print "size: %(size)s \t reason: %(reason)s \t %(file)s \t folder: %(folder)s" % {'file': key , 'size': value.size, 'folder': value.base, 'reason': value.reason}
        st = value.pack()
        folder_list[value.base] = value
        command += st+'\n'
    
    mkdirs = ''
    mkdirs += 'RD /S release_pack /Q \n'
    for key in folder_list:
        mkdirs += 'mkdir %s\\%s \n' % ('release_pack', key)
        
    release_bat = file('release.bat', 'w')
    release_bat.write(mkdirs)
    release_bat.write(command)
    release_bat.write("move update.bat release_pack\\dist\\")
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
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "========================================="
        print "= Usage: d:\\filemonitor.py new_version_path old_version_path" 
        print "= Default: 3.0.26 D:\\python_project\\FingerPrint\\release D:\\python_project\\FingerPrint\\Genecodev3.0.25" 
        print "========================================="
        release_version = "3.0.26"
        new_path = 'D:\\python_project\\FingerPrint\\release'
        old_path = 'D:\\python_project\\FingerPrint\\Genecodev3.0.25'
    else:
        release_version = sys.argv[1]
        new_path = sys.argv[2]
        old_path = sys.argv[3]
    versions_new = scan(new_path)
    versions_old = scan(old_path)
    diff = diff_list(versions_old, versions_new)
    folder_list = {}
    #Release(diff)
    #BuildUpdateFile(release_version, diff)
