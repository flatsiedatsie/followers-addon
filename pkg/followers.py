"""Followers API handler."""


import os
import sys
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
        self.ready = False
        
        self.api_server = 'http://127.0.0.1:8080'
        self.DEBUG = False
            
        self.things = [] # Holds all the things, updated via the API. Used to display a nicer thing name instead of the technical internal ID.
        self.data_types_lookup_table = {}
        self.seconds = 0
        self.minutes = 0
        self.error_counter = 0
        self.there_are_missing_properties = False
        self.ignore_missing_properties = False
        self.got_good_things_list = False
        self.api_seems_down = False
        
        # LOAD CONFIG
        try:
            self.add_from_config()
        except Exception as ex:
            print("Error loading config: " + str(ex))
        
        #self.DEBUG = True
        
        # Respond to gateway version
        try:
            if self.DEBUG:
                print("Gateway version: " + str(self.gateway_version))
        except:
            if self.DEBUG:
                print("self.gateway_version did not exist")
        
        
        
        
        # Paths
        # Get persistent data
        try:
            self.persistence_file_path = os.path.join(self.user_profile['dataDir'], self.addon_name, 'persistence.json')
            if not os.path.isdir(self.persistence_file_path):
                os.mkdir(self.persistence_file_path)
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


        if 'token' not in self.persistent_data:
            self.persistent_data['token'] = None

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

        
        self.things = {}
        self.simple_things = {}

        # Give the addons time to create all devices
        if not self.DEBUG:
            sleep(20)
            
        if self.DEBUG:
            print("Followers is now getting the simple things list.")
        self.update_simple_things()
        
        

        # Start the internal clock
        if self.DEBUG:
            print("Starting the internal clock")
        try:            
            if self.persistent_data['token'] != None:
                t = threading.Thread(target=self.clock)
                t.daemon = True
                t.start()
        except:
            print("Error starting the clock thread")

        self.ready = True



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
            self.close_proxy()
        
        if not config:
            print("Error loading config from database")
            return
        
        
        
        # Debug
        if 'Debugging' in config:
            self.DEBUG = bool(config['Debugging'])
            if self.DEBUG:
                print("-Debugging preference was in config: " + str(self.DEBUG))
        
        # Api token
        try:
            if 'Authorization token' in config:
                if len(str(config['Authorization token'])) > 10:
                    self.persistent_data['token'] = str(config['Authorization token'])
                else:
                    if self.DEBUG:
                        print("-Authorization token is present in the config data, but too short")
        except:
            if self.DEBUG:
                print("Error loading api token from settings")
        
        
        # Ignore missing properties?
        if 'Ignore missing properties' in config:
            self.ignore_missing_properties = bool(config['Ignore missing properties'])
            if self.DEBUG:
                print("-Ignore missing properties preference was in config: " + str(self.ignore_missing_properties))
        






