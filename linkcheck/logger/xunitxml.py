# -*- coding: iso-8859-1 -*-
"""
An xUnit XML logger.
"""
from . import xmllog
from .. import strformat



class TestResult():
    pass

class XunitXMLLogger(xmllog._XMLLogger):
    """
    xUnit XML output for Jenkins and other CI tools.
    """

    # see https://gist.github.com/Great-Antique/adb2b414110f5d242e57

    LoggerName = "xunitxml"

    LoggerArgs = {
        "filename": "linkchecker-out.xml",
    }

    def start_output(self):
        """
        Write start of checking info as xml comment.
        """
        super(XunitXMLLogger, self).start_output()
        self.tests = []

        self.xml_start_output()
        self.flush()

        # We don't actually start writing the xUnit content yet because we
        # need to know how many tests failed first.


    def log_url(self, url_data):
        """
        Called by linkchecker for each checked link (or only failures).
        """

        t = TestResult()
        t.attrs = {}

        if self.has_part("result"):
            if url_data.result:
                t.attrs['type'] = unicode(url_data.result)
            if not url_data.valid:
                t.failure = True
            else:
                t.failure = False
        else:
            return #TODO?

        if self.has_part("realurl"):
            t.real_url = unicode(url_data.url)

        if self.has_part('url'):
            t.url = unicode(url_data.base_url)

        if url_data.name and self.has_part('name'):
            t.name = "HAD A NAME:" + unicode(url_data.name)
        else:
            t.name = t.url

        t.attrs['name'] = t.name

        if url_data.parent_url and self.has_part('parenturl'):
            t.parent_url = unicode(url_data.parent_url)
            t.line = unicode(url_data.line)
            t.column = unicode(url_data.column)
        else:
            t.parent_url = "No parent URL?"
            t.line = False
            t.column = False

        if url_data.checktime and self.has_part("checktime"):
            t.attrs['time'] = u"%f" % url_data.checktime

        t.text = "{0.name} [{0.real_url}] from {0.parent_url}".format(t)
        #if t.line and t.column:
        #    t.text += "(line {0.line}, column {0.column})".format(t)

        self.tests.append(t)

    def end_output(self, **kwargs):
        """
        Called by linkchecker to conclude logging.  We use it to actually write
        the xUnit content, because we have collected all the test failures.
        """

        # Make a test suite for each page that was checked
        # and have the links on that page correspond to tests
        test_suites = {}
        for test in self.tests:
            if test.parent_url not in test_suites:
                test_suites[test.parent_url] = [test]
            else:
                test_suites[test.parent_url].append(test)

        suites_attrs = {}
        self.xml_starttag(u'testsuites', suites_attrs)
        for common_parent_url, tests in test_suites.iteritems():
            suite_attrs = {"created": strformat.strtime(self.starttime),
                           "name": common_parent_url,
                           "tests": unicode(len(tests)),
                           "errors": unicode(0),
                           "failures": unicode(len([test for test in tests if test.failure])),
                           "skip": unicode(0),
                           }
            self.xml_starttag(u'testsuite', suite_attrs)

            for test in tests:
                self.write_test_log(test)

            self.xml_endtag(u"testsuite")

        self.xml_endtag(u"testsuites")
        self.xml_end_output()
        self.close_fileoutput()


    def write_test_log(self, test):
        if test.failure:
            self.xml_tag(u'testcase',
                         content=test.text,
                         attrs=test.attrs)
            self.flush()

    def end_output_for_one_suite(self, **kwargs):
        """
        Write XML end tag.
        """
        suite_attrs = {"created": strformat.strtime(self.starttime),
                       "name": "LinkChecker",
                       "tests": unicode(len(self.tests)),
                       "errors": unicode(0),
                       "failures": str(len([test for test in self.tests if test.failure])),
                       "skip": unicode(0),
                       }
        self.xml_starttag(u'testsuite', suite_attrs)

        for test in self.tests:
            self.write_test_log(test)

        self.xml_endtag(u"testsuite")
        self.xml_end_output()
        self.close_fileoutput()

        #wait wait, do we want a test suite per page?

        # see https://gist.github.com/Great-Antique/adb2b414110f5d242e57
