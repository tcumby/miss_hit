#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2019-2020, Florian Schanda                    ##
##                                                                          ##
##  This file is part of MISS_HIT.                                          ##
##                                                                          ##
##  MATLAB Independent, Small & Safe, High Integrity Tools (MISS_HIT) is    ##
##  free software: you can redistribute it and/or modify it under the       ##
##  terms of the GNU General Public License as published by the Free        ##
##  Software Foundation, either version 3 of the License, or (at your       ##
##  option) any later version.                                              ##
##                                                                          ##
##  MISS_HIT is distributed in the hope that it will be useful,             ##
##  but WITHOUT ANY WARRANTY; without even the implied warranty of          ##
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           ##
##  GNU General Public License for more details.                            ##
##                                                                          ##
##  You should have received a copy of the GNU General Public License       ##
##  along with MISS_HIT. If not, see <http://www.gnu.org/licenses/>.        ##
##                                                                          ##
##############################################################################

# Main test driver

import os
import sys
import copy
import subprocess
import multiprocessing
import argparse

TEST_ROOT = os.getcwd()
MH_ROOT = os.path.normpath(os.path.join(TEST_ROOT, ".."))
TEST_ENV = copy.copy(os.environ)
TEST_ENV["PYTHONIOENCODING"] = "UTF-8"
TEST_ENV["PYTHONPATH"] = MH_ROOT


def execute_style_test(name):
    os.chdir(os.path.join(TEST_ROOT,
                          "style",
                          name))

    m_files = []
    slx_files = []
    for path, _, files in os.walk("."):
        for f in files:
            if f.endswith(".m"):
                m_files.append(os.path.join(path, f))
            elif f.endswith(".slx"):
                slx_files.append(os.path.join(path, f))

    # Take a copy of the original file
    orig = {}
    fixed = {}
    for f in m_files + slx_files:
        with open(f, "rb") as fd:
            orig[f] = fd.read()

    # Run in HTML mode
    r = subprocess.run(["coverage",
                        "run",
                        "--rcfile=%s" % os.path.join(TEST_ROOT,
                                                     "coverage.cfg"),
                        "--append",
                        "../../../mh_style",
                        ".",
                        "--single",
                        "--process-slx",
                        "--html=expected_out.html"],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8",
                       env=TEST_ENV)
    html_out = r.stdout

    # Run in plaintext mode and fix
    r = subprocess.run(["coverage",
                        "run",
                        "--rcfile=%s" % os.path.join(TEST_ROOT,
                                                     "coverage.cfg"),
                        "--append",
                        "../../../mh_style",
                        "--debug-validate-links",
                        ".",
                        "--single",
                        "--process-slx",
                        "--fix"],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8",
                       env=TEST_ENV)
    plain_out = r.stdout

    # Write the fixed file to foo.m_fixed
    for f in m_files + slx_files:
        with open(f, "rb") as fd:
            fixed[f] = fd.read()
        with open(f + "_fixed", "wb") as fd:
            fd.write(fixed[f])

    # Run in plaintext mode, again, to see if more things need fixing
    r = subprocess.run(["coverage",
                        "run",
                        "--rcfile=%s" % os.path.join(TEST_ROOT,
                                                     "coverage.cfg"),
                        "--append",
                        "../../../mh_style",
                        ".",
                        "--single",
                        "--process-slx",
                        "--fix"],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8",
                       env=TEST_ENV)
    plain_out_again = r.stdout

    # Check if fixed files not "fixed" again
    broken_fixes = set()
    for f in m_files + slx_files:
        with open(f, "rb") as fd:
            tmp = fd.read()
        if tmp != fixed[f]:
            broken_fixes.add(f)

    # Restore original output
    for f in m_files + slx_files:
        with open(f, "wb") as fd:
            fd.write(orig[f])

    # Save stdout
    with open("expected_out.txt", "w") as fd:
        fd.write("=== PLAIN MODE ===\n")
        fd.write(plain_out)
        fd.write("\n")
        fd.write("=== HTML MODE ===\n")
        fd.write(html_out)
        if broken_fixes:
            fd.write("\n")
            fd.write("=== ! BROKEN FIXES ! ===\n")
            for fail in sorted(broken_fixes):
                fd.write("Fixing is not idempotent for %s\n" % fail)

    os.rename(".coverage", os.path.join(TEST_ROOT,
                                        ".".join([".coverage",
                                                  "style",
                                                  name])))

    return "Ran style test %s" % name


