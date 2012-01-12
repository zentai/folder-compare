import sys, os
import time
import filecmp
class Version(object):
    """
    Version - store the file information.
    """
    def __init__(self, full, base, file, size):
        self.full = full + '\\' + file
        self.base = base
        self.file = file
        self.size = size
        self.reason = ''
    
    def pack(self, dictionary = { 'source': 'FingerPrint\\release', 'dest': 'release_pack' }):
        dictionary['file'] = self.base+'\\'+self.file
        dest = dictionary['dest']+'\\'+self.base
        return "copy %(source)s\\%(file)s %(dest)s\\%(file)s" % dictionary
    
    def save(self, release_version, dictionary = { 'source': '.', 'dest': '..\\..\\' }):
        dictionary['file'] = self.base+'\\'+self.file
        dictionary['source'] = (self.base+'\\'+self.file).replace('dist', 'update\\'+release_version)
        return "copy %(source)s %(file)s /Y" % dictionary
    
def scan(folder='.'):
    file_versions = {}
    rootlen = len(folder)
    i = 0
    for base, dirs, files in os.walk(folder):
        for file in files:
            # print "base: %s, dirs: %s, " % (base, dirs)
            (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(base+'/'+file)
            version = Version(base, base.replace(folder+'\\', ''), file, size)
            file_versions[version.base + "\\" + version.file] = version
    return file_versions
    
def diff_size(version_old, version_new):
    f = open('change_list.txt', 'w')
    diff = {}
    for key, value in sorted(version_new.items()):
        file = value
        try:
            file2 = version_old[key]
            if not filecmp.cmp(file.full, file2.full, shallow=False):
            # if file.size != file2.size:
                file2.reason = 'size diff'
                diff[key] = file2
                s = "%s \t %s \n" % (file2.full, "diff file")
                f.write(s)
            else:
                s = "%s \t %s \n" % (file2.full, "same file")
                f.write(s)
        except KeyError:
            file.reason = 'new file'
            diff[key] = file
            s = "%s \t %s \n" % (file.full, file.reason)
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
    diff = diff_size(versions_old, versions_new)
    folder_list = {}
    Release(diff)
    BuildUpdateFile(release_version, diff)
