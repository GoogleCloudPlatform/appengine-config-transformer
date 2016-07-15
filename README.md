Copyright 2015 Google Inc.
All rights reserved.

# App Engine Configuration File Transformer

Use this command-line tool to transform and copy your YAML formatted App Engine configuration files
into JSON formatted files that are suppported by the Google App Engine Admin API.

## Requirements:

* Install Python, either:
  * [Python 2.7](https://www.python.org/)
  * [App Engine SDK for Python](https://cloud-dot-devsite.googleplex.com/appengine/downloads#Google_App_Engine_SDK_for_Python)
* Install the 'yaml' library: [PyYAML package](https://pypi.python.org/pypi/PyYAML)

### Example Installation:

1. Download and install the [App Engine SDK for Python](https://cloud-dot-devsite.googleplex.com/appengine/downloads#Google_App_Engine_SDK_for_Python).
1. Install the 'yaml' library:  
   `sudo apt-get install python-yaml`
1. Clone the appengine-config-transformer project:  
   `git clone https://github.com/GoogleCloudPlatform/appengine-config-transformer.git`


## Usage:

    ./convert_yaml.py app.yaml > app.json
    
### Example:

    cd appengine-config-transformer  
    ./convert_yaml.py $HOME/appengine-guestbook-python/app.yaml > $HOME/appengine-guestbook-python/app.json