def execute_metric_test(name):
    os.chdir(os.path.join(TEST_ROOT,
                          "metrics",
                          name))

    # Run
    r = subprocess.run(["coverage",
                        "run",
                        "--rcfile=%s" % os.path.join(TEST_ROOT,
                                                     "coverage.cfg"),
                        "--append",
                        "../../../mh_metric",
                        "--single",
                        ".",],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8",
                       env=TEST_ENV)
    plain_out = r.stdout

    # HTML
    r = subprocess.run(["coverage",
                        "run",
                        "--rcfile=%s" % os.path.join(TEST_ROOT,
                                                     "coverage.cfg"),
                        "--append",
                        "../../../mh_metric",
                        "--single",
                        "--html=metrics.html",
                        ".",],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8",
                       env=TEST_ENV)
    html_out = r.stdout

    # JSON
    r = subprocess.run(["coverage",
                        "run",
                        "--rcfile=%s" % os.path.join(TEST_ROOT,
                                                     "coverage.cfg"),
                        "--append",
                        "../../../mh_metric",
                        "--single",
                        "--json=metrics.json",
                        ".",],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8",
                       env=TEST_ENV)
    json_out = r.stdout

    # Save stdout
    with open("expected_out.txt", "w") as fd:
        fd.write("=== PLAIN MODE ===\n")
        fd.write(plain_out)

        fd.write("\n\n=== HTML MODE ===\n")
        fd.write(html_out)

        fd.write("\n\n=== JSON MODE ===\n")
        fd.write(json_out)

    os.rename(".coverage", os.path.join(TEST_ROOT,
                                        ".".join([".coverage",
                                                  "metrics",
                                                  name])))

    return "Ran metrics test %s" % name


def execute_lint_test(name):
    os.chdir(os.path.join(TEST_ROOT,
                          "lint",
                          name))

    # Run
    r = subprocess.run(["coverage",
                        "run",
                        "--rcfile=%s" % os.path.join(TEST_ROOT,
                                                     "coverage.cfg"),
                        "--append",
                        "../../../mh_lint",
                        "--single",
                        ".",],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8",
                       env=TEST_ENV)
    plain_out = r.stdout

    # # HTML
    # r = subprocess.run([sys.executable,
    #                     "../../../mh_lint",
    #                     "--single",
    #                     "--html=lint.html",
    #                     ".",],
    #                    stdout=subprocess.PIPE,
    #                    stderr=subprocess.STDOUT,
    #                    encoding="utf-8",
    #                    env=TEST_ENV)
    # html_out = r.stdout

    # Save stdout
    with open("expected_out.txt", "w") as fd:
        fd.write("=== PLAIN MODE ===\n")
        fd.write(plain_out)

        # fd.write("\n\n=== HTML MODE ===\n")
        # fd.write(html_out)

    os.rename(".coverage", os.path.join(TEST_ROOT,
                                        ".".join([".coverage",
                                                  "lint",
                                                  name])))

    return "Ran lint test %s" % name


def execute_lexer_test(name):
    os.chdir(os.path.join(TEST_ROOT,
                          "lexer",
                          name))

    files = [f
             for f in os.listdir(".")
             if f.endswith(".m")]

    for f in files:
        r = subprocess.run(["coverage",
                            "run",
                            "--rcfile=%s" % os.path.join(TEST_ROOT,
                                                         "coverage.cfg"),
                            "--append",
                            "-m",
                            "miss_hit_core.m_lexer",
                            f],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,

                           encoding="utf-8",
                           env=TEST_ENV)
        plain_out = r.stdout

        with open(f + ".out", "w") as fd:
            fd.write(plain_out)

    os.rename(".coverage", os.path.join(TEST_ROOT,
                                        ".".join([".coverage",
                                                  "lexer",
                                                  name])))

    return "Ran lexer test %s" % name


def execute_parser_test(name):
    os.chdir(os.path.join(TEST_ROOT,
                          "parser",
                          name))

    files = [f
             for f in os.listdir(".")
             if f.endswith(".m")]

    for f in files:
        r = subprocess.run(["coverage",
                            "run",
                            "--rcfile=%s" % os.path.join(TEST_ROOT,
                                                         "coverage.cfg"),
                            "--append",
                            "../../../mh_debug_parser",
                            "--no-tb",
                            "--tree",
                            f],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           encoding="utf-8",
                           env=TEST_ENV)
        plain_out = r.stdout

        with open(f + ".out", "w") as fd:
            fd.write(plain_out)

    os.rename(".coverage", os.path.join(TEST_ROOT,
                                        ".".join([".coverage",
                                                  "parser",
                                                  name])))

    return "Ran parser test %s" % name


