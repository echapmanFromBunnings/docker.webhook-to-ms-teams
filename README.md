
# docker.webhook-to-ms-teams

This Dockerfile definition creates a simple and small docker image based on Alpine OS and Python. The size of this image is below 60 megabytes.

## Purpose

Different components are required for the project to send a notification from Github events to a channel in MS Teams via Gitub Actions:

1) a connector (Webhook app) in a MS Teams channel that allows a webhook to receive messages
2) a Github action in the respective repository, which should send messages to this MS Teams channel
3) an available system that provides Python to send the message wia http request

The footprint of the image should be as small as possible. The goal is to create an flexible image that is as small as possible, that is quickly built and accessed, and that can be easily managed and maintained.

The size of the created image is currently about 57 megabytes.

## How it works

This docker file is the basis for point 3). The image is created and provided on Docker Hub via the docker file provided here. This means that it can be used within the action under 2). The prerequisite for this is that the image is either created manually or - as in this case - automatically created by linked accounts between Docker Hub and Github as soon as the sources of the repository change.

## Installation

No special procedures are required to adopt the repository and set it up:

1) Create a fork of this repository
2) Link your Docker Hub and Github accounts
3) create a new repository in Docker Hub and link it to a repository on Github
4) define build rules for the Docker Hub repository. Example configuration:
   - Source type:Branch
   - Source:master
   - Docker tag:latest
   - Dockerfile location: Dockerfile
   - Build caching: on
5) Update the github repository to create the Docker Hub Repository

## License

MIT License

Copyright (c) 2020 R. Fuehrer

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.