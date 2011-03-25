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

        buildout = self.buildout['buildout']['directory']
        bindir = self.buildout['buildout']['bin-directory']
        part = self.options['location']

        cookie_option = ''   
        cookie = self.options.get('cookie', None)
        if cookie:
            cookie_option = '-setcookie \\"%s\\"' % cookie

        erlang_path = self.options.get('erlang-path')
        if erlang_path:
            erlang_path = 'PATH=%s:$PATH' % erlang_path
        else:
            erlang_path = ''

        rabbitmq_env_template = """\
# rod.recipe.rabbitmq specific overrides
RABBITMQ_HOME="%(part)s"
[ "x" = "x$HOSTNAME" ] && HOSTNAME=`env hostname`
NODENAME=rabbit@${HOSTNAME%%%%.*}
CONFIG_FILE=%(buildout)s/etc/rabbitmq
LOG_BASE=%(buildout)s/var/log/rabbitmq
MNESIA_BASE=%(buildout)s/var/rabbitmq/mnesia
SERVER_START_ARGS="%(cookie_option)s"
RABBITMQ_CTL_ERL_ARGS="%(cookie_option)s"
%(erlang_path)s

[ -f %(buildout)s/etc/rabbitmq-env.conf ] && . %(buildout)s/etc/rabbitmq-env.conf

""" % locals()

        rabbitmq_env = os.path.join(bindir, 'rabbitmq-env')
        script = open(rabbitmq_env, "w")
        script.write(rabbitmq_env_template)
        script.close()
        os.chmod(rabbitmq_env, 0755)

        paths = [rabbitmq_env]

        for script in ('rabbitmq-server', 'rabbitmqctl'):
            link = os.path.join(bindir, script)
            os.symlink(os.path.join(part, 'scripts', script), link)
            paths.append(link)

        return paths

    def install_rabbitmq(self):
        """Downloads and installs RabbitMQ."""

        arch_filename = self.options['url'].split(os.sep)[-1]
        dst = self.options.setdefault('location',
            os.path.join(self.buildout['buildout']['parts-directory'],
            self.name))
        # Re-use the buildout download cache if defined
        downloads_dir = self.buildout['buildout'].get('download-cache')
        if downloads_dir is None:
            download_dir = os.path.join(self.buildout['buildout']['directory'],
                                        'downloads')
            if not os.path.isdir(download_dir):
                os.mkdir(download_dir)
            self.buildout['buildout'].setdefault('download-cache', download_dir)
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
        erlang_path = self.options.get('erlang-path')
        if erlang_path:
            new_path = [erlang_path] + os.environ['PATH'].split(':')
            os.environ['PATH'] = ':'.join(new_path)

        old_cwd = os.getcwd()
        os.chdir(dst)
        retcode = subprocess.call(['make', 'PYTHON=%s' % sys.executable])
        if retcode != 0:
            raise Exception("building RabbitMQ failed")
        os.chdir(old_cwd)
        
        paths = self.gen_scripts()

        for path in remove_after_install:
            shutil.rmtree(path)

        return paths + [dst]

    def install(self):
        """Creates the part."""

        return self.install_rabbitmq()

    def update(self):
        pass