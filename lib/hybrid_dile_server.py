# -*- coding: utf-8 -*-
"""
    Hybrid Dile Server
    ~~~~~~~~
    A data tile server
    :copyright: (c) 2016 by Raffaele Montella & Sergio Apreda.
    :license: Apache 2.0, see LICENSE for more details.
"""
import  json, sys, re, urllib, urllib2, socket, unicodedata
import  pydoc, cgi, os, time, inspect, collections

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
from boto.exception     import S3ResponseError

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
    DATABASE         = 'test',
    COLLECTION_DILES = 'diles',
    COLLECTION_FILES = 'files',
    DEBUG            = True,
    SECRET_KEY       = 'development key',
    USERNAME         = 'admin',
    PASSWORD         = 'default',
    LOCATION         = 'loc.geometry',
    TIME             = 'time',
    LIMIT            = 100 
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


def uJsonToDict(param):

    # if param isn't None and it's str,unicode type
    if param is not None and isinstance(param, (basestring)):
        try:
            jstring   = json.loads(json.dumps(param))
            item      = literal_eval(jstring)
            print item
        except:
            return None
        else:
            if item:
                return item
            else:
                return None
    else:
        return None  

""" --------------------- DB QUERY FUNCTIONS --------------------- """

def query_diles_db(query):

    db = get_db()

    # convention: query[size:2] -- query[0]: query document, query[1]: projection 
    if query[0]:
        # returns the result set with a limit of 100 entities
        # Note: could be interesting to use the sort function on an automatically
        #       generated counter field that measures the times the a document was matched
        #       question: is a document considered matching if outside of the result limit ? (prb not)
        return list(db[app.config['COLLECTION_DILES']].find(query[0],query[1]).limit(app.config['LIMIT']))
    else:
        return "ERROR: malformed query"

def query_files_db(query):

    db = get_db()

    # convention: query[size:2] -- query[0]: query document, query[1]: projection
    if query[0]:
        return list(db[app.config['COLLECTION_FILES']].find(query[0],query[1]).limit(app.config['LIMIT']))
    else:
        return "ERROR: malformed query"

def aggregate_result_diles(pipeline):

    db = get_db()
    return list(db[app.config['COLLECTION_DILES']].aggregate(pipeline).limit(app.config['LIMIT']))


def aggregate_result_diles(pipeline):

    db = get_db()
    return list(db[app.config['COLLECTION_FILES']].aggregate(pipeline).limit(app.config['LIMIT']))

""" ---------------------------------------------------------------- """


""" ------------- DICT OPERATIONS (FOR DOC BASED DB) --------------- """ 

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


def getDimentions(param, qbm):


    dimensions = uJsonToDict(param)

    # being a monodimensional interval per variable, a dict doesn't cause
    # collisions, because any overlap can be resolved by the extention of the domain
    if dimensions is not None and isinstance(dimensions,dict):

        for key in dimensions:

            d = dimensions[key]

            # convention: d[size:2] -- d[0]: offset start, d[1]: offset end
            if key.lower() == app.config['TIME']:           
                qbm.addField(qbm.queryTimeRange(key,d[0],d[1]))
            else:
                qbm.addField(qbm.queryRange(key,d[0],d[1]))
    return qbm


def getFeature(param, qbm):


    feature = uJsonToDict(param) 

    # in this case overalp could happen spatially speaking, but it doesn't matter
    # in mongodb the geointersect handle geojsons as is (supposedly)
    if feature is not None and isinstance(feature, dict):

        try:
            if feature['geometry']['type'] == 'Point':


                c = feature['geometry']['coordinates']
                qbm.addField(qbm.queryIntersectPoint(app.config['LOCATION'], float(c[0]), float(c[1])))        
        
            elif feature['geometry']['type'] == 'Polygon':
            
                bb = polyToBB(feature) 
                qbm.addField(qbm.queryIntersectBbox(app.config['LOCATION'], bb))
            else:
                pass
        except:
            pass

    return qbm


