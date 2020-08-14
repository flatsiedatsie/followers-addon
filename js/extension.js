(function() {
  class Followers extends window.Extension {
    constructor() {
      	super('followers');
		//console.log("Adding followers addon to menu");
      	this.addMenuEntry('Followers');

      	this.content = '';
		
		this.item_elements = ['limit1','limit2','thing1','property1','limit3','limit4','thing2','property2'];
		this.all_things;
		this.items_list = [];
		
		this.item_number = 0;

		fetch(`/extensions/${this.id}/views/content.html`)
        .then((res) => res.text())
        .then((text) => {
         	this.content = text;
        })
        .catch((e) => console.error('Failed to fetch content:', e));
    }



    show() {
		this.view.innerHTML = this.content;
	  	//console.log("followers show called");

		const pre = document.getElementById('extension-followers-response-data');
		const view = document.getElementById('extension-followers-view'); 
		//const original = document.getElementById('extension-followers-original-item');
		//const list = document.getElementById('extension-followers-list');
		const leader_dropdown = document.querySelectorAll(' #extension-followers-view #extension-followers-original-item .extension-followers-thing1')[0];
		const follower_dropdown = document.querySelectorAll(' #extension-followers-view #extension-followers-original-item .extension-followers-thing2')[0];
	
		pre.innerText = "";
		
	  	// Click event for ADD button
		document.getElementById("extension-followers-add-button").addEventListener('click', () => {
			this.items_list.push({'enabled': false});
			this.regenerate_items();
			view.scrollTop = view.scrollHeight;
	  	});
		

		// Pre populating the original item that will be clones to create new ones
	    API.getThings().then((things) => {
			
			this.all_things = things;
			//console.log("all things: ");
			//console.log(things);
			
			
			// pre-populate the hidden 'new' item with all the thing names
			var thing_ids = [];
			var thing_titles = [];
			
			for (let key in things){

				var thing_title = 'unknown';
				if( things[key].hasOwnProperty('title') ){
					thing_title = things[key]['title'];
				}
				else if( things[key].hasOwnProperty('label') ){
					thing_title = things[key]['label'];
				}
				
				//console.log(thing_title);
				try{
					if (thing_title.startsWith('highlights-') ){
						// Skip highlight items
						continue;
					}
					
				}
				catch(e){console.log("error in creating list of things for highlights: " + e);}
			
				var thing_id = things[key]['href'].substr(things[key]['href'].lastIndexOf('/') + 1);
				try{
					if (thing_id.startsWith('highlights-') ){
						// Skip items that are already highlight clones themselves.
						//console.log(thing_id + " starts with highlight-, so skipping.");
						continue;
					}
					
				}
				catch(e){console.log("error in creating list of things for highlights: " + e);}
				thing_ids.push( things[key]['href'].substr(things[key]['href'].lastIndexOf('/') + 1) );
				

				// for each thing, get its property list. Only add it to the selectable list if it has properties that are numbers. 
				// In case of the second thing, also make sure there is at least one non-read-only property.
				const property_lists = this.get_property_lists(things[key]['properties']);
				
				if(property_lists['property1_list'].length > 0){
					//console.log("adding thing to source list because a property has a number");
					leader_dropdown.options[leader_dropdown.options.length] = new Option(thing_title, thing_id);
					if(property_lists['property2_list'].length > 0){
						//console.log("adding thing to target list because a property can be written");
						follower_dropdown.options[follower_dropdown.options.length] = new Option(thing_title, thing_id);
					}	
				}
			}
			
	  		// Get list of items
	        window.API.postJson(
	          `/extensions/${this.id}/api/init`

	        ).then((body) => {
				//console.log("Python API result:"); 
				//console.log(body);
				//console.log(body['items']);
				if(body['state'] == 'ok'){
					this.items_list = body['items']
					this.regenerate_items();
				}
				else{
					pre.innerText = body['state'];
				}
				

	        }).catch((e) => {
	          	//pre.innerText = e.toString();
	  			//console.log("followers: error in calling init via API handler");
	  			console.log(e.toString());
				pre.innerText = "Loading items failed - connection error";
	        });				
				
	    });		

	}
	
	
	
	//
	//  REGENERATE ITEMS
	//
	
	regenerate_items(items){
		//console.log("regenerating");
		//console.log("this.all_things = ");
		//console.log(this.all_things);
		
		const pre = document.getElementById('extension-followers-response-data');
		//const leader_property_dropdown = document.querySelectorAll(' #extension-followers-view #extension-followers-original-item .extension-followers-property2')[0];
		//const follower_property_dropdown = document.querySelectorAll(' #extension-followers-view #extension-followers-original-item .extension-followers-property2')[0];
		
		try {
			items = this.items_list
		
			const original = document.getElementById('extension-followers-original-item');
			const list = document.getElementById('extension-followers-list');
			list.innerHTML = "";
		
			// Loop over all items
			for( var item in items ){
				var clone = original.cloneNode(true);
				clone.removeAttribute('id');

				// Add delete button click event
				const delete_button = clone.querySelectorAll('.extension-followers-item-delete-button')[0];
				delete_button.addEventListener('click', (event) => {
					var target = event.currentTarget;
					var parent3 = target.parentElement.parentElement.parentElement; //parent of "target"
					parent3.classList.add("delete");
			  	});
			
				const final_delete_button = clone.querySelectorAll('.rule-delete-confirm-button')[0];
				final_delete_button.addEventListener('click', (event) => {
					var target = event.currentTarget;
					var parent3 = target.parentElement.parentElement.parentElement; //parent of "target"
					var parent4 = parent3.parentElement;
					parent4.removeChild(parent3);
					parent4.dispatchEvent( new CustomEvent('change',{bubbles:true}) );
				});
				
				
				
			
				const cancel_delete_button = clone.querySelectorAll('.rule-delete-cancel-button')[0];
				cancel_delete_button.addEventListener('click', (event) => {
					var target = event.currentTarget;
					var parent3 = target.parentElement.parentElement.parentElement;
					parent3.classList.remove("delete");
					
				});
				
				// Change switch icon
				clone.querySelectorAll('.switch-checkbox')[0].id = 'toggle' + this.item_number;
				clone.querySelectorAll('.switch-slider')[0].htmlFor = 'toggle' + this.item_number;
				this.item_number++;
				
				
			
				// Populate the properties dropdown
				try{
					for( var thing in this.all_things ){
						
						//console.log("this.all_things[thing]['id'] = " + this.all_things[thing]['id']);
						//console.log("items[item]['thing1'] = " + items[item]['thing1']);
						
						if( this.all_things[thing]['id'].endsWith( items[item]['thing1'] ) ){
							//console.log("bingo, at thing1. Now to grab properties.");
							const property1_dropdown = clone.querySelectorAll('.extension-followers-property1')[0];
							const property_lists = this.get_property_lists(this.all_things[thing]['properties']);
							//console.log("property lists:");
							//console.log(property_lists);
							
							for( var title in property_lists['property1_list'] ){
								//console.log("adding prop title:" + property_lists['property1_list'][title]);
								property1_dropdown.options[property1_dropdown.options.length] = new Option(property_lists['property1_list'][title], property_lists['property1_system_list'][title]);
							}
						}
						if( this.all_things[thing]['id'].endsWith( items[item]['thing2'] ) ){
							//console.log("bongo, at thing2 (" + items[item]['thing2'] + "). Now to grab properties.");
							const property2_dropdown = clone.querySelectorAll('.extension-followers-property2')[0];
							//console.log(property2_dropdown);
							const property_lists = this.get_property_lists(this.all_things[thing]['properties']);
							//console.log(property_lists['property2_list']);
							for( var title in property_lists['property2_list'] ){
								//console.log("adding prop title:" + property_lists['property2_list'][title]);
								property2_dropdown.options[property2_dropdown.options.length] = new Option(property_lists['property2_list'][title], property_lists['property2_system_list'][title]);
							}
						}
					}
				}
				catch (e) {
					console.log("Could not loop over all_things: " + e); // pass exception object to error handler
				}
				
			
				// Update to the actual values of regenerated item
				for(var key in this.item_elements){
					try {
						if(this.item_elements[key] != 'enabled'){
							clone.querySelectorAll('.extension-followers-' + this.item_elements[key] )[0].value = items[item][ this.item_elements[key] ];
						}
					}
					catch (e) {
						console.log("Could not regenerate actual values of follower: " + e);
					}
				}
				
				// Set enabled state of regenerated item
				if(items[item]['enabled'] == true){
					//clone.querySelectorAll('.extension-followers-enabled')[0].removeAttribute('checked');
					clone.querySelectorAll('.extension-followers-enabled' )[0].checked = items[item]['enabled'];
				}
				list.append(clone);
			}
			
			

			//
			//  Change listener. Called if the user changes anything in the existing items in the list. Mainly used to update properties if a new thing is selected.
			//
			
			list.addEventListener('change', (event) => {
				//console.log("changed");
				//console.log(event);
				
				try {
					
					// Loops over all the things, and when a thing matches the changed element, its properties list is updated.
					for( var thing in this.all_things ){
						//console.log( this.all_things[thing] );
						
						if( this.all_things[thing]['id'].endsWith( event['target'].value ) ){
							const property_dropdown = event['target'].nextSibling;
							const property_lists = this.get_property_lists(this.all_things[thing]['properties']);
							try{
								if(property_dropdown !== undefined){
									if('options' in property_dropdown){
										var select_length = property_dropdown.options.length;
										for (var i = select_length-1; i >= 0; i--) {
											property_dropdown.options[i] = null;
										}
									}
								}
							}
							catch(e){
								console.log("error clearing property dropdown select options: " + e);
							}

							
							// If thing1 dropdown was changed, update its property titles
							if( event['target'].classList.contains("extension-followers-thing1") ){
								for( var title in property_lists['property1_list'] ){
									property_dropdown.options[property_dropdown.options.length] = new Option(property_lists['property1_list'][title], property_lists['property1_system_list'][title]);
								}
							}
							// If thing2 dropdown was changed, update its property titles
							else if ( event['target'].classList.contains("extension-followers-thing2") ){
								for( var title in property_lists['property2_list'] ){
									property_dropdown.options[property_dropdown.options.length] = new Option(property_lists['property2_list'][title], property_lists['property2_system_list'][title]);
								}
							}
						}
					}
					
				}
				catch (e) {
					console.log("error handling change in follower: " + e);
				}
				
				
				
				var updated_values = [];
				const item_list = document.querySelectorAll('#extension-followers-list .extension-followers-item');
				
				// Loop over all the elements
				item_list.forEach(item => {
					var new_values = {};
					var incomplete = false;
					
					// For each item in the followers list, loop over all values in the item to check if they are filled.
					for (let value_name in this.item_elements){
						const new_value = item.querySelectorAll('.extension-followers-' + this.item_elements[value_name])[0].value;
						//console.log("new_value = " + new_value);
						//console.log("new_value.length = " + new_value.length);
						if(new_value.length > 0){
							new_values[ this.item_elements[value_name] ] = item.querySelectorAll('.extension-followers-' + this.item_elements[value_name])[0].value;
						}
						else{
							incomplete = true;
						}
					}
					//console.log( "Is item checked?" + item.querySelectorAll('.extension-followers-enabled')[0].checked );
					
					// Check if the minimum and maximum values are not the same, as that could lead to strange errors
					const delta1 = Math.abs( new_values['limit1'] - new_values['limit2'] );
					const delta2 = Math.abs( new_values['limit3'] - new_values['limit4'] );
					//console.log("delta1 = " + delta1);
					//console.log("delta2 = " + delta2);
					
					// Set the item to enabled as soon as all values are filled in properly. This is done only once.
					if( incomplete == false && delta1 > 0 && delta2 > 0 && item.classList.contains('new') && item.querySelectorAll('.extension-followers-enabled')[0].checked == false ){
					    item.classList.remove('new');
						item.querySelectorAll('.extension-followers-enabled')[0].checked = true;
					}
					// Disable an item if it no longer has all required values, or if they are set incorrectly
					if( (incomplete == true || delta1 == 0 || delta2 == 0 ) && item.querySelectorAll('.extension-followers-enabled')[0].checked == true ){
						item.querySelectorAll('.extension-followers-enabled')[0].checked = false;
					}

					// TODO: what happens with negative values? or a mix of negative and positive values?

					// Check if this item is enabled
					new_values['enabled'] = item.querySelectorAll('.extension-followers-enabled')[0].checked;
					
					updated_values.push(new_values);
					
				});
				
				//console.log("updated_values:");
				//console.log(updated_values);
				
				
				// Store the updated list
				this.items_list = updated_values;
				
				// Send new values to backend
				window.API.postJson(
					`/extensions/${this.id}/api/update_items`,
					{'items':updated_values}
				).then((body) => { 
					//thing_list.innerText = body['state'];
					//console.log(body); 
					if( body['state'] != 'ok' ){
						pre.innerText = body['state'];
					}

				}).catch((e) => {
					console.log("followers: error in save items handler");
					pre.innerText = e.toString();
				});
				
			});
			
		}
		catch (e) {
			// statements to handle any exceptions
			console.log(e); // pass exception object to error handler
		}
	}
	




	//
	//  A helper method that generates nice lists of properties from a Gateway property dictionary
	//
	get_property_lists(properties){
		//console.log("checking properties on:");
		//console.log(properties);
		var property1_list = []; // list of user friendly titles
		var property1_system_list = []; // list internal property id's
		var property2_list = [];
		var property2_system_list = [];
		
		for (let prop in properties){
			//console.log(properties[prop]);
			var title = 'unknown';
			if( properties[prop].hasOwnProperty('title') ){
				title = properties[prop]['title'];
			}
			else if( properties[prop].hasOwnProperty('label') ){
				title = properties[prop]['label'];
			}
				
			
			var system_title = properties[prop]['links'][0]['href'].substr(properties[prop]['links'][0]['href'].lastIndexOf('/') + 1);

			// If a property is a number, add it to the list of possible source properties
			if( properties[prop]['type'] == 'integer' || properties[prop]['type'] == 'float' || properties[prop]['type'] == 'number'){
				
				property1_list.push(title);
				property1_system_list.push(system_title);
				
				// If a property is not read-only, then it can be added to the list of 'target' properties that can be changed based on a 'source' property
				if ( 'readOnly' in properties[prop] ) { // If readOnly is set, it could still be set to 'false'.
					if(properties[prop]['readOnly'] == false){
						property2_list.push(title);
						property2_system_list.push(system_title);
					}
				}
				else{ // If readOnly is not set, we can asume the property is not readOnly.
					property2_list.push(title);
					property2_system_list.push(system_title);
				}
			}
		}
		
		// Sort lists alphabetically.
		/*
		property1_list.sort();
		property1_system_list.sort();
		property2_list.sort();
		property2_system_list.sort();
		*/
		
		return { 'property1_list' : property1_list, 'property1_system_list' : property1_system_list, 'property2_list' : property2_list,'property2_system_list' : property2_system_list };
	}

		
		
		
		
	// HELPER METHODS
	
	hasClass(ele,cls) {
		//console.log(ele);
		//console.log(cls);
	  	return !!ele.className.match(new RegExp('(\\s|^)'+cls+'(\\s|$)'));
	}

	addClass(ele,cls) {
	  	if (!this.hasClass(ele,cls)) ele.className += " "+cls;
	}

	removeClass(ele,cls) {
	  	if (this.hasClass(ele,cls)) {
	    	var reg = new RegExp('(\\s|^)'+cls+'(\\s|$)');
	    	ele.className=ele.className.replace(reg,' ');
	  	}
	}
		
		

  }

  new Followers();
	
})();


