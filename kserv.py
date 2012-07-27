#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, socket, shutil
from subprocess import Popen, PIPE
from tempfile   import NamedTemporaryFile

host = ''
port = 50000
backlog = 5
size = 1024
autoadd = True
keydir = 'keys'
prepend = 'invited-'

are = re.compile('^ssh-[rd]sa$')
mre = re.compile('^[a-z0-9\-_\.]+$')
nre = re.compile('^[a-z0-9]+$')

def add_key (alg, key, nm):
    try:
        name, machine = nm.split('@')
    except ValueError:
        return False

    name = name

    d = './' + keydir + '/' + machine
    kf = d + '/' + prepend + name + '.pub'

    if  not mre.match (machine) or not nre.match (name) or not are.match (alg):
        return False

    if os.path.exists(kf):
        print 'ignoring duplicate key for:', kf
        return True # we do this so that we don't leak info

    f = NamedTemporaryFile(delete=False)
    f.file.write ('%s %s %s@%s\n' % (alg, key, name, machine))
    f.close()

    p = Popen(['ssh-vulnkey', f.name], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    p.stdin.close()
    if p.stderr.read().__len__() > 1:
        f.unlink (f.name)
        return False

    if not os.path.exists (d):
        os.makedirs (d)

    shutil.move (f.name, kf)
    print "Imported", kf
    return True

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host,port))
s.listen(backlog)


print "Ready to serve on port %d" % (port)
while 1:
    client, address = s.accept()
    data = client.recv(size)

    if data:
        data = data.rstrip()
        da = data.split(' ')
        if da.__len__() == 3:
            if add_key (*da):
                client.send('OK')
            else:
                client.send('EMALFORMED')
                client.close()
        elif da.__len__() == 2:
            (alg, key) = da
            client.send('ENONAME')
        else:
            client.send('EMALFORMED')

    client.close()
