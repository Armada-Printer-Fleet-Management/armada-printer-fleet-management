# Server testing guide

This document sets the standard that everyone, humans and agents, should follow when implementing tests for the application server.

It does not let an agent decide which tests to write.  Before writing tests for a feature change, an agent asks
the developer which ones to write, as described under "The developer chooses the tests" in `.integrity/POLICY.md`, and uses this document to work out what to suggest.  If
the developer's choices leave a gap against this document, the agent points it out and does not fill it unasked.

Paths and commands in this document are relative to `apps/server/` unless they say otherwise.  Picture: `docs/testing.html`.

## Definitions

There are three sizes of tests: unit, integration and end-to-end (e2e).  This section describes the purpose and scope of each size of test.
It is also a high-level overview, with more details provided in subsequent sections, so be sure to read it all.

### Unit tests

Unit tests are the most fundamental type of test.  Their purpose is to give the most coverage while being the fastest and least flaky.
The scope of a unit test is defined as all code that runs within a single process.  This means that if the function under test calls another function
that also runs within the same process, then the called function should not be mocked.  Examples of separate processes are the FastAPI application,
the database and the file store.  If the function under test would run code in another process, then the behaviour of that other process must be mocked.

### Integration tests

Integration tests focus on what unit tests cannot see: real dependencies and the wiring between them.  Their purpose is to validate that the interactions
between processes act as expected.  They are expected to be slower than unit tests, but should remain just as reliable.  The scope of an integration test is
defined as all code that runs within a single system.  In simple terms, any dependency the server has that is also managed by us (i.e. runs within the
dev/deploy stack) should not be mocked.  A dependency outside the dev/deploy stack has to be mocked at its port.  Integration tests focus on one endpoint or
infrastructure adapter at a time.  Following a user across several steps is left to e2e tests.

### End-to-end tests

End-to-end (e2e) tests act as the final sign-off that the system works as expected.  Their purpose is to replicate user behaviour and user flow against
a deployed server that is as prod-like as possible.  They will most likely be much slower than integration tests, and will inevitably have some
amount of flakiness.  The scope of an e2e test is everything.  Nothing is mocked in an e2e test.  The key difference for e2e tests is that their goal
is not immaculate coverage.  Because of their size and flakiness, e2e tests should be written deliberately to cover the key user flows that we need to ensure
work as expected.

## Test layout

| Path | Holds |
| --- | --- |
| `tests/unit/` | Unit tests, including tests of the code's structure and generated documentation.  These never need Docker |
| `tests/integration/` | Integration tests.  These always need Docker |
| `tests/integration/contract/` | What every adapter of a port must do.  One suite runs against each adapter, whether a fake or the real one.  A new adapter joins by adding its factory to `ADAPTERS` |
| `tests/fakes.py` | Fakes shared between tests |
| `e2e/` | End-to-end tests |

Test files are named `test_<what they cover>.py`.

Fixtures go in the `conftest.py` of the narrowest folder that covers the tests likely to use them, so that they can be found and are not duplicated.  A fixture stays in
a test file only if it is very specific to that file.  When a `conftest.py` grows too large to scan easily, move its fixtures into a `fixtures/` folder.

Autouse fixtures can affect a test without anything in the test showing it, so use one only when every test in its scope needs it.  Otherwise, name the fixture on the
tests that need it with `@pytest.mark.usefixtures`.  An autouse fixture goes in the test file if only that file needs it, and otherwise in the closest `conftest.py`,
never in a `fixtures/` folder.  It carries a comment saying why it is automatic.  `pytest --setup-show` lists every fixture that ran for a test.

Refer to seeded data through the constants in `api/infrastructure/dev_data.py`, never by repeating a literal ID.  A test that needs data the seed does not have creates
it itself.  All test data is made up.  Never use real names, email addresses, organisations or files, even when reproducing a bug found with real data.  Describe the shape
of that data in the test instead, and use `example.com` for email addresses.

Tests follow the same code standards as the rest of the server, including `pyright --strict` and `ruff`.

## Test suite setup

This section goes into detail about how each test suite should run.  In CI, the unit and integration tests run separately, while also taking coverage metrics.
Coverage is reported, and does not fail the build.

### Unit tests

All process behaviour outside of the application server is mocked, so these tests need nothing else running.  Run them with
`uv run --directory apps/server pytest tests/unit`.

### Integration tests

Integration tests cover all behaviour within a system, and run with the same single `pytest` command as the unit tests.  Run them alone with
`uv run --directory apps/server pytest tests/integration`, or with the unit tests using `uv run --directory apps/server pytest`.  A session fixture starts the
dependencies in Docker when the suite begins and stops them when it ends, so that nothing is left running.  They run as their own stack, fully separate from the dev
stack, defined in `infra/test/compose.yaml` at the repository root, so that neither influences the other.  If Docker is not available the tests fail rather than skip, so that a passing result always means they ran.

The dependencies are seeded from `api/infrastructure/dev_data.py`.  Data that only tests need, such as additional types of test user, is added on top of it from
test code and never added to `dev_data.py`.

Before each test, the data is reset so that no test can contaminate another: database tables are truncated and reseeded, keeping the migrations in place, and the
file store's objects are deleted.  Do not rebuild the database or rerun migrations between tests.

Contract tests are the one exception to starting from seeded data.  A contract describes what an adapter does from a known state, and every adapter under it must start the same way,
so a SQL adapter's factory uses the `empty_database` fixture, which removes the seed after the reset.

### End-to-end tests

E2e tests simulate real user behaviour against a real running hosted server.  The exact target is still to be decided, but it should be as prod-like as possible.
It will not be production, where at most health checks would run.  At runtime, the test suite is given the target system's URL, as well as the
values of any test data that it should expect the target to have.  It then runs its tests against the target, as if it were a real user.

