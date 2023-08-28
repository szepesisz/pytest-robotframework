from __future__ import annotations

import os
from pathlib import Path

from pytest import mark

from tests.utils import (
    PytesterDir,
    assert_log_file_exists,
    assert_robot_total_stats,
    output_xml,
    run_and_assert_result,
    run_pytest,
)


def test_one_test_passes(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1)
    assert_log_file_exists(pytester_dir)


def test_one_test_fails(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, failed=1)
    assert_log_file_exists(pytester_dir)


def test_one_test_skipped(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, skipped=1)
    assert_log_file_exists(pytester_dir)
    assert output_xml(pytester_dir).xpath(
        "./suite//test[@name='test_one_test_skipped']/kw[@type='SETUP']/msg[@level='SKIP']"
    )


def test_two_tests_one_fail_one_pass(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1, failed=1)
    assert_log_file_exists(pytester_dir)


def test_two_tests_two_files_one_fail_one_pass(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1, failed=1)
    assert_log_file_exists(pytester_dir)


def test_two_tests_with_same_name_one_fail_one_pass(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1, failed=1)
    assert_log_file_exists(pytester_dir)


def test_suites(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1)
    assert_log_file_exists(pytester_dir)
    assert output_xml(pytester_dir).xpath(
        "./suite/suite[@name='Suite1']/suite[@name='Test"
        " Asdf']/test[@name='test_func1']"
    )


def test_nested_suites(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=2, failed=1)
    assert_log_file_exists(pytester_dir)
    xml = output_xml(pytester_dir)
    assert xml.xpath(
        "./suite/suite[@name='Suite1']/suite[@name='Suite2']/suite[@name='Test"
        " Asdf']/test[@name='test_func1']"
    )
    assert xml.xpath(
        "./suite/suite[@name='Suite1']/suite[@name='Suite3']/suite[@name='Test"
        " Asdf2']/test[@name='test_func2']"
    )
    assert xml.xpath("./suite/suite[@name='Test Top Level']/test[@name='test_func1']")


def test_robot_args(pytester_dir: PytesterDir):
    results_path = pytester_dir.path / "results"
    result = pytester_dir.runpytest("--robotargs", f"-d {results_path}")
    result.assert_outcomes(passed=1)
    assert (results_path / "log.html").exists()


def test_robot_options_variable(pytester_dir: PytesterDir):
    results_path = pytester_dir.path / "results"
    env_variable = "ROBOT_OPTIONS"
    try:
        os.environ[env_variable] = f"-d {results_path}"
        result = pytester_dir.runpytest()
    finally:
        del os.environ[env_variable]
    result.assert_outcomes(passed=1)
    assert (results_path / "log.html").exists()


def test_robot_options_merge_listeners(pytester_dir: PytesterDir):
    result = pytester_dir.runpytest(
        "--robotargs", f"--listener {pytester_dir.path / 'Listener.py'}"
    )
    result.assert_outcomes(passed=1)
    assert_log_file_exists(pytester_dir)


def test_robot_options_variable_merge_listeners(pytester_dir: PytesterDir):
    env_variable = "ROBOT_OPTIONS"
    try:
        os.environ[env_variable] = f"--listener {pytester_dir.path / 'Listener.py'}"
        result = pytester_dir.runpytest()
    finally:
        del os.environ[env_variable]
    result.assert_outcomes(passed=1)
    assert_log_file_exists(pytester_dir)


def test_listener_calls_log_file(pytester_dir: PytesterDir):
    result = pytester_dir.runpytest(
        "--robotargs", f"--listener {pytester_dir.path / 'Listener.py'}"
    )
    result.assert_outcomes(passed=1)
    assert_log_file_exists(pytester_dir)
    assert Path("hi").exists()


def test_doesnt_run_when_collecting(pytester_dir: PytesterDir):
    result = run_pytest(pytester_dir, "--collect-only")
    result.assert_outcomes()
    assert not (pytester_dir.path / "log.html").exists()


def test_correct_items_collected_when_collect_only(pytester_dir: PytesterDir):
    result = run_pytest(pytester_dir, "--collect-only", "test_bar.py")
    assert result.parseoutcomes() == {"test": 1}
    assert "<Function test_func2>" in (line.strip() for line in result.outlines)


def test_setup_passes(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1)
    assert_log_file_exists(pytester_dir)
    xml = output_xml(pytester_dir)
    assert xml.xpath(
        ".//test/kw[contains(@name, ' Setup')]/msg[@level='INFO' and .='2']"
    )
    assert xml.xpath(
        ".//test/kw[contains(@name, ' Run Test')]/msg[@level='INFO' and .='1']"
    )


def test_setup_fails(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, errors=1)
    assert_log_file_exists(pytester_dir)
    xml = output_xml(pytester_dir)
    assert xml.xpath(
        ".//test/kw[contains(@name, ' Setup')]/msg[@level='FAIL' and .='Exception: 2']"
    )
    assert not xml.xpath(".//test/kw[contains(@name, ' Run Test')]")


def test_setup_skipped(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, skipped=1)
    assert_log_file_exists(pytester_dir)
    xml = output_xml(pytester_dir)
    assert xml.xpath(".//test/kw[contains(@name, ' Setup')]/msg[@level='SKIP']")
    assert not xml.xpath(".//test/kw[contains(@name, ' Run Test')]")