def getVariables(var,qbm):

    
    if isinstance(var,(tuple,list)):

        queries = [ {"variable": x} for x in var if isinstance(x,basestring)]
        
        if len(queries) > 1:
            
            try:
                qbm.addField(qbm.queryLogical('or',queries))
            except:
                pass

        elif len(queries) == 1:
            
            try:
                qbm.addField({"variable":var[0]})
            except:
                pass
        else:
            pass

    elif isinstance(var,basestring):

        try:
            qbm.addField({"variable": var})
        except:
            pass

    return qbm

""" ---------------------------------------------------------------- """


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

    note1 = {
                "title" :   "Dimensions (use with any of the above)",
                "example":  "?dim={'time'%3A+['1980-01-01-00%3A00%3A00'%2C+'1980-01-02-00%3A00%3A00']}",
                "desc":     "add in the url query field, can have multipe keys (like time) for multiple dims"
    }

    note2 = {
                "title" :   "Variables (use with any of the above)",
                "example":  "?var=pr&var=tasmax",
                "desc":     "add in the url query field, can add multiple variables as for example"
    }

    my_path=os.path.abspath(inspect.getfile(inspect.currentframe()))

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
                        line=line.replace(":example: ","").strip()
                        action['example']=request.host+line
                    elif line.startswith(":param: "):
                        line=line.replace(":param: ","").strip()
                        name=line.split(" -- ")[0]
                        desc=line.split(" -- ")[1]
                        action['params'].append({"name":name,"desc":desc})
                    elif line.startswith(":returns: "):
                        line=line.replace(":returns: ","").strip()
                        action['returns']=line
                    else:
                        pass

     
    actions.append(note1)
    actions.append(note2)

    return render_template('layout.html',actions=actions)



"""
-------------------------------------------------------------------------------------------
"""



@app.route('/discovery/dile/by/feature')
def discovery_dile_by_feature():

    """Discovery the diles given a Feature (Point or Polygon)
 
    :param:feat -- json feature
    :param:dim  -- json document
    :param:var  -- single or multiple string variables' names  
    :example:/discovery/dile/by/feature?feat={'geometry'%3A+{'type'%3A+'Point'%2C+'coordinates'%3A+[-90%2C+42.293564192170095]}%2C+'type'%3A+'Feature'%2C+'properties'%3A+{}}
    :returns:geojson -- return a feature collection with the selected diles.
    -------------------------------------------------------------------------------------------
    """

    # creating the object to build the queries
    qbm = QueryBuilderMongo()

    # request the arguments of the url query
    f_param = request.args.get('feat')    
    d_param = request.args.get('dim')
    v_param = request.args.getlist('var')


    # creating the feature query
    if f_param is not None:
        qbm = getFeature(f_param, qbm)
    else:
        return "ERROR: -feat- not found"


    # creating the dimension query
    if d_param is not None:
        qbm = getDimentions(d_param, qbm)

    # creating the variables query
    if v_param:
        qbm = getVariables(v_param, qbm)


    # adding the projection
    qbm.addProjection({"_id": 0, "uri" : 1})

    return jsonify(query_diles_db(qbm.getQuery()))



@app.route('/discovery/dile/by/position/<lon>/<lat>')
@jsonp
def discovery_dile_by_position(lon,lat):
    """Discovery the diles given a lon/lat position.

    :example: /discovery/dile/by/position/-135.0/22.5
    :param: dim -- json document
    :param: var -- single or multiple string variables' names 
    :returns: geojson -- the return a feature collection with the selected diles.
    -------------------------------------------------------------------------------------------

    """

    qbm   = QueryBuilderMongo()

    d_param = request.args.get('dim')
    v_param = request.args.getlist('var')

    # creating the dimension query
    if d_param is not None:
        qbm = getDimentions(d_param, qbm)

    # creating the variables query
    if v_param:
        qbm = getVariables(v_param, qbm)

    query = qbm.queryIntersectPoint(app.config['LOCATION'], float(lon), float(lat))

    qbm.addField(query)
    qbm.addProjection({"_id": 0, "uri" : 1})

    return jsonify(query_diles_db(qbm.getQuery()))

    

