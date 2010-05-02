"""Recipe for setting up RabbitMQ."""

import logging
import os
import pkg_resources
import shutil
import subprocess
import sys
import tempfile
import urllib
import zc.recipe.egg

logger = logging.getLogger(__name__)


class Recipe(zc.recipe.egg.Eggs):
    """Buildout recipe for installing RabbitMQ."""

    def __init__(self, buildout, name, opts):
        """Standard constructor for zc.buildout recipes."""

        super(Recipe, self).__init__(buildout, name, opts)

    def gen_scripts(self):
        """Generates RabbitMQ bin scripts."""

        bindir = self.buildout['buildout']['bin-directory']
        server = os.path.join(bindir, 'rabbitmq-server')

        prefix = self.options.get('prefix', os.getcwd())
        erlang_path = self.options.get(
            'erlang-path', '/usr/local/lib/erlang/bin')
        rabbitmq_part = os.path.join(
            self.buildout['buildout']['parts-directory'], self.name)

        server_template = """#!/bin/sh
NODENAME=rabbit
NODE_IP_ADDRESS=0.0.0.0
NODE_PORT=5672
SERVER_ERL_ARGS="+K true +A30 \
-kernel inet_default_listen_options [{nodelay,true},{sndbuf,16384},{recbuf,4096}] \
-kernel inet_default_connect_options [{nodelay,true}]"
CLUSTER_CONFIG_FILE=%(prefix)s/etc/rabbitmq_cluster.config
LOG_BASE=%(prefix)s/var/log/rabbitmq
MNESIA_BASE=%(prefix)s/var
SERVER_START_ARGS=

[ -f %(prefix)s/etc/rabbitmq.conf ] && . %(prefix)s/etc/rabbitmq.conf

[ "x" = "x$RABBITMQ_NODENAME" ] && RABBITMQ_NODENAME=${NODENAME}
[ "x" = "x$RABBITMQ_NODE_IP_ADDRESS" ] && RABBITMQ_NODE_IP_ADDRESS=${NODE_IP_ADDRESS}
[ "x" = "x$RABBITMQ_NODE_PORT" ] && RABBITMQ_NODE_PORT=${NODE_PORT}
[ "x" = "x$RABBITMQ_SERVER_ERL_ARGS" ] && RABBITMQ_SERVER_ERL_ARGS=${SERVER_ERL_ARGS}
[ "x" = "x$RABBITMQ_CLUSTER_CONFIG_FILE" ] && RABBITMQ_CLUSTER_CONFIG_FILE=${CLUSTER_CONFIG_FILE}
[ "x" = "x$RABBITMQ_LOG_BASE" ] && RABBITMQ_LOG_BASE=${LOG_BASE}
[ "x" = "x$RABBITMQ_MNESIA_BASE" ] && RABBITMQ_MNESIA_BASE=${MNESIA_BASE}
[ "x" = "x$RABBITMQ_SERVER_START_ARGS" ] && RABBITMQ_SERVER_START_ARGS=${SERVER_START_ARGS}

[ "x" = "x$RABBITMQ_MNESIA_DIR" ] && RABBITMQ_MNESIA_DIR=${MNESIA_DIR}
[ "x" = "x$RABBITMQ_MNESIA_DIR" ] && RABBITMQ_MNESIA_DIR=${RABBITMQ_MNESIA_BASE}/${RABBITMQ_NODENAME}

## Log rotation
[ "x" = "x$RABBITMQ_LOGS" ] && RABBITMQ_LOGS=${LOGS}
[ "x" = "x$RABBITMQ_LOGS" ] && RABBITMQ_LOGS="${RABBITMQ_LOG_BASE}/${RABBITMQ_NODENAME}.log"
[ "x" = "x$RABBITMQ_SASL_LOGS" ] && RABBITMQ_SASL_LOGS=${SASL_LOGS}
[ "x" = "x$RABBITMQ_SASL_LOGS" ] && RABBITMQ_SASL_LOGS="${RABBITMQ_LOG_BASE}/${RABBITMQ_NODENAME}-sasl.log"
[ "x" = "x$RABBITMQ_BACKUP_EXTENSION" ] && RABBITMQ_BACKUP_EXTENSION=${BACKUP_EXTENSION}
[ "x" = "x$RABBITMQ_BACKUP_EXTENSION" ] && RABBITMQ_BACKUP_EXTENSION=".1"

[ -f  "${RABBITMQ_LOGS}" ] && cat "${RABBITMQ_LOGS}" >> "${RABBITMQ_LOGS}${RABBITMQ_BACKUP_EXTENSION}"
[ -f  "${RABBITMQ_SASL_LOGS}" ] && cat "${RABBITMQ_SASL_LOGS}" >> "${RABBITMQ_SASL_LOGS}${RABBITMQ_BACKUP_EXTENSION}"

if [ -f "$RABBITMQ_CLUSTER_CONFIG_FILE" ]; then
    RABBITMQ_CLUSTER_CONFIG_OPTION="-rabbit cluster_config \"$RABBITMQ_CLUSTER_CONFIG_FILE\""
else
    RABBITMQ_CLUSTER_CONFIG_OPTION=""
fi

RABBITMQ_START_RABBIT=
[ "x" = "x$RABBITMQ_NODE_ONLY" ] && RABBITMQ_START_RABBIT='-noinput -s rabbit'

# we need to turn off path expansion because some of the vars, notably
# RABBITMQ_SERVER_ERL_ARGS, contain terms that look like globs and
# there is no other way of preventing their expansion.
set -f

exec %(erlang_path)s/erl \\
    -pa "%(rabbitmq_part)s/ebin" \\
    ${RABBITMQ_START_RABBIT} \\
    -sname ${RABBITMQ_NODENAME} \\
    -boot start_sasl \\
    +W w \\
    ${RABBITMQ_SERVER_ERL_ARGS} \\
    -rabbit tcp_listeners '[{"'${RABBITMQ_NODE_IP_ADDRESS}'", '${RABBITMQ_NODE_PORT}'}]' \\
    -sasl errlog_type error \\
    -kernel error_logger '{file,"'${RABBITMQ_LOGS}'"}' \\
    -sasl sasl_error_logger '{file,"'${RABBITMQ_SASL_LOGS}'"}' \\
    -os_mon start_cpu_sup true \\
    -os_mon start_disksup false \\
    -os_mon start_memsup false \\
    -os_mon start_os_sup false \\
    -os_mon memsup_system_only true \\
    -os_mon system_memory_high_watermark 0.95 \\
    -mnesia dir "\\"${RABBITMQ_MNESIA_DIR}\\"" \\
    ${RABBITMQ_CLUSTER_CONFIG_OPTION} \\
    ${RABBITMQ_SERVER_START_ARGS} \\
    "$@"
""" % locals()

        script = open(server, "w")
        script.write(server_template)
        script.close()
        os.chmod(server, 0755)

        ctl = os.path.join(bindir, 'rabbitmqctl')

        ctl_template = """#/bin/sh

NODENAME=rabbit

[ "x" = "x$RABBITMQ_NODENAME" ] && RABBITMQ_NODENAME=${NODENAME}
[ "x" = "x$RABBITMQ_CTL_ERL_ARGS" ] && RABBITMQ_CTL_ERL_ARGS=${CTL_ERL_ARGS}

exec %(erlang_path)s/erl \\
    -pa "%(rabbitmq_part)s/ebin" \\
    -noinput \\
    -hidden \\
    ${RABBITMQ_CTL_ERL_ARGS} \\
    -name rabbitmqctl$$ \\
    -s rabbit_control \\
    -nodename $RABBITMQ_NODENAME \\
    -extra "$@"
""" % locals()

        script = open(ctl, "w")
        script.write(ctl_template)
        script.close()
        os.chmod(ctl, 0755)

    def install_rabbitmq(self):
        """Downloads and installs RabbitMQ."""

        arch_filename = self.options['url'].split(os.sep)[-1]
        dst = os.path.join(self.buildout['buildout']['parts-directory'],
                           self.name)
        downloads_dir = os.path.join(os.getcwd(), 'downloads')
        if not os.path.isdir(downloads_dir):
            os.mkdir(downloads_dir)
        src = os.path.join(downloads_dir, arch_filename)
        if not os.path.isfile(src):
            logger.info("downloading RabbitMQ distribution...")
            urllib.urlretrieve(self.options['url'], src)
        else:
            logger.info("RabbitMQ distribution already downloaded.")

        extract_dir = tempfile.mkdtemp("buildout-" + self.name)
        remove_after_install = [extract_dir]
        is_ext = arch_filename.endswith
        is_archive = True
        if is_ext('.tar.gz') or is_ext('.tgz'):
            call = ['tar', 'xzf', src, '-C', extract_dir]
        elif is_ext('.zip'):
            call = ['unzip', src, '-d', extract_dir]
        else:
            is_archive = False

        if is_archive:
            retcode = subprocess.call(call)
            if retcode != 0:
                raise Exception("extraction of file %r failed (tempdir: %r)" %
                                (arch_filename, extract_dir))
        else:
            shutil.copy(arch_filename, extract_dir)

        if is_archive:
            top_level_contents = os.listdir(extract_dir)
            if len(top_level_contents) != 1:
                raise ValueError("can't strip top level directory because "
                                 "there is more than one element in the "
                                 "archive.")
            base = os.path.join(extract_dir, top_level_contents[0])
        else:
            base = extract_dir

        if not os.path.isdir(dst):
            os.mkdir(dst)

            for filename in os.listdir(base):
                shutil.move(os.path.join(base, filename),
                            os.path.join(dst, filename))
        else:
            logger.info("RabbitMQ already installed.")

        r = pkg_resources.working_set.find(
            pkg_resources.Requirement.parse('simplejson'))

        os.environ['PYTHONPATH'] = r.location
        erlang_path = self.options.get('erlang-path',
                                       '/usr/local/lib/erlang/bin')
        new_path = [erlang_path] + os.environ['PATH'].split(':')
        os.environ['PATH'] = ':'.join(new_path)

        old_cwd = os.getcwd()
        os.chdir(dst)
        retcode = subprocess.call(['make', 'PYTHON=%s' % sys.executable])
        if retcode != 0:
            raise Exception("building RabbitMQ failed")
        os.chdir(old_cwd)
        
        self.gen_scripts()

        for path in remove_after_install:
            shutil.rmtree(path)

        return (dst,)

    def install(self):
        """Creates the part."""

        return self.install_rabbitmq()

    def update(self):
        """Updates the part."""

        dst = os.path.join(self.buildout['buildout']['parts-directory'],
                           self.name)
        return (dst,)
