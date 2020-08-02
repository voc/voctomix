# Voctoremote

This is a very simple script that deploys a simple web page containing configurable buttons that when clicked send configured commands to the voctocore control server.

For now this is just a bunch of preconfigured buttons. The interface doesn't know what composite is currently active and does thus not display it. This is programmed to be really simple for the purpose of possibly using it in conjuction with the [ISDN project](https://c3voc.de/wiki/projects:isdn).

While it is certainly possible to have some kind of web-voctogui using websockets it would significantly increase the complexity of this and would probably be better of in it's own repository and not really suited for the ISDN project. Such an interface could also use mjpeg or h264 videos for previews.

## Requirements

You need Python 3 and flask to run this script.

```bash
$ pip install -r requirements.txt
```

## Development

```bash
# Set the `FLASK_APP` environment variable to point to `voctoremote.py`.
$ export FLASK_APP=example-scripts/voctoremote/voctoremote.py
# Run flask's builtin web server (for development purposes only)
$ flask run
> * Serving Flask app "example-scripts/voctoremote/voctoremote.py"
# etc
#
# If you want to listen on all interfaces:
# $ flask run --host=0.0.0.0
# Change 0.0.0.0 to a known IP address on your machine to *only* listen on that interface 
```

## Production

For production deployment you should use a proper setup like NginX + Gunicorn.
