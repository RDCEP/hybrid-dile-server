# -*- coding: utf-8 -*-
"""
    Hybrid Dile Server
    ~~~~~~~~
    A data tile server
    :copyright: (c) 2016 by Raffaele Montella.
    :license: Apache 2.0, see LICENSE for more details.
"""
import json, sys, re, urllib, urllib2, socket, json, pydoc, cgi, os, time, inspect
from hashlib import md5
from datetime import datetime
from pymongo  import MongoClient
from flask import Flask, request, session, url_for, redirect, jsonify,\
     render_template, abort, g, flash, _app_ctx_stack
from flask import abort

from functools import wraps
from boto.s3.connection import S3Connection
from boto.s3.connection import Location

AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
with open('/home/ubuntu/.s3/AWS_ACCESS_KEY_ID', 'r') as myfile:
  AWS_ACCESS_KEY_ID=myfile.read().replace('\n', '')

with open('/home/ubuntu/.s3/AWS_SECRET_ACCESS_KEY', 'r') as myfile:
  AWS_SECRET_ACCESS_KEY=myfile.read().replace('\n', '')


def jsonp(func):
    """ Wrap json as jsonp """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            data = str(func(*args, **kwargs).data)
            content = str(callback) + '(' + data + ')'
            mimetype = 'application/javascript'
            return current_app.response_class(content, mimetype=mimetype)
        else:
            return func(*args, **kwargs)
    return decorated_function


# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE='test',
    COLLECTION='netcdf',
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('HYBRID_DILE_SERVER_SETTINGS', silent=True)

@app.teardown_appcontext
def close_database(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'db'):
        top.db.close()


def connect_db():
    """Connects to the specific database."""
    client = MongoClient()
    db = client[app.config['DATABASE']]
    return db

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'db'):
        g.db = connect_db()
    return g.db

def init_db():
    """Initializes the database."""
    db = get_db()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')

@app.route('/')
def index():
    """Shows the home page
    """
    actions=[]
    my_path=os.path.abspath(inspect.getfile(inspect.currentframe()))
    print "my_path:"+my_path
    with open(my_path) as f:
        add=False
        action=None
        for line in f:
            line=line.lstrip()
            if line.startswith("@app."):
                line=line.replace("@app.","").replace("'",'"').replace("\n","")
                method=None
                if line.startswith("route"):
                    method="get"
                    path=re.findall(r'"([^"]*)"', line)[0]
                    if path != '/':
                        action={"method":method,"url":cgi.escape(path),"params":[]}
            elif line.startswith('"""') and action is not None:
                if add is False:
                    add=True
                    action['title']=line.replace('"""','').strip()
                else:
                    add=False
                    actions.append(action)
                    action=None
            elif line.startswith("@jsonp"):
                action['jsonp']=True
            else:
                if add is True:
                    if ":example:" in line:
                        line=line.replace(":example:","").strip()
                        action['example']=request.host+line
                    elif line.startswith(":param"):
                        line=line.replace(":param:","").strip()
                        name=line.split(":")[0]
                        desc=line.split(":")[1]
                        action['params'].append({"name":name,"desc":desc})
                    elif line.startswith(":returns:"):
                        line=line.replace(":returns:","").strip()
                        action['returns']=line
                    else:
                        pass
    return render_template('layout.html',actions=actions)

"""
-------------------------------------------------------------------------------------------
"""

@app.route('/discovery/dile/by/position/<float:lon>/<float:lat>')
@jsonp
def discovery_dile_by_position(lon,lat):
    """Discovery the diles given a lon/lat position.
    :param: time: time costraits
    :param: level: level costrains
    :param: vars: variables contraints

    :example: /discovery/dile/by/position/14.28/40.55

    :returns:  geojson -- the return a feature collection with the selected diles.
    -------------------------------------------------------------------------------------------

    """
    query={}
    return jsonify(query_db(query))

@app.route('/discovery/dile/by/radius/<float:lon>/<float:lat>/<float:radius>')
@jsonp
def discovery_dile_by_range(lon,lat,radius):
    """Discovery the diles given a center point by lon/lat and a radius in km.

    :param: time: time costraits
    :param: level: level costrains
    :param: vars: variables contraints

    :example: /discovery/dile/by/position/14.25/40.25/25.0

    :returns:  geojson -- the return a feature collection with the selected diles.
    -------------------------------------------------------------------------------------------

    """
    query={}
    return jsonify(query_db(query))

@app.route('/discovery/dile/by/bbox/<float:minLon>/<float:minLat>/<float:maxLon>/<float:maxLat>')
@jsonp
def discovery_dile_by_bbox(minLon,minLat,maxLon,maxLat):
    """Discovery the diles given a bounding box.

    :param: time: time costraits
    :param: level: level costrains
    :param: vars: variables contraints

    :example: /discovery/dile/by/bbox/13.0/40.0/15.0/41.0

    :returns:  geojson -- the return a feature collection with the selected diles.
    -------------------------------------------------------------------------------------------

    """
    time=request.args.get('time')
    level=request.args.get('level')
    vars=request.args.get('vars')
    
    query= {
    "loc.geometry": {
        "$geoIntersects": {
            "$geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [ minLon, minLat ],
                        [ minLon, maxLat ],
                        [ maxLon, maxLat ],
                        [ maxLon, minLat ],
                        [ minLon, minLat ]
                    ]
                ]
                }
            }
        }
    }
    return jsonify(query_db(query))

def query_db(query):
    features=[]
    db = get_db()
    diles = db[app.config['COLLECTION']].find(query)
    for dile in diles:
        feature={
            "geometry": {
                "coordinates": [
                    [
                        [ -29.8828125, 33.7243396617476 ], 
                        [ -29.8828125, 45.5832897560063 ], 
                        [  -9.84375,   45.5832897560063 ], 
                        [  -9.84375,   33.7243396617476 ], 
                        [ -29.8828125, 33.7243396617476 ]
                    ]
                ], 
                "type": "Polygon"
            }, 
            "properties": {
                "uri": dile['uri']
            }, 
            "type": "Feature"
        }
        features.append(feature)
    result={
        "type": "FeatureCollection",
        "features": features
    }

    return result

@app.route('/select/dile')
@jsonp
def select_dile_by_uri():
    """Download a dile given a uri.

    :example: /select/dile?uri=s3:///sadiles/results/009fe65264b158898f16e991f28223d2/tmin/0/0/2/0/0

    :returns:  netcdf4 -- the return the dile.
    -------------------------------------------------------------------------------------------

    """
    uri=request.args.get('uri')
    if uri is not None:
        if uri.startswith("s3://"):
            uri=uri.replace("s3://","")
            conn = S3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
            try:
                mybucket = conn.get_bucket(uri)
                response = make_response(bucket)
                response.headers['Content-Type'] = 'application/x-netcdf'
                response.headers['Content-Disposition'] = 'attachment; filename=dile.nc4'
                return response
            except:
                pass
        abort(404)
    abort(400)