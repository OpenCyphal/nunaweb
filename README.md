# nunaweb
A web UI for generating code for DSDL via Nunavut.

![Nunaweb screenshot](/screenshots/2021-01-27_ushot_screenshot.png)

Nunaweb makes it easy to generate code for DSDL namespaces from the web.
Simply upload your namespaces as .zip archives (or provide a remote link)
and hit Submit. The web UI will display the commands needed to generate
the code with the specified settings, and then compile your namespaces into
the specified target language.

The application is deployed to production at https://nunaweb.opencyphal.org.

## Setting up a development environment

Nunaweb uses [Vue/Nuxt.js](https://nuxtjs.org/) on the frontend and
[Flask](https://flask.palletsprojects.com/en/1.1.x/) on the backend. It
uses [Nunavut](https://github.com/UAVCAN/nunavut) to generate code.

Clone the repository to get started.

### Frontend setup

`cd` into the `nunaweb/` directory (which contains the frontend) and
run `npm install`. From there, you can run `npm run dev` to start a
development server.

### Backend setup

Because the backend requires several services to be running, we've
simplified startup with a docker-compose file.

1. Install [Docker](https://www.docker.com/) or a compatible container runtime.
2. Install [Docker-Compose](https://docs.docker.com/compose/).
3. Install requirements locally with `pip3 install -r requirements.txt`.
4. Spin up the backend server with `docker-compose up`
   (make sure you add your user to the `docker` group;
   otherwise you may have to use sudo.)

You should now have a development environment set up.

## Contributing

Interested in contributing? You can [file issues](https://github.com/bbworld1/nunaweb/issues)
for bug fixes and improvements or
[submit PRs](https://github.com/bbworld1/nunaweb/pulls) to improve the code.
