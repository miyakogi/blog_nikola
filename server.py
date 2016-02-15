#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from livereload import Server, shell

server = Server()
server.watch('./posts/*.md', shell('nikola build'))
server.serve(port=8889, root='./output')
