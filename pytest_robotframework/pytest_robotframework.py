from __future__ import annotations

from typing import TYPE_CHECKING, cast

from deepmerge import always_merger
from robot.api import SuiteVisitor
from robot.libraries.BuiltIn import BuiltIn
from robot.output import LOGGER
from robot.run import RobotFramework
from typing_extensions import override

from pytest_robotframework import _resources, _suite_variables, import_resource
from pytest_robotframework._common import (
    KeywordNameFixer,
    PytestRuntestLogListener,
    PytestRuntestProtocolInjector,
    RobotArgs,
    parse_robot_args,
)
from pytest_robotframework._python import PythonParser
from pytest_robotframework._robot import (
    CollectedTestsFilterer,
    RobotFile,
    RobotItem,
    collected_robot_suite_key,
)

if TYPE_CHECKING:
    from pathlib import Path

    from pytest import Collector, Item, Parser, Session
    from robot import model


def pytest_addoption(parser: Parser):
    parser.addoption(
        "--robotargs",
        default="",
        help="additional arguments to be passed to robotframework",
    )


def pytest_collection(session: Session):
    collected_suite: model.TestSuite | None = None

    class RobotTestCollector(SuiteVisitor):
        @override
        def visit_suite(self, suite: model.TestSuite):
            nonlocal collected_suite
            # copy the suite since we want to remove everything from it to prevent robot from running anything
            # but still want to preserve them in `collected_suite`
            collected_suite = suite.deepcopy()  # type:ignore[no-untyped-call]
            suite.suites.clear()  # type:ignore[no-untyped-call]
            suite.tests.clear()  # type:ignore[no-untyped-call]

    robot = RobotFramework()  # type:ignore[no-untyped-call]
    robot.main(  # type:ignore[no-untyped-call]
        [session.path],  # type:ignore[no-any-expr]
        extension="py:robot",
        runemptysuite=True,
        console="none",
        report=None,
        output=None,
        log=None,
        # the python parser is not actually used here, but required because collection needs to be run with the
        # same settings as the actual run, otherwise test longnames could be different (see the TODO in
        # get_item_from_robot_test)
        parser=[PythonParser(session)],  # type:ignore[no-any-expr]
        prerunmodifier=[RobotTestCollector()],  # type:ignore[no-any-expr]
    )
    if not collected_suite:
        raise Exception("failed to collect .robot tests")
    session.stash[collected_robot_suite_key] = collected_suite


def pytest_collect_file(parent: Collector, file_path: Path) -> Collector | None:
    if file_path.suffix == ".robot":
        return RobotFile.from_parent(  # type:ignore[no-untyped-call,no-any-expr,no-any-return]
            parent, path=file_path
        )
    return None


def pytest_runtest_setup(item: Item):
    if isinstance(item, RobotItem):
        # `set_variables` and `import_resource` is only supported in python files.
        # when running robot files, suite variables should be set using the `*** Variables ***` section
        # and resources should be imported with `Resource` in the `*** Settings***` section
        return
    builtin = BuiltIn()
    for key, value in _suite_variables[item.path].items():
        builtin.set_suite_variable(r"${" + key + "}", value)
    for resource in _resources:
        import_resource(resource)


def pytest_runtestloop(session: Session) -> object:
    if session.config.option.collectonly:  # type:ignore[no-any-expr]
        return None
    # needed for log_file listener methods to prevent logger from deactivating after the test is over
    with LOGGER:
        robot = RobotFramework()  # type:ignore[no-untyped-call]
        robot.main(  # type:ignore[no-untyped-call]
            [session.path],  # type:ignore[no-any-expr]
            extension="py:robot",
            # needed because PythonParser.visit_init creates an empty suite
            runemptysuite=True,
            **cast(
                RobotArgs,
                always_merger.merge(  # type:ignore[no-untyped-call]
                    parse_robot_args(robot, session),
                    dict[str, object](
                        parser=[PythonParser(session)],
                        prerunmodifier=[
                            CollectedTestsFilterer(session),
                            PytestRuntestProtocolInjector(session),
                        ],
                        prerebotmodifier=[KeywordNameFixer()],
                        listener=[PytestRuntestLogListener(session)],
                    ),
                ),
            ),
        )
    return True
