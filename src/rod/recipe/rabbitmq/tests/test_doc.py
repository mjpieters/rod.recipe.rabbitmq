"""Doctest runner for rod.recipe.rabbitmq."""

__docformat__ = 'restructuredtext'

import unittest
import zc.buildout.tests
import zc.buildout.testing

from zope.testing import doctest, renormalizing

optionflags = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE |
               doctest.REPORT_ONLY_FIRST_FAILURE)


def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop('zc.recipe.egg', test)
    zc.buildout.testing.install_develop('rod.recipe.rabbitmq', test)
    zc.buildout.testing.install_develop('simplejson', test)


def test_suite():
    suite = unittest.TestSuite((
            doctest.DocFileSuite(
                '../README.txt',
                setUp=setUp,
                tearDown=zc.buildout.testing.buildoutTearDown,
                optionflags=optionflags,
                checker=renormalizing.RENormalizing([
                        zc.buildout.testing.normalize_path,
                        ]),
                ),
            ))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
