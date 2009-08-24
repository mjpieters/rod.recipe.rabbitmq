A brief documentation
=====================

This recipe takes a number of options:

erlang-path
    The path where to find the erlc command (default = /usr/local/bin).

url
    The URL to download the RabbitMQ source distribution.

prefix
    Prefix path (default = <buildout directory>).
 

Tests
=====

We will define a buildout template used by the recipe:

    >>> buildout_cfg = """
    ... [buildout]
    ... parts = rabbitmq
    ... offline = true
    ...
    ... [rabbitmq]
    ... recipe = rod.recipe.rabbitmq
    ... url = http://www.rabbitmq.com/releases/rabbitmq-server/v1.6.0/rabbitmq-server-1.6.0.tar.gz
    ... """

We'll start by creating a buildout:

    >>> import os.path
    >>> write('buildout.cfg', buildout_cfg)

Running the buildout gives us:

    >>> output = system(buildout)
    >>> if output.endswith("ebin/rabbit_app.in > ebin/rabbit.app\n"): True
    ... else: print output
    True