#
#  CLOCK
#

    def clock(self):
        """ Runs every second """
        previous_action_times_count = 0
        #previous_injection_time = time.time()
        enabled_count = len(self.persistent_data['items'])
        
        previous_timestamp = 0
        
        while self.running:
            
            current_timestamp = int(time.time())
            
            if current_timestamp == previous_timestamp:
                time.sleep(.1)
            else:
                previous_timestamp = current_timestamp
                if self.DEBUG:
                    print(" ")
                    print("previous_timestamp: " + str(previous_timestamp))
                
                try:
                    if self.got_good_things_list:
                    
                        """
                        if self.DEBUG:
                            print("FOLLOWERS IS MUCH SLOWER TO MAKE DEBUGGING EASIER. SLEEPING 4 SECONDS.")
                            time.sleep(4)
                        
                        
                        else:
                        
                            if enabled_count == 0:
                                time.sleep(5)
                            elif enabled_count < 2:
                                if self.items_with_issues == 0:
                                    time.sleep(.5)
                                else:
                                    time.sleep(.8)
                            else:
                                time.sleep(1)
                        """
                        
                        # Keeping an eye on any error that may develop if things disappear or properties don't (yet) exist
                        try:
                
                            self.seconds += 1
                            if (self.seconds + 10) % 10 == 0:
                                if self.there_are_missing_properties: # and self.ignore_missing_properties == False:
                                    #if self.DEBUG:
                                    if self.DEBUG:
                                        print("Error, missing properties were spotted, so updating simple_things dictionary. self.ignore_missing_properties: " + str(self.ignore_missing_properties))
                                    self.update_simple_things() # perhaps they have appeared, so every 10 seconds there's a check

                            if self.seconds == 180: # items with missing things will only be checked once every 3 minutes
                                self.seconds = 0
                                self.minutes += 1
                                if self.minutes == 20: # A lof of time has passed. Time to check if broken followers should be disabled entirely.
                                    self.minutes = 0
                                if self.DEBUG:
                                    print("self.minutes is now: " + str(self.minutes))

                            if self.error_counter != 0:
                                if self.DEBUG:
                                    print("self.error_counter = " + str(self.error_counter))
                
                        
                            if self.error_counter > 5:
                                if self.DEBUG:
                                    print("At least 5 errors counted: " + str(self.error_counter))
                                #if self.ignore_missing_properties == False:
                                #self.update_simple_things()
                                self.error_counter = 0

                
                        except Exception as ex:
                            if self.DEBUG:
                                print("Error while keeping an eye on errors")
                    
                    
                        self.there_are_missing_properties = False
                        enabled_count = 0 # how many if the items are enabled?
                        attempted_items = 0
                        self.items_with_issues = 0 # used to check if ALL items have issues at the same time. If so, that probably means the network is down.
                        #item_counter = 0 # used to only query one device per second. Device 0 at second zero, device 1 at second 1, etc
                        api_cache = {} # during this loop, before we get an api get request, look up if that exact same request was done before. No need to do the exact same request twice.
                        for index, item in enumerate(self.persistent_data['items']):
                            try:
                                if self.DEBUG:
                                    print("Follower #" + str(index))
                    
                                attempted_connections = 0 # can make up to 2 API connections in one run, if all goes well.
                                api_error_spotted = 0

                    

                                # Speed limiter keeps API's happy. We skip items that are set to a lower speed
                                #if 'speed' in item and index != self.seconds:
                                #    if self.seconds % item['speed'] != 0:
                                #        continue
                                    
                            

                                if not 'api_error_count' in self.persistent_data['items'][index]:
                                    if 'speed' in self.persistent_data['items'][index]:
                                        self.persistent_data['items'][index]['api_error_count'] = int(self.persistent_data['items'][index]['speed'])
                                        if self.DEBUG:
                                            print("setting initial api_error_count to speed: " + str(self.persistent_data['items'][index]['speed']))
                                    else:
                                        if self.DEBUG:
                                            print("setting initial api_error_count to 0")
                                    self.persistent_data['items'][index]['api_error_count'] = 0
                                elif self.persistent_data['items'][index]['api_error_count'] > 600:
                                    if self.DEBUG:
                                        print("- limiting api error count to 60")
                                    self.persistent_data['items'][index]['api_error_count'] = 600 # That's a lot of errors
                            
                            
                                if not 'speed' in self.persistent_data['items'][index]:
                                    if self.DEBUG:
                                        print("adding speed property to item, with value of 0 (high speed)")
                                    self.persistent_data['items'][index]['speed'] = 0 # before the speed option all followers were high speed
                            
                            
                                #once every hour we reset the api_error_count
                                if self.seconds == 0 and self.minutes == 0:
                                    if self.DEBUG:
                                        print("seconds and minutes are 0, resetting api error count")
                                    self.persistent_data['items'][index]['api_error_count'] = 0
                            
                                # TODO: this could potentially interfere with the speed option, where they both block progress, and the item is never tested
                                if self.DEBUG:
                                    print("seconds: " + str( self.seconds ))
                                    print("error count: " + str( self.persistent_data['items'][index]['api_error_count'] ))
                            
                                if self.persistent_data['items'][index]['api_error_count'] > 0:
                                
                                    if self.persistent_data['items'][index]['api_error_count'] < 3:
                                        if (self.seconds + 10) % 10 != 0:
                                            if self.DEBUG:
                                                print("up to 3 errors, doing light skip (check once every 10 seconds)")
                                                print("seconds modulo: " + str( (self.seconds + 10) % 10 ))
                                            continue
                                    
                                    elif self.persistent_data['items'][index]['api_error_count'] < 6:
                                        if (self.seconds + 30) % 30 != 0:
                                            if self.DEBUG:
                                                print("up to 6 errors, switched to check once every 30 seconds")
                                                print("seconds modulo: " + str( (self.seconds + 10) % 10 ))
                                            continue
                                    
                                    elif self.persistent_data['items'][index]['api_error_count'] < 10:
                                        if (self.seconds + 60) % 60 != 0:
                                            if self.DEBUG:
                                                print("up to 10 errors, switched to check once every 60 seconds)")
                                                print("seconds modulo: " + str( (self.seconds + 10) % 10 ))
                                            continue
                                    
                                    elif (self.seconds + 180) % 180 != 0:
                                        if self.DEBUG:
                                            print("more than 10 errors, switched to check once every 3 minutes)")
                                        continue
                                    
                                    if self.DEBUG:
                                        print("Device had API errors, but is allowed to continue this one time")
                                    
                                #if self.seconds > 0 and self.persistent_data['items'][index]['api_error_count'] > 0:
                                #    print("this item has API errors. Skipping.")
                                #    continue
                                    #if self.seconds % self.persistent_data['items'][index]['api_error_count'] != 0:
                                    #    print("blocked by modulo. Seconds: " + str(self.seconds) + ", and error count is: " + str(self.persistent_data['items'][index]['api_error_count']))
                                    #    continue
                            
                                #
                                #  PRE-CHECK
                                #  Items with missing parts in the thing list will be slowed down to once every 3 minutes
                    
                                # At the very least all the variables should be present in the item. The UI should not allow incomplete items to be set, but we check here just in case.
                                if 'thing1' in item and 'thing2' in item and 'property1' in item and 'property2' in item and 'limit1' in item and 'limit2' in item and 'limit3' in item and 'limit4' in item:
                                    #print("all variables are there")
                                    #print(str( bool(item['enabled']) ))
                    
                                    if self.DEBUG:
                                        print(str(item['property1']) + " -> " + str(item['property2']))
                                    
                                    if not 'enabled' in item:
                                        self.persistent_data['items'][index]['enabled'] = True
                                        self.save_persistent_data()
                                        item['enabled'] = True
                    
                                    elif bool(item['enabled']) is False:
                                        if self.DEBUG:
                                            print("this follower is curently not enabled, skipping")
                                        self.persistent_data['items'][index]['api_error_count'] = 0
                                        continue
                
                                    enabled_count += 1
                
                                    #elif self.persistent_data['items'][index]['missing_thing'] == True and self.seconds != 60:
                                        # items with missing things are only allowed to pass once every 3 minutes, to check if they have appeared.
                    
                                    # Make sure the things and property ID's exist (in theory...)
                                    # If things are missing, the followers can be disabled automatically. 
                                    # If only properties are missing, we keep checking if they may appear
                    
                        
                                    #print("looking for: " + str(str(item['thing1'])))
                        
                                    parts_not_in_simple_things = 0 # every time someting is wrong with this item, it will increase.
                        
                                    if not 'missing_parts' in self.persistent_data['items'][index]:
                                        self.persistent_data['items'][index]['missing_parts'] = 0
                        
                        
                        
                                    # reset the missing parts indicator so this thing will get another shot
                                    if self.seconds == index:
                                        if self.persistent_data['items'][index]['missing_parts'] > 0:
                                            if self.DEBUG:
                                                print("resetting parts count to 0 for: " + str(item[thing2]))
                                            self.persistent_data['items'][index]['missing_parts'] = 0
                                    elif self.persistent_data['items'][index]['missing_parts'] > 0:
                                        continue
                        
                                    # make sure the item has an api error count
                                    if not 'api_error_count' in self.persistent_data['items'][index]:
                                        self.persistent_data['items'][index]['api_error_count'] = 0
                            
                            
                            
                            
                        
                                    # This first part checks if the thing and property ID's are in the things data we got from the API. IF not, that's a bad sign, but it could be temporary, or an issue with the API not providing all the things. They may appear a little later.
                        
                                    if not str(item['thing1']) in self.simple_things:
                                            parts_not_in_simple_things += 1
                                            if self.DEBUG:
                                                print("first thing was not in things_list")

                                    else:
                                        if not str(item['property1']) in self.simple_things[ str(item['thing1']) ]:
                                            self.there_are_missing_properties = True
                                            parts_not_in_simple_things += 1
                                            if self.DEBUG:
                                                print("First property was not in things list: " + str(item['property1']))

                
                
                                    if not str(item['thing2']) in self.simple_things:
                                        parts_not_in_simple_things += 1
                                        if self.DEBUG:
                                            print("thing was not in simple_things list")

                                    else:
                                        if not str(item['property2']) in self.simple_things[ str(item['thing2']) ]:
                                            parts_not_in_simple_things += 1
                                            self.there_are_missing_properties = True
                                            if self.DEBUG:
                                                print("second property was not in things_list: " + str(item['property2']))

                            
                        
                                    if parts_not_in_simple_things > 0:
                                    
                                        if (self.seconds + 10) % 10 != 0:
                                            if self.DEBUG:
                                                print("skipping because of missing parts")
                                            continue
                                        #if index != self.seconds: # If this is not the one second where a broken device is allowed to pass, then remember that we saw errors, so that it will skipped for the next 3 minutes.
                                    self.persistent_data['items'][index]['missing_parts'] = parts_not_in_simple_things
                                
                                
                            
                                    #
                                    #  Doing the API requests
                                    #
                                
                        
                                    # check if we already did this exact API request during this loop, and if so, recreate the output from memory
                                    double_name = str(item['thing1']) + str(item['property1'])
                                    if double_name in api_cache:
                                        if self.DEBUG:
                                            print("already spotted in api_cache: " + str(double_name) + ", with value: " + str(api_cache[double_name]))
                                        api_get_result = {}
                                        if api_cache[double_name] == 'error':
                                            api_get_result = {'error':'500'}
                                        else:
                                            api_get_result[ str(item['property1']) ] = api_cache[double_name]
                            
                                    else:
                                        # Now we start actually querying the API
                                        api_get_result = self.api_get( '/things/' + str(item['thing1']) + '/properties/' + str(item['property1']))
                                        time.sleep(.02)
                                    #print("detail: " + str(item['thing1']))
                        
                                    try:
                                        if self.DEBUG:
                                            print("api_get_result = " + str(api_get_result))
                                        if type(api_get_result) == int:
                                            wrapped_api_get_result = {}
                                            wrapped_api_get_result[str(item['property1'])] = api_get_result
                                            if self.DEBUG:
                                                print("wrapped_api_get_result = " + str(wrapped_api_get_result))
                                            api_get_result = wrapped_api_get_result
                                        
                                        key = list(api_get_result.keys())[0] #.keys() # ?? isn't that just the property_id?
                                    except Exception as ex:
                                        if self.DEBUG:
                                            print("error parsing the returned json: " + str(ex))
                                        self.error_counter += 2
                                        api_error_spotted += 1
                                        key = "error" #str(item['property1'])
                
                

                                    try:
                                        if key == "error": 
                                            api_error_spotted += 1
                                            api_cache[double_name] = 'error'
                                            if api_get_result[key] == 500:
                                                if self.DEBUG:
                                                    print("API GET failed with a 500 server error.")
                                        
                                                if self.ignore_missing_properties == False:
                                                    self.error_counter += 2

                                        else:
                                            #print("API GET was succesfull")
                                            if type(api_get_result) == int:
                                                if self.DEBUG:
                                                    print("Error/warning: api_get_result was still an int")
                                                original_value = api_get_result
                                            else:
                                                original_value = api_get_result[key]
                                        
                                            api_cache[double_name] = original_value
                                            #if self.DEBUG:
                                            #    print("type of original_value variable is: " + str(type(original_value)))
                                            #    print("got original value from API: " + str(original_value))
                        
                        
                                            if not original_value == "" and api_error_spotted == 0: # only PUT if there were no issues with GET
                                                #api_error_spotted += 1
                                                #print("original value is an empty string.") # this happens if the gateway has just been rebooted, and the property exists but its value is still undefined.
                                                #continue
                                
                                                # If the value we received is within tolerances, then we calculate the value that the second property should be set to
                                                if min(float(item['limit1']), float(item['limit2'])) <= float(original_value) <= max(float(item['limit1']), float(item['limit2'])):
                                                    output = translate(original_value, item['limit1'], item['limit2'], item['limit3'], item['limit4'])
                                                    #print("got translated output: " + str(output))

                                    
                                                    if 'previous_value' not in item:
                                                        item['previous_value'] = None # We remember the previous value that was sent to the second device. If we sent it before, we don't resend it, to avoid overwhelming the API. TODO: makes more sense to check if the previous input was the same as the result? Although I guess this has the same effect.
                                    
                                    
                                                    # Figure out what type of variable it is: integer or float
                                                    try:
                                                        numeric_value = get_int_or_float(output)
                                                        #print("initial numeric_value = " + str(numeric_value))
                                                        if 'property2_type' in item:
                                                            if str(item['property2_type']) == 'integer':
                                                                numeric_value = round(numeric_value)
                                                        else:
                                                        
                                                            if self.DEBUG:
                                                                print("property2_type int ot float type was not in item, falling back to get_int_or_float")
                                                        
                                                            #temporary fix, as sending floats to percentage properties doesn't work properly.
                                                            numeric_value = round(numeric_value)
                                                            
                                                    except Exception as ex:
                                                        if self.DEBUG:
                                                            print("Error turning into int: " + str(ex))
                                                        continue
                                    
                                    
                                                    if not 'previous_value' in self.persistent_data['items'][index]:
                                                        self.persistent_data['items'][index]['previous_value'] = None

                                    
                                                    if str(item['previous_value']) == str(numeric_value):
                                                        if self.DEBUG:
                                                            print("current value was already set, will not do PUT")
                                                    else:

                                                        try:
                                                            if self.DEBUG:
                                                                print("new value for: " + str(item['thing2']) + " - " + str(item['property2']) + ", will update this numeric_value via API: " + str(numeric_value))
                        
                                    
                                                            data_to_put = {}
                                                            data_to_put[str(item['property2'])] = numeric_value
                                                            if self.DEBUG:
                                                                print("data_to_put = " + str(data_to_put))
                                                            api_put_result = self.api_put( '/things/' + str(item['thing2']) + '/properties/' + str(item['property2']), data_to_put )
                                                            time.sleep(.02)
                                                            attempted_connections += 1
                                                
                                                            try:
                                                                key = list(api_put_result.keys())[0]
                                                                if key == "error":
                                                                    api_error_spotted += 1
                                                        
                                                                    if self.DEBUG:
                                                                        print("api_put_result['error'] = " + str(api_put_result[key]))
                                                                    if api_put_result[key] == 500:
                                                                        if self.DEBUG:
                                                                            print("API PUT failed with a 500 server error.")
                                                                        if self.ignore_missing_properties == False:
                                                                            self.error_counter += 2
                                                    
                                                                else:
                                                                    # updating the property to the new value worked
                                                                    self.persistent_data['items'][index]['previous_value'] = numeric_value
                                                    
                                            
                                                            except Exception as ex:
                                                                if self.DEBUG:
                                                                    print("Error while checking if PUT was succesful: " + str(ex))
                                        
                                                        except Exception as ex:
                                                            print("Error late in putting via API: " + str(ex))
                                    
                                                else:
                                                    if self.DEBUG:
                                                        print("input was out of bounds")
                                    
                                    
                                    except Exception as ex:
                                        if self.DEBUG:
                                            print("Error putting via API: " + str(ex))

                                    # For how many items one of more API connections were attempted.
                                    if attempted_connections > 0:
                                        attempted_items += 1  
                                
                                    # If any of those API connections failed, we count that item as an item with API issues.
                                    if api_error_spotted > 0:
                                        if self.DEBUG:
                                            print("total api_error_spotted: " + str(api_error_spotted))
                                        self.items_with_issues += 1
                                        if not self.api_seems_down:
                                            self.persistent_data['items'][index]['api_error_count'] += 1
                                            if self.DEBUG:
                                                print("total api error count for this item is now: " + str(self.persistent_data['items'][index]['api_error_count']))
                                    elif self.persistent_data['items'][index]['api_error_count'] > 0:
                                        if self.DEBUG:
                                            print("setting device back to intended speed after succesful api call: " + str(int(self.persistent_data['items'][index]['speed'])))
                                        self.persistent_data['items'][index]['api_error_count'] = int(self.persistent_data['items'][index]['speed'])
                        
                                    # once every hour check for often the thing made a failed run. If it's a lot.. disable it? Then the user can find out and reset the counter too.
                                    if self.minutes == 20:
                                        #if not self.ignore_missing_properties:
                                        if self.persistent_data['items'][index]['api_error_count'] > 50 and not self.ignore_missing_properties:
                                            self.persistent_data['items'][index]['enabled'] = False
                                    
                                        #self.there_are_missing_properties = False # perhaps with this device disabled the problem with missing properties is now solved.
                                        self.save_persistent_data()
                                
                                # This item somehow had missing values. That's not supposed to happen.
                                elif 'enabled' in item: # this might be superfluous
                                    if item['enabled']:
                                        # the device should not be enabled, it's incomplete.
                                        self.persistent_data['items'][index]['enabled'] = False
                                        self.save_persistent_data()
                                        if self.DEBUG:
                                            print("Set an incomplete enabled item to disabled")
                            
                            except Exception as ex:
                                print("Error while looping over an item: " + str(ex))
                                print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))   
                
                
                        # the for-loop is done
                        #if all followers we tried to connect to have api errors simultaneously, that means the internet is down, and API errors should be ignored.
                        if self.DEBUG:
                            print("attempted_items: " + str(attempted_items))
                            print("items_with_issues: " + str(self.items_with_issues))
                    
                        if enabled_count > 2:
                            if self.items_with_issues == attempted_items != 0:
                                self.api_seems_down = True
                                print("all attempted items are having API issues. API is probably not reachable. (1)") 
                                    # TODO: reset all api error counter? Or lower them a bit? Or just create a variable for the next loop? The last one :-)
                        
                                time.sleep(2) # give the API a break
                    
                            elif self.items_with_issues == len(self.persistent_data['items']):
                                # all items have issues
                                if self.DEBUG:
                                    print("all Followers items are having API issues. API is probably not reachable. Sleeping 2 seconds.") 
                                self.api_seems_down = True
                                time.sleep(2) # give the API a break
                            else:
                                self.api_seems_down = False
                        else:
                            self.api_seems_down = False
                        #print("items: " + str(self.persistent_data['items']))
                        if self.DEBUG:
                            print(".")
                    
                
                        if self.error_counter > 0:
                            self.error_counter -= 1 # if everything went ok, the error count will slowly drop down to 0 again, at which point extra api calls to check out what's wrong will no longer be needed.
                    
            

                    else:
                        # if the API never provided a good things list, then we will keep trying to get that first.
                        time.sleep(4)
                        if self.DEBUG:
                            print("making another attempt to get the initial things list")
                        self.update_simple_things()


                except Exception as ex:
                    if self.DEBUG:
                        print("General clock error: " + str(ex))
                        print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))

                



    def update_simple_things(self):
        if self.DEBUG:
            print("in update_simple_things")
        try:
            fresh_things = self.api_get("/things")
            if self.DEBUG:
                print("- Did the things API call.")
                #print(str(self.things))
            
            if hasattr(fresh_things, 'error'):
                if self.DEBUG:
                    print("try_update_things: get_api returned an error.")
                
                if fresh_things['error'] == '403':
                    if self.DEBUG:
                        print("Spotted 403 error, will try to switch to https API calls")
                    self.api_server = 'https://127.0.0.1:4443'
                    #fresh_things = self.api_get("/things")
                    #if self.DEBUG:
                        #print("Tried the API call again, this time at port 4443. Result: " + str(fresh_things))
                return
            
            self.things = fresh_things
            
        except Exception as ex:
            print("Error getting things from API: " + str(ex))
            
        try:
            new_simple_things = {}
            for thing in self.things:
                if self.DEBUG:
                    print("thing = "  + str(thing))
                    
                try:
                    thing_id = str(thing['id'].rsplit('/', 1)[-1])
                    if self.DEBUG:
                        print("thing_id = "  + str(thing_id))
                    new_simple_things[thing_id] = []
                
                    if 'properties' in thing:
                        for thing_property_key in thing['properties']:
                            #print("-thing_property_key = " + str(thing_property_key))
                            
                            try:
                                found_links = False
                                if 'links' in thing['properties'][thing_property_key]:
                                    if len(thing['properties'][thing_property_key]['links']) > 0:
                                        property_id = thing['properties'][thing_property_key]['links'][0]['href'].rsplit('/', 1)[-1]
                                        found_links = True
                        
                                if found_links == False:
                                    if 'forms' in thing['properties'][thing_property_key]:
                                        if len(thing['properties'][thing_property_key]['forms']) > 0:
                                            property_id = thing['properties'][thing_property_key]['forms'][0]['href'].rsplit('/', 1)[-1]
                                if self.DEBUG:
                                    print("property_id = " + str(property_id))
                            
                            except Exception as ex:
                                print("Error extracting links/forms: " + str(ex))
                            # all that trouble.. what is property_id used for?
                        
                            new_simple_things[thing_id].append(thing_property_key)
                            
                
                except Exception as ex:
                    print("Error parsing to simple_things: " + str(ex))
                
            self.simple_things = new_simple_things
            self.got_good_things_list = True
            if self.DEBUG:
                print("- self.simple_things is now: " + str(self.simple_things))
                
        except Exception as ex:
            print("Error parsing to simple_things: " + str(ex))
        
    



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
        
                            fresh_token = request.body['jwt']
                            if fresh_token != None:
                                if len(str(fresh_token)) > 10:
                                    self.persistent_data['token'] = str(fresh_token)
        
                            # Check if a token is present
                            token = True
                            if self.persistent_data['token'] == None:
                                state = 'This addon requires an authorization token to work. Visit the settings page of this addon to learn more.'
                                token = False

                            return APIResponse(
                                status=200,
                                content_type='application/json',
                                content=json.dumps({'state' : state, 'items' : self.persistent_data['items'], 'debug':self.DEBUG, 'ready':self.ready, 'token': token}),
                            )
                        except Exception as ex:
                            print("Error getting init data: " + str(ex))
                            return APIResponse(
                                status=500,
                                content_type='application/json',
                                content=json.dumps({'state' : "Internal error: no thing data", 'items' : [], 'debug':self.DEBUG, 'ready':self.ready, 'token': token}),
                            )
                            
                    
                    elif request.path == '/update_items':
                        try:
                            self.persistent_data['items'] = request.body['items']
                            
                            self.update_simple_things()
                            if self.got_good_things_list:
                                # try to get the correct property type (integer/float)
                                try:
                                    for i in range(len(self.persistent_data['items'])):
                                        
                                        item = self.persistent_data['items'][i]
                                        #print("_item: " + str(item))
                                        if 'thing2' in item and 'property2' in item:
                                            for thing in self.things:
                                                thing_id = str(thing['id'].rsplit('/', 1)[-1])
                                                if str(item['thing2']) == thing_id:
                                                    for thing_property_key in thing['properties']:
                                                    
                                                        if len(thing['properties'][thing_property_key]['links']) > 0:
                                                            property_id = thing['properties'][thing_property_key]['links'][0]['href'].rsplit('/', 1)[-1]
                                                        else:
                                                            property_id = thing['properties'][thing_property_key]['links'][0]['forms'].rsplit('/', 1)[-1]
                                                            
                                                        if str(item['property2']) == property_id:
                                                            if self.DEBUG:
                                                                print("Property: " + str(property_id) + ", was of variable type: " + str(thing['properties'][thing_property_key]['type']))
                                                            self.persistent_data['items'][i]['property2_type'] = str(thing['properties'][thing_property_key]['type'])

                      
                                except Exception as ex:
                                    if self.DEBUG:
                                        print("Error finding if property should be int or float: " + str(ex))
                            
                            else:
                                return APIResponse(
                                    status=500,
                                    content_type='application/json',
                                    content=json.dumps({"state":"Please wait a few seconds, Followers has not fully loaded yet"}),
                                )
                            
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
                                content=json.dumps({"state":"Error updating items: " + str(ex)}),
                            )
                        
                    else:
                        return APIResponse(status=404)
                        
                        
                except Exception as ex:
                    if self.DEBUG:
                        print("Error while handling request: " + str(ex))
                    return APIResponse(
                        status=500,
                        content_type='application/json',
                        content=json.dumps({"state":"Error in API handler"}),
                    )
                    
            else:
                return APIResponse(status=404)
                
        except Exception as e:
            if self.DEBUG:
                print("Failed to handle UX extension API request: " + str(e))
            return APIResponse(
                status=500,
                content_type='application/json',
                content=json.dumps({"state":"API Error"}),
            )


    def unload(self):
        self.running = False
        if self.DEBUG:
            print("Followers shutting down")




    def cancel_pairing(self):
        """Cancel the pairing process."""
        #print("END OF PAIRING -----------------------------")

        # Get all the things via the API.
        self.update_simple_things()




