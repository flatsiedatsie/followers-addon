"""Followers API handler."""


import os
import sys
from os import path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
import json
import time
from time import sleep
import requests
import threading

try:
    from gateway_addon import APIHandler, APIResponse, Database
    #print("succesfully loaded APIHandler and APIResponse from gateway_addon")
except:
    print("Import APIHandler and APIResponse from gateway_addon failed. Use at least WebThings Gateway version 0.10")
    sys.exit(1)


_TIMEOUT = 3

_CONFIG_PATHS = [
    os.path.join(os.path.expanduser('~'), '.webthings', 'config'),
]

if 'WEBTHINGS_HOME' in os.environ:
    _CONFIG_PATHS.insert(0, os.path.join(os.environ['WEBTHINGS_HOME'], 'config'))




class FollowersAPIHandler(APIHandler):
    """Followers API handler."""

    def __init__(self, verbose=False):
        """Initialize the object."""
        #print("INSIDE API HANDLER INIT")
        
        
        self.addon_name = 'followers'
        self.running = True

        self.server = 'http://127.0.0.1:8080'
        self.DEBUG = False
            
        self.things = [] # Holds all the things, updated via the API. Used to display a nicer thing name instead of the technical internal ID.
        self.data_types_lookup_table = {}
        self.token = None
        
        
        # LOAD CONFIG
        try:
            self.add_from_config()
        except Exception as ex:
            print("Error loading config: " + str(ex))
        
        #self.DEBUG = True
        
        
        
        # Paths
        # Get persistent data
        try:
            self.persistence_file_path = os.path.join(self.user_profile['dataDir'], self.addon_name, 'persistence.json')
        except:
            try:
                if self.DEBUG:
                    print("setting persistence file path failed, will try older method.")
                self.persistence_file_path = os.path.join(os.path.expanduser('~'), '.webthings', 'data', self.addon_name,'persistence.json')
            except:
                if self.DEBUG:
                    print("Double error making persistence file path")
                self.persistence_file_path = "/home/pi/.webthings/data/" + self.addon_name + "/persistence.json"
        
        if self.DEBUG:
            print("Current working directory: " + str(os.getcwd()))
        
        
        first_run = False
        try:
            with open(self.persistence_file_path) as f:
                self.persistent_data = json.load(f)
                if self.DEBUG:
                    print("Persistence data was loaded succesfully.")
                
        except:
            first_run = True
            print("Could not load persistent data (if you just installed the add-on then this is normal)")
            self.persistent_data = {'items':[]}
            
        if self.DEBUG:
            print("self.persistent_data is now: " + str(self.persistent_data))

        
        
        
        # Is there user profile data?    
        #try:
        #    print(str(self.user_profile))
        #except:
        #    print("no user profile data")
                

            
            
        # Intiate extension addon API handler
        try:
            manifest_fname = os.path.join(
                os.path.dirname(__file__),
                '..',
                'manifest.json'
            )

            with open(manifest_fname, 'rt') as f:
                manifest = json.load(f)

            APIHandler.__init__(self, manifest['id'])
            self.manager_proxy.add_api_handler(self)
            

            if self.DEBUG:
                print("self.manager_proxy = " + str(self.manager_proxy))
                print("Created new API HANDLER: " + str(manifest['id']))
        
        except Exception as e:
            print("Failed to init UX extension API handler: " + str(e))

        

        # Respond to gateway version
        try:
            if self.DEBUG:
                print(self.gateway_version)
        except:
            print("self.gateway_version did not exist")
            
        #while(True):
        #    sleep(1)
        

        # Start the internal clock
        if self.DEBUG:
            print("Starting the internal clock")
        try:            
            if self.token != None:
                t = threading.Thread(target=self.clock)
                t.daemon = True
                t.start()
        except:
            print("Error starting the clock thread")




    # Read the settings from the add-on settings page
    def add_from_config(self):
        """Attempt to read config data."""
        try:
            database = Database(self.addon_name)
            if not database.open():
                print("Could not open settings database")
                return
            
            config = database.load_config()
            database.close()
            
        except Exception as ex:
            print("Error! Failed to open settings database: " + str(ex))
        
        if not config:
            print("Error loading config from database")
            return
        
        
        
        # Api token
        try:
            if 'Authorization token' in config:
                self.token = str(config['Authorization token'])
                print("-Authorization token is present in the config data.")
        except:
            print("Error loading api token from settings")
        

        if 'Debugging' in config:
            self.DEBUG = bool(config['Debugging'])
            if self.DEBUG:
                print("-Debugging preference was in config: " + str(self.DEBUG))