@app.route('/discovery/dile/by/radius/<lon>/<lat>/<radius>')
@jsonp
def discovery_dile_by_radius(lon,lat,radius):
    """Discovery the diles given a center point by lon/lat and a radius in km.

    :example: /discovery/dile/by/radius/-135.0/22.5/5000.0
    :param: dim -- json document
    :param: var -- single or multiple string variables' names 
    :returns: geojson -- the return a feature collection with the selected diles.
    -------------------------------------------------------------------------------------------

    """

    qbm = QueryBuilderMongo()

    d_param = request.args.get('dim')
    v_param = request.args.getlist('var')

    # creating the dimension query
    if d_param is not None:
        qbm = getDimentions(d_param, qbm)

    # creating the variables query
    if v_param:
        qbm = getVariables(v_param, qbm)

    query = qbm.queryIntersectRadius(app.config['LOCATION'], float(lon), float(lat), float(radius))

    qbm.addField(query)
    qbm.addProjection({"_id": 0, "uri" : 1})

    return jsonify(query_diles_db(qbm.getQuery()))


@app.route('/discovery/dile/by/bbox/<minLon>/<minLat>/<maxLon>/<maxLat>')
@jsonp
def discovery_dile_by_bbox(minLon,minLat,maxLon,maxLat):
    """Discovery the diles given a bounding box.

    :example: /discovery/dile/by/bbox/-135.0/22.5/-45.0/67.5
    :param: dim -- json document
    :param: var -- single or multiple string variables' names 
    :returns: geojson -- the return a feature collection with the selected diles.
    -------------------------------------------------------------------------------------------

    """

    bb = {
            "lat_min": float(minLat),
            "lat_max": float(maxLat),
            "lon_min": float(minLon),
            "lon_max": float(maxLon)
    }

    qbm = QueryBuilderMongo()

    d_param = request.args.get('dim')
    v_param = request.args.getlist('var')

    # creating the dimension query
    if d_param is not None:
        qbm = getDimentions(d_param, qbm)

    # creating the variables query
    if v_param:
        qbm = getVariables(v_param, qbm)

    query = qbm.queryIntersectBbox(app.config['LOCATION'],bb)

    qbm.addField(query)
    qbm.addProjection({"_id": 0, "uri" : 1})


    return jsonify(query_diles_db(qbm.getQuery()))



@app.route('/select/dile')
@jsonp
def select_dile_by_uri():
    """Download a dile given a uri.

    :example: /select/dile?uri=http://s3.amazonaws.com/edu-uchicago-rdcep-diles/fd65252e41e3cf0b431a07ad6e2cbe85/sdile_pr_2_1_1/pr/0/2/1/1/dile_0_2_1_1.nc
    :param: uri -- a valid uri to access the dile
    :returns: netcdf4 -- the return of the dile.
    -------------------------------------------------------------------------------------------

    """
    uri=request.args.get('uri')
    
    if uri is not None:
        
        if uri.startswith("s3://.amazonaws.com/"):
            
            path        = uri.replace(".amazonaws.com/","")
            bname, kstr = path.split("/",1) # split the bname from the key string
            
            print "BNAME: ", bname
            print "KEY: ", kstr

            return "OK!"

            """
            conn        = S3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

            try:     
                bucket  = conn.get_bucket(bname)
            except:
                print "BUCKET NOT FOUND"
                return str("ERROR: bucket "+bname+" not found")
            else:
                print "BUCKET CONNECTED"
                try:
                    key = bucket.get_key(kstr)
                except:
                    print "KEY NOT FOUND"
                    return str("ERROR: key "+kstr+"not found")
                else:
                    print "STATUS: "
                    print "bname: ", bname
                    print "key_str: ", kstr
                    print "key: ", key

                    try:
                        
                        key.open_read()                         # opens the file
                        headers = dict(key.resp.getheaders())   # request the headers
                        return Response(key, headers=headers)   # return a response
                                                    
                    except S3ResponseError as e:
                        return Response(e.body, status=e.status, headers=key.resp.getheaders())
                
                ""
                -- outside boto approach --

                response = make_response(uri)
                response.headers['Content-Type'] = 'application/x-netcdf'
                response.headers['Content-Disposition'] = 'attachment; filename=dile.nc4'
                return response
                
                """