#
#  API
#

    def api_get(self, api_path,intent='default'):
        """Returns data from the WebThings Gateway API."""
        if self.DEBUG:
            print("GET PATH = " + str(api_path))
            #print("intent in api_get: " + str(intent))
        #print("GET TOKEN = " + str(self.persistent_data['token']))
        if self.persistent_data['token'] == None:
            print("API GET: PLEASE ENTER YOUR AUTHORIZATION CODE IN THE SETTINGS PAGE")
            return []
        
        try:
            r = requests.get(self.api_server + api_path, headers={
                  'Content-Type': 'application/json',
                  'Accept': 'application/json',
                  'Authorization': 'Bearer ' + str(self.persistent_data['token']),
                }, verify=False, timeout=5)
            if self.DEBUG:
                print("API GET: " + str(r.status_code) + ", reason: " + str(r.reason))

            if r.status_code != 200:
                if self.DEBUG:
                    print("API returned a status code that was not 200. It was: " + str(r.status_code))
                return {"error": str(r.status_code)}
                
            else:
                to_return = r.text
                try:
                    if self.DEBUG:
                        print("api_get: received: " + str(r))
                    #for prop_name in r:
                    #    print(" -> " + str(prop_name))
                    if not '{' in r.text:
                        if self.DEBUG:
                            print("api_get: response was not json (gateway 1.1.0 does that). Turning into json...")
                        
                        if 'things/' in api_path and '/properties/' in api_path:
                            if self.DEBUG:
                                print("properties was in api path: " + str(api_path))
                            likely_property_name = api_path.rsplit('/', 1)[-1]
                            to_return = {}
                            to_return[ likely_property_name ] = json.loads(r.text)
                            if self.DEBUG:
                                print("returning fixed: " + str(to_return))
                            return to_return
                                
                except Exception as ex:
                    print("api_get_fix error: " + str(ex))
                        
                if self.DEBUG:
                    print("returning without 1.1.0 fix")
                return json.loads(r.text)
            
        except Exception as ex:
            print("Error doing http request/loading returned json: " + str(ex))
           
            return {"error": 500}



    def api_put(self, api_path, json_dict, intent='default'):
        """Sends data to the WebThings Gateway API."""
        
        try:
        
            if self.DEBUG:
                print("PUT > api_path = " + str(api_path))
                print("PUT > json dict = " + str(json_dict))
                print("PUT > self.api_server = " + str(self.api_server))
                print("PUT > intent = " + str(intent))
                print("self.gateway_version: " + str(self.gateway_version))
        
            simplified = False
            property_was = None
            if self.gateway_version != "1.0.0":
        
                if 'things/' in api_path and '/properties/' in api_path:
                    if self.DEBUG:
                        print("PUT: properties was in api path: " + str(api_path))
                    for key in json_dict:
                        property_was = key
                        simpler_value = json_dict[key]
                        json_dict = simpler_value
                    #simpler_value = [elem[0] for elem in json_dict.values()]
                    if self.DEBUG:
                        print("simpler 1.1.0 value to put: " + str(simpler_value))
                    simplified = True
                    #likely_property_name = api_path.rsplit('/', 1)[-1]
                    #to_return = {}
            
            
        except Exception as ex:
            print("Error preparing PUT: " + str(ex))

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.persistent_data['token']),
        }
        try:
            r = requests.put(
                self.api_server + api_path,
                json=json_dict,
                headers=headers,
                verify=False,
                timeout=5
            )
            if self.DEBUG:
                print("API PUT: " + str(r.status_code) + ", reason: " + str(r.reason))
                print("PUT returned: " + str(r.text))
                print("PUT returned type: " + str(type(r.text)))
                print("PUT returned len: " + str(len(r.text)))

            if r.status_code < 200 or r.status_code > 208:
                if self.DEBUG:
                    print("Error communicating: " + str(r.status_code))
                return {"error": str(r.status_code)}
            else:
                return_value = {}
                try:
                    if len(r.text) != 0:
                        if simplified:
                            if property_was != None:
                                if not '{' in r.text:
                                    return_value[property_was] = r.text
                                else:
                                    return_value[property_was] = json.loads(r.text) # json.loads('{"' + property_was + '":' + r.text + '}')
                        else:
                            return_value = json.loads(r.text)
                except Exception as ex:
                    if self.DEBUG:
                        print("Error reconstructing put response: " + str(ex))
                
                return_value['succes'] = True
                return return_value

        except Exception as ex:
            print("Error doing http request/loading returned json: " + str(ex))
            return {"error": 500}

#
#  SAVE TO PERSISTENCE
#

    def save_persistent_data(self):
        if self.DEBUG:
            print("Follower: Saving to persistence data store at path: " + str(self.persistence_file_path))
            
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
                json.dump( self.persistent_data, open( self.persistence_file_path, 'w+' ), indent=4 )
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