#
#  CLOCK
#

    def clock(self):
        """ Runs every second """
        previous_action_times_count = 0
        #previous_injection_time = time.time()
        while self.running:
            time.sleep(1)
            #print("waking")
            #print("items: " + str(self.persistent_data['items']))
            try:
                #for item in self.persistent_data['items']:
                for index, item in enumerate(self.persistent_data['items']):
                    #print(str(index))
                
                    if 'thing1' in item and 'thing2' in item and 'property1' in item and 'property2' in item and 'limit1' in item and 'limit2' in item and 'limit3' in item and 'limit4' in item and 'enabled' in item:
                        #print("all variables are there")
                        #print(str( bool(item['enabled']) ))
                        if bool(item['enabled']) is False:
                            #print("not enabled")
                            continue
                    
                        #print("")
                        
                        api_get_result = self.api_get( '/things/' + str(item['thing1']) + '/properties/' + str(item['property1']))
                        #print("detail: " + str(item['thing1']))
                    
                        try:
                            key = list(api_get_result.keys())[0]
                        except:
                            print("error parsing the returned json")
                            #continue
                    
                        try:
                            if key == "error": 
                                if api_get_result[key] == 500:
                                    
                                    #return
                                    #print("API GET failed")

                                    continue

                            else:
                                #print("API GET was succesfull")
                                original_value = api_get_result[key]
                                #if self.DEBUG:
                                #    print("type of original_value variable is: " + str(type(original_value)))
                                #    print("got original value from API: " + str(original_value))
                            
                            
                                if original_value is "":
                                    #print("original value is an empty string.") # this happens if the gateway has just been rebooted, and the property doesn not have a value yet.
                                    continue
                                    
                                if min(float(item['limit1']), float(item['limit2'])) <= float(original_value) <= max(float(item['limit1']), float(item['limit2'])):
                                    output = translate(original_value, item['limit1'], item['limit2'], item['limit3'], item['limit4'])
                                    #print("got translated output: " + str(output))

                            
                                    if 'previous_value' not in item:
                                        item['previous_value'] = None

                                    try:
                                        numeric_value = get_int_or_float(output)
                                        #print("initial numeric_value = " + str(numeric_value))
                                        if 'property2_type' in item:
                                            if str(item['property2_type']) == 'integer':
                                                numeric_value = round(numeric_value)
                                        else:
                                            if self.DEBUG:
                                                print("property2_type was not in item")
                                    except Exception as ex:
                                        print("Error turning into int: " + str(ex))
                                        continue
                                        
                                    if str(item['previous_value']) != str(numeric_value):
                                        item['previous_value'] = numeric_value

                                        try:
                                            if self.DEBUG:
                                                print("new value for " + str(item['thing2']) + " - " + str(item['property2']) + ", will update via API: " + str(numeric_value))
                            
                                        
                                            data_to_put = { str(item['property2']) : numeric_value }
                                            #print("data_to_put = " + str(data_to_put))
                                            api_put_result = self.api_put( '/things/' + str(item['thing2']) + '/properties/' + str(item['property2']), data_to_put )
                                            #print("api_put_result = " + str(api_put_result))

                                            #if api_put_result[str(item['property2'])] == str(numeric_value):
                                            #    print("API PUT was succesfull")
                                            #else:
                                            #    print("API PUT failed")
                                        except Exception as ex:
                                            print("Error late in putting via API: " + str(ex))
                                        
                                        
                        except Exception as ex:
                            print("Error putting via API: " + str(ex))

                    elif 'enabled' in item: # this might be superfluous
                        if item['enabled']:
                            # the device should not be enabled, it's incomplete.
                            self.persistent_data['items'][index]['enabled'] = False
                            self.save_persistent_data()
                            if self.DEBUG:
                                print("Set an incomplete enabled item to disabled")
                    

            except Exception as ex:
                print("Clock error: " + str(ex))              
                        
                        

