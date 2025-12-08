setup:
    #!/usr/bin/env sh
    python -m venv venv
    source venv/bin/activate
    python -m pip install -r requirements.txt

clean:
    rm -r -f dist

build: setup clean
    #!/usr/bin/env sh
    source venv/bin/activate
    python -m build

install: build
    python -m pip install --force-reinstall ./dist/*.whl

test test_case="":
    python -m unittest discover -s src