## Coverage

This section goes into detail about what sort of coverage each test suite should focus on.

### Unit tests

Unit tests should be the main vector for getting complete coverage on the system.  Because they are fast and reliable, one does not need to be too afraid
of overdoing it when it comes to writing unit tests.  Unit tests should attempt to cover all equivalence classes and boundaries, and verify that the output is what is
expected.  What unit tests should not do, however, is test how the function under test produces the result.  This means tests should not assert that the function
under test called certain other functions a certain number of times.  A test only cares that "with input X, it returns output Y".  Asserting on the specific
behaviour of a function usually does not provide any useful information, and can make a test brittle.  Tests on the internal behaviour of a function should be written
deliberately and sparingly.  An example of a valid behaviour test is checking that a cache stops the cached function from being called multiple times.

Additionally, unit tests, while they can span the whole process, should keep their target coverage concise.  The target of any unit test should be to verify
the behaviour of a target function, rather than a whole string of functions.

Every response an endpoint can return is covered by at least one unit test, so an endpoint's full set of responses can be read in one place.  Each distinct code
and meaning counts separately, so "job not found" and "file not found" are two responses even though both use the same code.  For these tests the RPC handler or
REST route is the target function, and only its dependencies at their ports are mocked.  Rule combinations are covered by tests on the entity or service, not
repeated at the endpoint.

### Integration tests

Integration tests cover what unit tests cannot see, using far fewer tests.  They often take a lot longer to run than a unit test, so a test belongs here only if it
could fail while every unit test passes.  Integration tests should focus on two realms of coverage:

- **Infrastructure adapters:** each adapter keeps its port's promises against the real dependency, including how it reports failures.  Run the contract tests in
  `tests/integration/contract/` against it, and add tests only for behaviour specific to that adapter.
- **Endpoints:** enter through the RPC or REST endpoint and check the response.  Cover the happy path and key failure cases.  A failure is key if it depends on real
  stored state, depends on more than one dependency agreeing, or would do real harm if answered wrongly.  Failures decided purely in-process stay in unit tests.

### End-to-end tests

E2e tests should only focus on mimicking key user flows.  The reasoning behind any e2e test should start with "as a user, I want to do this, then this, and so on".
E2e tests should not focus on testing every possible response type from each endpoint, as that is covered by unit tests.  Instead, e2e tests are there to validate
that generally everything is working as expected, including that all the production-level configuration works as we expect it to.

### Bug fixes

A bug fix comes with a test that fails without the fix, so that the bug cannot quietly return.  Write it at the smallest size that can catch the bug, which is usually a
unit test.  If only a larger test can catch it, that also shows which kind of test was missing.

## Mocking

This section explains how mocking should be handled.

### Unit tests

As mentioned in the definitions, a unit test's scope spans a single process.  This definition should be kept close, as it is slightly different from the typical
definition of a unit test.  Because the scope spans the entire process, unit tests do not need to mock any functions that the function under test calls, as long as
those functions do not call any dependency outside the process.  This is encouraged, as it is always better to test the real code than to liberally create mocks.
It gives larger coverage with fewer tests, and reduces the brittleness of tests that break because the production code changed and drifted away from the mocked
behaviour.

Mocking should be done at the port closest to the process boundary, so that as much real in-process code runs as possible.  For example, the file store is mocked
at its plugin port, which keeps the adapter over it real, while a SQL adapter has no port beneath it and so is replaced at the domain's repository port.

There are three forms of mocking.  Use the first one that fits:

1. **Fakes:** a working, simplified implementation of a port, used for larger and more complex dependencies.  If a port has a fake, use it.  Every fake must pass its
   port's contract tests, which any real adapter of that port also passes, so that it cannot drift from production behaviour.
2. **Stubs:** return a simple canned response, for simple scenarios that have no fake.
3. **Mocks:** like stubs, but they also assert on how they were called.  Use them only when that behaviour is itself what's being tested, as described under Coverage.

If a stub or mock may be needed in numerous tests, it is preferred to make it a fixture.

Some things are not separate processes but still need care in a unit test:

- **Time:** unit tests never use a real sleep.  Control time as described under Reliability.
- **Filesystem:** a real temporary directory is fine, since it is fast and isolated to the test.
- **Environment variables and global state:** these may be changed, as long as a fixture restores them after the test.  `monkeypatch` does this for environment variables.
- **Network:** any real network connection is a separate process, even to localhost, so it is mocked.

### Integration tests

Any dependency run by the dev/deploy stack is real in integration tests.  A dependency outside the stack is mocked at its port, following the same procedure as
unit tests.

### End-to-end tests

Nothing should be mocked.

## Reliability

Every test must pass alone and in any order, and must not depend on what an earlier test left behind.

Control time by passing a fixed `clock` to the code under test, rather than reading the real time.

Async tests are plain `async def` functions run by `pytest-asyncio`, never by calling `asyncio.run`.

Anything tied to an event loop, such as a database engine, is only used on the loop that created it.  `TestClient` runs the application on its own loop, so always use it
as `with TestClient(app)`, which keeps one loop for all of its requests and runs the lifespan.  Let the lifespan create what the application needs, rather than sharing it
from the test.  `TestClient` is synchronous, so tests using it are plain `def` functions, since calling it from an `async def` test blocks that test's own loop.

An integration test waiting on a real dependency polls for the expected result with a timeout, rather than sleeping for a fixed time.  A fixed sleep is either slow or
flaky, and often both.

A flaky unit or integration test is a bug.  It is fixed, or removed with a ticket to replace it, and is never retried automatically, because even a single failure is
something we want to know about.