#
#  HANDLE REQUEST
#

    def handle_request(self, request):
        """
        Handle a new API request for this handler.

        request -- APIRequest object
        """
        
        try:
        
            if request.method != 'POST':
                return APIResponse(status=404)
            
            if request.path == '/init' or request.path == '/update_items':

                try:
                    
                    if request.path == '/init':
                        if self.DEBUG:
                            print("Getting the initialisation data")
                            
                        try:
                            state = 'ok'
        
                            # Check if a token is present
                            if self.token == None:
                                state = 'This addon requires an authorization token to work. Visit the settings page of this addon to learn more.'


                            return APIResponse(
                                status=200,
                                content_type='application/json',
                                content=json.dumps({'state' : state, 'items' : self.persistent_data['items']}),
                            )
                        except Exception as ex:
                            print("Error getting init data: " + str(ex))
                            return APIResponse(
                                status=500,
                                content_type='application/json',
                                content=json.dumps({'state' : "Internal error: no thing data", 'items' : []}),
                            )
                            
                    
                    elif request.path == '/update_items':
                        try:
                            self.persistent_data['items'] = request.body['items']
                            
                            
                            #print("")
                            # Get all the things via the API.
                            try:
                                self.things = self.api_get("/things")
                                #print("Did the things API call")
                            except Exception as ex:
                                print("Error getting updated things data via API: " + str(ex))
                                
                            # try to get the correct property type (integer/float)
                            try:
                                for item in self.persistent_data['items']:
                                    #print("_item: " + str(item))
                                    if 'thing2' in item and 'property2' in item:
                                        for thing in self.things:
                                            thing_id = str(thing['id'].rsplit('/', 1)[-1])
                                            #print("__id: " + str(thing_id))
                                            if str(item['thing2']) == thing_id:
                                                #print("BINGO. Props:")
                                                #print(str(thing['properties']))
                                                for thing_property_key in thing['properties']:
                                                    
                                                    property_id = thing['properties'][thing_property_key]['links'][0]['href'].rsplit('/', 1)[-1]
                                                    #print("property_id = " + str(property_id))
                                                    if str(item['property2']) == property_id:
                                                        #print("bingo for property: " + str(property_id))
                                                        #print("___type: " + str(thing['properties'][thing_property_key]['type']))

                                                        #self.persistent_data['items'][item]['property2_type'] = str(thing['properties'][thing_property_key]['type'])
                                                        item['property2_type'] = str(thing['properties'][thing_property_key]['type'])

                      
                            except Exception as ex:
                                print("Error finding if property should be int or float: " + str(ex))
                            
                            self.save_persistent_data()    
                                
                            
                            return APIResponse(
                                status=200,
                                content_type='application/json',
                                content=json.dumps({'state' : 'ok'}),
                            )
                        except Exception as ex:
                            if self.DEBUG:
                                print("Error saving updated items: " + str(ex))
                            return APIResponse(
                                status=500,
                                content_type='application/json',
                                content=json.dumps("Error updating items: " + str(ex)),
                            )
                            
                        
                    else:
                        return APIResponse(
                            status=500,
                            content_type='application/json',
                            content=json.dumps("API error"),
                        )
                        
                        
                except Exception as ex:
                    if self.DEBUG:
                        print("Error while handling request: " + str(ex))
                    return APIResponse(
                        status=500,
                        content_type='application/json',
                        content=json.dumps("Error in API handler"),
                    )
                    
            else:
                return APIResponse(status=404)
                
        except Exception as e:
            if self.DEBUG:
                print("Failed to handle UX extension API request: " + str(e))
            return APIResponse(
                status=500,
                content_type='application/json',
                content=json.dumps("API Error"),
            )


    def unload(self):
        self.running = False
        if self.DEBUG:
            print("Followers shutting down")




    def cancel_pairing(self):
        """Cancel the pairing process."""
        #print("END OF PAIRING -----------------------------")

        # Get all the things via the API.
        try:
            self.things = self.api_get("/things")
            #print("Did the things API call")
        except Exception as ex:
            print("Error, couldn't load things at init: " + str(ex))




