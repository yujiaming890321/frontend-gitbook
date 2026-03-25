# npm

## npm-ci - Clean install a project

This command is similar to npm help install, except it's meant to be used in automated environments
such as test platforms, continuous integration, and deployment -- or any situation where you want to
make sure you're doing a clean install of your dependencies.

The main differences between using npm install and npm ci are:

• The project must have an existing package-lock.json or npm-shrinkwrap.json.
npm install依赖package.json，而npm ci依赖package-lock.json

• If dependencies in the package lock do not match those in package.json, npm ci will exit with an error, instead of updating the package lock.

• npm ci can only install entire projects at a time: individual dependencies cannot be added with this command.

• If a node_modules is already present, it will be automatically removed before npm ci begins its install.

• It will never write to package.json or any of the package-locks: installs are essentially frozen.