def test_teardown_passes(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1)
    assert_log_file_exists(pytester_dir)
    xml = output_xml(pytester_dir)
    assert xml.xpath(
        ".//test/kw[contains(@name, ' Run Test')]/msg[@level='INFO' and .='1']"
    )
    assert xml.xpath(
        ".//test/kw[contains(@name, ' Teardown')]/msg[@level='INFO' and .='2']"
    )


def test_teardown_fails(pytester_dir: PytesterDir):
    result = run_pytest(pytester_dir)
    result.assert_outcomes(passed=1, errors=1)
    # unlike pytest, teardown failures in robot count as a test failure
    assert_robot_total_stats(pytester_dir, failed=1)
    assert_log_file_exists(pytester_dir)
    xml = output_xml(pytester_dir)
    assert xml.xpath(".//test/kw[contains(@name, ' Run Test')]")
    assert xml.xpath(
        ".//test/kw[contains(@name, ' Teardown')]/msg[@level='FAIL' and"
        " .='Exception: 2']"
    )


def test_teardown_skipped(pytester_dir: PytesterDir):
    result = run_pytest(pytester_dir)
    result.assert_outcomes(passed=1, skipped=1)
    # unlike pytest, teardown skips in robot count as a test skip
    assert_robot_total_stats(pytester_dir, skipped=1)
    assert_log_file_exists(pytester_dir)
    xml = output_xml(pytester_dir)
    assert xml.xpath(".//test/kw[contains(@name, ' Run Test')]")
    assert xml.xpath(".//test/kw[contains(@name, ' Teardown')]/msg[@level='SKIP']")


def test_fixture(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1)
    assert_log_file_exists(pytester_dir)


def test_module_docstring(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1)
    assert_log_file_exists(pytester_dir)
    assert output_xml(pytester_dir).xpath("./suite/suite/doc[.='hello???']")


def test_test_case_docstring(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1)
    assert_log_file_exists(pytester_dir)
    assert output_xml(pytester_dir).xpath("./suite/suite/test/doc[.='hello???']")


def test_keyword_decorator(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1)
    assert_log_file_exists(pytester_dir)
    assert output_xml(pytester_dir).xpath(
        ".//kw[contains(@name, ' Run Test')]/kw[@name='foo']/doc[.='hie']"
    )


def test_tags(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1)
    assert_log_file_exists(pytester_dir)
    xml = output_xml(pytester_dir)
    assert xml.xpath(".//test[@name='test_tags']/tag[.='slow']")


def test_parameterized_tags(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1)
    assert_log_file_exists(pytester_dir)
    xml = output_xml(pytester_dir)
    assert xml.xpath(".//test[@name='test_tags']/tag[.='foo:bar']")


@mark.xfail(
    reason=(
        "TODO: figure out how to modify the keyword names before the xml is written or"
        " read the html file instead"
    )
)
def test_keyword_names(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=2)
    assert_log_file_exists(pytester_dir)
    xml = output_xml(pytester_dir)
    for index in range(2):
        assert xml.xpath(f".//test[@name='test_{index}']/kw[@name='Setup']")
        assert xml.xpath(f".//test[@name='test_{index}']/kw[@name='Run Test']")
        assert xml.xpath(f".//test[@name='test_{index}']/kw[@name='Teardown']")


def test_suite_variables(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1)
    assert_log_file_exists(pytester_dir)


def test_variables_list(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1)
    assert_log_file_exists(pytester_dir)


def test_variables_not_in_scope_in_other_suites(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=2)
    assert_log_file_exists(pytester_dir)


def test_parametrize(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1, failed=1)
    assert_log_file_exists(pytester_dir)
    xml = output_xml(pytester_dir)
    assert xml.xpath("//test[@name='test_eval[1-8]']")
    assert xml.xpath("//test[@name='test_eval[6-6]']")


def test_unittest_class(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1)
    assert_log_file_exists(pytester_dir)


def test_robot_keyword_in_python_test(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, passed=1)
    assert_log_file_exists(pytester_dir)


def test_xfail_fails(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, xfailed=1)
    assert_log_file_exists(pytester_dir)
    assert output_xml(pytester_dir).xpath(
        "//kw[contains(@name, ' Run Test') and ./msg[@level='SKIP' and .='xfail:"
        " asdf']]"
    )


def test_xfail_passes(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, failed=1)
    assert_log_file_exists(pytester_dir)
    assert output_xml(pytester_dir).xpath(
        "//kw[contains(@name, ' Run Test') and ./msg[@level='FAIL' and"
        " .='[XPASS(strict)] asdf']]"
    )


def test_xfail_fails_no_reason(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, xfailed=1)
    assert_log_file_exists(pytester_dir)
    assert output_xml(pytester_dir).xpath(
        "//kw[contains(@name, ' Run Test') and ./msg[@level='SKIP' and .='xfail']]"
    )


def test_xfail_passes_no_reason(pytester_dir: PytesterDir):
    run_and_assert_result(pytester_dir, failed=1)
    assert_log_file_exists(pytester_dir)
    assert output_xml(pytester_dir).xpath(
        "//kw[contains(@name, ' Run Test') and ./msg[@level='FAIL' and"
        " .='[XPASS(strict)] ']]"
    )