def execute_simulink_parser_test(name):
    os.chdir(os.path.join(TEST_ROOT,
                          "simulink_parser",
                          name))

    files = [f
             for f in os.listdir(".")
             if f.endswith(".slx")]

    for f in files:
        r = subprocess.run(["coverage",
                            "run",
                            "--rcfile=%s" % os.path.join(TEST_ROOT,
                                                         "coverage.cfg"),
                            "--append",
                            "-m",
                            "miss_hit_core.s_parser",
                            f],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           encoding="utf-8",
                           env=TEST_ENV)
        plain_out = r.stdout

        with open(f + ".out", "w") as fd:
            fd.write(plain_out)

    if files:
        os.rename(".coverage", os.path.join(TEST_ROOT,
                                            ".".join([".coverage",
                                                      "simulink_parser",
                                                      name])))

    return "Ran simulink parser test %s" % name


def execute_config_parser_test(name):
    os.chdir(os.path.join(TEST_ROOT,
                          "config_parser",
                          name))

    files = [f
             for f in os.listdir(".")
             if f.endswith(".cfg")]

    for f in files:
        r = subprocess.run(["coverage",
                            "run",
                            "--rcfile=%s" % os.path.join(TEST_ROOT,
                                                         "coverage.cfg"),
                            "--append",
                            "-m",
                            "miss_hit_core.cfg_parser",
                            "--no-tb",
                            f],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           encoding="utf-8",
                           env=TEST_ENV)
        plain_out = r.stdout

        with open(f + ".out", "w") as fd:
            fd.write(plain_out)

    os.rename(".coverage", os.path.join(TEST_ROOT,
                                        ".".join([".coverage",
                                                  "config_parser",
                                                  name])))

    return "Ran config parser test %s" % name


def execute_sanity_test(name):
    os.chdir(os.path.join(TEST_ROOT,
                          "sanity",
                          name))

    if os.path.isfile(os.path.join(MH_ROOT, "miss_hit_core", name + ".py")):
        module = "miss_hit_core"
    elif os.path.isfile(os.path.join(MH_ROOT, "miss_hit", name + ".py")):
        module = "miss_hit"
    else:
        return "FAILED sanity test %s (cannot find module)" % name

    r = subprocess.run(["coverage",
                        "run",
                        "--rcfile=%s" % os.path.join(TEST_ROOT,
                                                     "coverage.cfg"),
                        "--append",
                        "-m",
                        "%s.%s" % (module, name)],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8",
                       env=TEST_ENV)
    plain_out = r.stdout

    with open("%s.out" % name, "w") as fd:
        fd.write(plain_out.rstrip() + "\n")

    os.rename(".coverage", os.path.join(TEST_ROOT,
                                        ".".join([".coverage",
                                                  "sanity",
                                                  name])))

    return "Ran sanity test %s" % name


def run_test(test):
    if os.path.exists(os.path.join(TEST_ROOT,
                                   test["kind"],
                                   test["test"],
                                   "ONLY_LINUX")):
        if sys.platform != "linux":
            return "SKIPPED linux-only test %s" % test["test"]

    fn = {
        "style"           : execute_style_test,
        "metrics"         : execute_metric_test,
        "lint"            : execute_lint_test,
        "lexer"           : execute_lexer_test,
        "parser"          : execute_parser_test,
        "simulink_parser" : execute_simulink_parser_test,
        "config_parser"   : execute_config_parser_test,
        "sanity"          : execute_sanity_test,
    }
    return fn[test["kind"]](test["test"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--single",
                    action="store_true",
                    default=False)
    ap.add_argument("--suite",
                    default=None)
    ap.add_argument("--no-summary",
                    default=False,
                    action="store_true")

    options = ap.parse_args()

    # Make sure we're in the right directory
    assert os.path.isfile("../mh_style")
    assert os.path.isdir("../miss_hit_core")
    root = os.getcwd()

    tests = []

    if options.suite:
        suites = [options.suite]
    else:
        suites = ["lexer", "parser", "simulink_parser",
                  "config_parser",
                  "style", "metrics", "lint",
                  "sanity"]

    for kind in suites:
        for t in os.listdir(kind):
            tests.append({"kind" : kind,
                          "test" : t})

    os.system("coverage erase")

    if options.single:
        for t in tests:
            print("Running %s" % t)
            print(run_test(t))
    else:
        pool = multiprocessing.Pool()
        for res in pool.imap_unordered(run_test, tests, 2):
            print(res)

    os.chdir(TEST_ROOT)
    os.system("coverage combine")

    if not options.no_summary:
        os.system("coverage html --rcfile=coverage.cfg")
        os.system("coverage report --rcfile=coverage.cfg")


if __name__ == "__main__":
    main()
