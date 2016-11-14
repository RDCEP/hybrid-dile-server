# -*- coding: utf-8 -*-
"""
    Hybrid Dile Server
    ~~~~~~~~
    A data tile server
    :copyright: (c) 2016 by Raffaele Montella & Sergio Apreda.
    :license: Apache 2.0, see LICENSE for more details.
"""
import  geojson, json, sys, re, urllib, urllib2, socket, json, pydoc, cgi, os, time, inspect

from hashlib  import md5
from datetime import datetime
from pymongo  import MongoClient

from geojson  import Feature, Point, FeatureCollection
from ast      import literal_eval

from diles.dilefactory       import DileFactory
from utils.querybuildermongo import QueryBuilderMongo

from flask import Flask
from flask import Response
from flask import request
from flask import jsonify
from flask import current_app
from flask import make_response
from flask import session
from flask import url_for
from flask import redirect
from flask import render_template
from flask import abort
from flask import g
from flask import flash
from flask import _app_ctx_stack

from functools import wraps
from functools import update_wrapper

from boto.s3.connection import S3Connection
from boto.s3.connection import Location

AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
with open('/home/ubuntu/.s3/AWS_ACCESS_KEY_ID', 'r') as myfile:
  AWS_ACCESS_KEY_ID=myfile.read().replace('\n', '')

with open('/home/ubuntu/.s3/AWS_SECRET_ACCESS_KEY', 'r') as myfile:
  AWS_SECRET_ACCESS_KEY=myfile.read().replace('\n', '')


#### CROSSDOMAIN DECORATOR ####

def crossdomain(origin=None, methods=None, headers=None, max_age=21600, attach_to_all=True, automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers
            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            h['Access-Control-Allow-Credentials'] = 'true'
            h['Access-Control-Allow-Headers'] = "Origin, X-Requested-With, Content-Type, Accept, Authorization"
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)

    return decorator


#### JSONP DECORATOR ####
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
    DATABASE         ='test',
    COLLECTION_DILES ='diles',
    COLLECTION_FILES ='files',
    DEBUG            =True,
    SECRET_KEY       ='development key',
    USERNAME         ='admin',
    PASSWORD         ='default',
    LOCATION         = 'loc.geometry',
    TIME             = 'time' 
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

def query_diles_db(query):

    db = get_db()
    return list(db[app.config['COLLECTION_DILES']].find(query[0],query[1]))


def query_files_db(query):

    db = get_db()
    return list(db[app.config['COLLECTION_FILES']].find(query[0],query[1]))


def aggregate_result_diles(pipeline):

    db = get_db()
    return list(db[app.config['COLLECTION_DILES']].aggregate(pipeline))


def aggregate_result_diles(pipeline):

    db = get_db()
    return list(db[app.config['COLLECTION_FILES']].aggregate(pipeline))


def getUrlParam(name):
  
  value=None
  
  try:
    value=request.args.get(name)
  except:
    pass
  if value is None:
    try:
      value=request.form[name]
    except:    
      pass

  return value


def getKeyValue(dictionary,param):

    if param in dictionary:
        return dictionary[param]
    
    else:
        for key in dictionary:
            if type(dictionary.get(key)) == type(dict()):
                return getKeyValue(dictionary.get(key),param)

    return None


def polyToBB(feature):
    
    coords  = feature['geometry']['coordinates']
    
    bb = {
            "lon_min" : float(coords[0][0]),
            "lon_max" : float(coords[2][0]),
            "lat_min" : float(coords[0][1]),
            "lat_max" : float(coords[2][1])
         }
    
    return bb


def jsonToDict(param):
    
    try:
        jstring   = json.loads(json.dumps(param))
        item      = literal_eval(jstring)
    except:
        return None
    else:
        return item

def geojsonToDict(param):

    try:
        jstring   = geojson.loads(geojson.dumps(param))
        item = literal_eval(jstring)
    except:
        return None
    else:
        return item  

def getDimentions(dimensions, qbm):

    if dimensions is not None:
        
        for dim in dimensions:            
            
            d = dimensions[dim]
            
            if dim.lower() == 'time':           
                qbm.addField(qbm.queryTimeRange(dim.lower(),d[0],d[1]))
            else:
                qbm.addField(qbm.queryRange(dim.lower(),d[0],d[1]))

    return qbm


def getFeature(feature, qbm):

    if feature['geometry']['type'] == 'Point':

        c = feature['geometry']['coordinates']
        qbm.addField(qbm.queryIntersectPoint(app.config['LOCATION'], float(c[0]), float(c[1])))        
    
    elif feature['geometry']['type'] == 'Polygon':
    
        bb = polyToBB(feature) 
        qbm.addField(qbm.queryIntersectBbox(app.config['LOCATION'], bb))
    else:
        pass

    return qbm

def uvarToVar(uvar):

    return literal_eval(uvar)

def getVariables(var,qbm):
    
    if isinstance(var,tuple) or isinstance(var,list):
        
        queries = [{"variable": x } for x in var if isinstance(x,basestring)]
        
        try:
            qbm.queryLogical('or',queries)
        except:
            raise

    elif isinstance(var,basestring):

        try:
            qbm.addField({"variable": var})
        except:
            raise

    return qbm




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
            elif line.startswith("@crossdomain"):
                action['crossdomain']=True
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

