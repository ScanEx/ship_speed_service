import cherrypy, json, os, couchdb, subprocess

class Root(object):
    
    def __init__(self):

        # cherrypy.log.screen = False
        self.server = couchdb.Server()
        self.db = self.server['sentinel_1']
        self.data_dir = r'y:\Kosmosnimki\alt_proc\sentinel-1\\'

    @cherrypy.expose
    def index(self):

        return 'Hello!'

    @cherrypy.expose
    def ship_speed(self, sceneid, ship, wakes):

        view = self.db.view('scenes_by_gmx_sceneid/scenes_by_gmx_sceneid')
        for row in view[sceneid[:32]]:
            if self.db[row.id]['gmx_sceneid']==sceneid:
                break
        else:
            return json.dumps( dict(error='SceneID not in DB') )
        scene = self.db[row.id]
        date = scene['date']
        zipfile = self.data_dir + 'dates/%s/%s/' % (date[0:4], date) + scene['filename'] + '.zip'
        if not os.path.exists(zipfile):
            print('No zip file')
            return json.dumps( dict(error='No zip file'))

        if not os.path.exists(sceneid):
            cmd = 'C:/alt_proc/soft/7-Zip/7z.exe x -y -r -o%s %s' % (sceneid, zipfile)
            subprocess.call(cmd)

        uuid = self.server.uuids(1)[0]
        with open(uuid + '.ship', 'w') as f:
            f.write(ship)
        with open(uuid + '.wakes', 'w') as f:
            f.write(wakes)
        cmd = r'c:\alt_proc\soft\s1-ships-speed\bin\ShipSpeed.exe ' + \
              r'--i_raster %s\%s.SAFE\manifest.safe ' % (sceneid, scene['filename']) + \
              r'--i_ships %s.ship ' % uuid + \
              r'--i_wakes %s.wakes ' % uuid + \
              r'--ofile %s.out ' % uuid
        print(cmd)
        subprocess.call(cmd)

        if not os.path.exists('%s.out ' % uuid):
            return json.dumps( dict(error='No result'))
        with open('%s.out ' % uuid) as f:
            speed = f.read()

        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'

        return speed

config = {
    'global': {
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 1661,
        },
}
cherrypy.quickstart(Root(), '/', config = config)