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
        t.errors = []

        if not self.has_part("result"):
            t.errors.append("Missing result")
        else:
            t.result = unicode(url_data.result)
            if not url_data.valid:
                t.result_type = "failure"
            else:
                t.result_type = "success"

        if self.has_part('url'):
            t.url = unicode(url_data.base_url)
        else:
            t.errors.append("Missing url")
            t.url = None

        if self.has_part("realurl"):
            t.real_url = unicode(url_data.url)

        if url_data.name and self.has_part('name'):
            t.name = unicode(url_data.name)
        else:
            t.name = t.url

        if url_data.parent_url and self.has_part('parenturl'):
            t.parent_url = unicode(url_data.parent_url)
            t.line = unicode(url_data.line)
            t.column = unicode(url_data.column)
        else:
            t.parent_url = "No parent URL?"
            t.line = False
            t.column = False

        if url_data.checktime and self.has_part("checktime"):
            t.time = u"%f" % url_data.checktime

        if t.errors:
            t.result_type = "error"

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
                           "errors": str(len([test for test in tests if test.result == "error"])),
                           "failures": str(len([test for test in tests if test.result == "failure"])),
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
        if test.errors:
            tag = u'error'
        elif test.result_type == "failure":
            tag = u'failure'
        else:
            return

        if test.errors:
            content = "Error creating xUnit output: "
            content += ", ".join(test.errors)
        else:
            message = "{0.result} when requesting {0.name} [{0.real_url}] from {0.parent_url}".format(test)
            content = "{0.result} when requesting {0.name} [{0.real_url}] from {0.parent_url}".format(test)
            if test.line and test.column:
                content += " at source line {0.line}, column {0.column}".format(test)

        testcase_attrs = {}
        testcase_attrs[u'name'] = test.name

        tag_attrs = {}
        if not test.errors:
            tag_attrs[u'message'] = message

        self.xml_starttag(u'testcase', attrs=testcase_attrs)

        self.xml_tag(tag, content, attrs=tag_attrs)

        self.xml_endtag(u'testcase')
        self.flush()

    def end_output_for_one_suite(self, **kwargs):
        """
        Write XML end tag.
        """
        suite_attrs = {"created": strformat.strtime(self.starttime),
                       "name": "LinkChecker",
                       "tests": unicode(len(self.tests)),
                       "errors": str(len([test for test in self.tests if test.result_type == "error"])),
                       "failures": str(len([test for test in self.tests if test.result_type == "failure"])),
                       "skip": unicode(0),
                       }

        self.xml_starttag(u'testsuite', suite_attrs)

        for test in self.tests:
            self.write_test_log(test)

        self.xml_endtag(u"testsuite")
        self.xml_end_output()
        self.close_fileoutput()

        # wait wait, do we want a test suite per page?

        # see https://gist.github.com/Great-Antique/adb2b414110f5d242e57