@app.route('/test')
def test():
    
    qbm = QueryBuilderMongo()

    param = getUrlParam('var')
    var = uvarToList(param) 

    qbm = getVariables(var, qbm)

    return jsonify(qbm.getQuery())



@app.route('/discovery/dile/by/feature')
def discovery_dile_by_feature():

    """Discovery the diles given a Feature (Point or Polygon)
 
    :param: feature:    json feature  
    :example: /discovery/dile/by/feature?feature={'geometry'%3A+{'type'%3A+'Point'%2C+'coordinates'%3A+[-90%2C+42.293564192170095]}%2C+'type'%3A+'Feature'%2C+'properties'%3A+{}}
    :returns:  geojson -- return a feature collection with the selected diles.
    -------------------------------------------------------------------------------------------
    """

    qbm = QueryBuilderMongo()

    f_param = getUrlParam('feature')    
    d_param = getUrlParam('dimensions')

    if f_param is not None:
        feature = geojsonToDict(f_param)       
        if feature is not None:
            qbm = getFeature(feature, qbm)
        else:
            return "ERROR: -feature- invalid geojson syntax"


    if d_param is not None:
        dimensions = jsonToDict(d_param)
        if dimensions is not None:
            qbm = getDimentions(dimensions, qbm)
        else:
            return "ERROR: -dimensions- invalid json syntax"

    qbm.addProjection({"_id": 0, "uri" : 1})

    return jsonify(query_diles_db(qbm.getQuery()))
    


@app.route('/discovery/dile/by/position/<lon>/<lat>')
@jsonp
def discovery_dile_by_position(lon,lat):
    """Discovery the diles given a lon/lat position.

    :example: /discovery/dile/by/position/-135.0/22.5
    :param: dimensions: json document
    :returns:  geojson -- the return a feature collection with the selected diles.
    -------------------------------------------------------------------------------------------

    """

    qbm   = QueryBuilderMongo()

    d_param = getUrlParam('dimensions')

    if d_param is not None:
        dimensions = jsonToDict(d_param)
    if dimensions is not None:
        qbm = getDimentions(dimensions, qbm)
    else:
        return "ERROR: -dimensions- invalid json syntax" 

    query = qbm.queryIntersectPoint(app.config['LOCATION'], float(lon), float(lat))

    qbm.addField(query)
    qbm.addProjection({"_id": 0, "uri" : 1})

    return jsonify(query_diles_db(qbm.getQuery()))

    

@app.route('/discovery/dile/by/radius/<lon>/<lat>/<radius>')
@jsonp
def discovery_dile_by_radius(lon,lat,radius):
    """Discovery the diles given a center point by lon/lat and a radius in km.

    :example: /discovery/dile/by/radius/-135.0/22.5/5000.0

    :returns:  geojson -- the return a feature collection with the selected diles.
    -------------------------------------------------------------------------------------------

    """

    qbm = QueryBuilderMongo()

    d_param = getUrlParam('dimensions')

    if d_param is not None:
        dimensions = jsonToDict(d_param)
    if dimensions is not None:
        qbm = getDimentions(dimensions, qbm)
    else:
        return "ERROR: -dimensions- invalid json syntax"    

    query = qbm.queryIntersectRadius(app.config['LOCATION'], float(lon), float(lat), float(radius))

    qbm.addField(query)
    qbm.addProjection({"_id": 0, "uri" : 1})

    return jsonify(query_diles_db(qbm.getQuery()))



@app.route('/discovery/dile/by/bbox/<minLon>/<minLat>/<maxLon>/<maxLat>')
@jsonp
def discovery_dile_by_bbox(minLon,minLat,maxLon,maxLat):
    """Discovery the diles given a bounding box.

    :example: /discovery/dile/by/bbox/-135.0/22.5/-45.0/67.5
    :param: dimensions: json document
    :returns:  geojson -- the return a feature collection with the selected diles.
    -------------------------------------------------------------------------------------------

    """

    bb = {
            "lat_min": float(minLat),
            "lat_max": float(maxLat),
            "lon_min": float(minLon),
            "lon_max": float(maxLon)
    }

    qbm = QueryBuilderMongo()

    d_param = getUrlParam('dimensions')

    if d_param is not None:
        dimensions = jsonToDict(d_param)
    if dimensions is not None:
        qbm = getDimentions(dimensions, qbm)
    else:
        return "ERROR: -dimensions- invalid json syntax" 

    query = qbm.queryIntersectBbox(app.config['LOCATION'],bb)

    qbm.addField(query)
    qbm.addProjection({"_id": 0, "uri" : 1})


    return jsonify(query_diles_db(qbm.getQuery()))



@app.route('/select/dile')
@jsonp
def select_dile_by_uri():
    """Download a dile given a uri.

    :example: /select/dile?uri=http://s3.amazonaws.com/edu-uchicago-rdcep-diles/fd65252e41e3cf0b431a07ad6e2cbe85/sdile_pr_2_1_1/pr/0/2/1/1/dile_0_2_1_1.nc

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
