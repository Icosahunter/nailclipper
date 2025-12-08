setup:
    #!/usr/bin/env sh
    python3 -m venv venv
    source venv/bin/activate
    python3 -m pip install -r requirements.txt

clean:
    rm -r -f dist

build: setup clean
    #!/usr/bin/env sh
    source venv/bin/activate
    python3 -m build

install: build
    python3 -m pip install --force-reinstall ./dist/*.whl

test test_case="": install
    #!/usr/bin/env sh
    python3 -m nailclipper.tests.main