#
#  API
#

    def api_get(self, api_path):
        """Returns data from the WebThings Gateway API."""
        #if self.DEBUG:
        #    print("GET PATH = " + str(api_path))
        #print("GET TOKEN = " + str(self.token))
        if self.token == None:
            print("PLEASE ENTER YOUR AUTHORIZATION CODE IN THE SETTINGS PAGE")
            return {"error": 500}
        
        try:
            r = requests.get(self.server + api_path, headers={
                  'Content-Type': 'application/json',
                  'Accept': 'application/json',
                  'Authorization': 'Bearer ' + str(self.token),
                }, verify=False, timeout=3)
            #if self.DEBUG:
            #    print("API GET: " + str(r.status_code) + ", " + str(r.reason))

            if r.status_code != 200:
                if self.DEBUG:
                    print("API returned a status code that was not 200. It was: " + str(r.status_code))
                return {"error": r.status_code}
                
            else:
                #if self.DEBUG:
                #    print("API get succesfull: " + str(r.text))
                return json.loads(r.text)
            
        except Exception as ex:
            if self.DEBUG:
                print("Error doing " + str(api_path) + " request/loading returned json: " + str(ex))
            #return [] # or should this be {} ? Depends on the call perhaps.
            return {"error": 500}


    def api_put(self, api_path, json_dict):
        """Sends data to the WebThings Gateway API."""

        #if self.DEBUG:
            #print("PUT > api_path = " + str(api_path))
            #print("PUT > json dict = " + str(json_dict))
            #print("PUT > self.server = " + str(self.server))
            #print("PUT > self.token = " + str(self.token))
            

        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.token),
        }
        try:
            r = requests.put(
                self.server + api_path,
                json=json_dict,
                headers=headers,
                verify=False,
                timeout=3
            )
            #if self.DEBUG:
            #print("API PUT: " + str(r.status_code) + ", " + str(r.reason))

            if r.status_code != 200:
                #if self.DEBUG:
                #    print("Error communicating: " + str(r.status_code))
                return {"error": str(r.status_code)}
            else:
                if self.DEBUG:
                    print("API PUT response: " + str(r.text))
                return json.loads(r.text)

        except Exception as ex:
            if self.DEBUG:
                print("Error doing http request/loading returned json: " + str(ex))
            #return {"error": "I could not connect to the web things gateway"}
            #return [] # or should this be {} ? Depends on the call perhaps.
            return {"error": 500}



#
#  SAVE TO PERSISTENCE
#

    def save_persistent_data(self):
        #if self.DEBUG:
        #print("Saving to persistence data store at path: " + str(self.persistence_file_path))
            
        try:
            if not os.path.isfile(self.persistence_file_path):
                open(self.persistence_file_path, 'a').close()
                if self.DEBUG:
                    print("Created an empty persistence file")
            #else:
            #    if self.DEBUG:
            #        print("Persistence file existed. Will try to save to it.")


            with open(self.persistence_file_path) as f:
                if self.DEBUG:
                    print("saving persistent data: " + str(self.persistent_data))
                json.dump( self.persistent_data, open( self.persistence_file_path, 'w+' ) )
                return True

        except Exception as ex:
            print("Error: could not store data in persistent store: " + str(ex) )
            return False



def translate(value, leftMin, leftMax, rightMin, rightMax):
    try:
        
        #print("leftMin = " + str(leftMin))
        #print("leftMax = " + str(leftMax))
        #print("rightMin = " + str(rightMin))
        #print("rightMax = " + str(rightMax))
        # Figure out how 'wide' each range is
        leftSpan = float(leftMax) - float(leftMin)
        rightSpan = float(rightMax) - float(rightMin)
        
        #print(str(leftSpan))
        #print(str(rightSpan))
        
        # Convert the left range into a 0-1 range (float)
        valueScaled = float(float(value) - float(leftMin)) / float(leftSpan)

        #print("valueScaled = " + str(valueScaled))
        
        new_value = float(rightMin) + (valueScaled * rightSpan)

        # Convert the 0-1 range into a value in the right range.
        return new_value
    except Exception as ex:
        print("Error in translate: " + str(ex) )
        return 0
    
    
    
    
    
def get_int_or_float(v):
    number_as_float = float(v)
    number_as_int = int(number_as_float)
    if number_as_float == number_as_int:
        return number_as_int
    else:
        return float( int( number_as_float * 1000) / 1000)