#!/bin/bash

# U CAN TOUCH THIS

PYTHON_BIN="`which python2`" # python < 2.6 may not work D:
VIRTUALENV_BIN="`which virtualenv`"
PIP_BIN="`which pip`"
LIBXML2_VER="2.7.3" # <-- will be installed inside the virtualenv

[[ -z "$PYTHON_BIN" ]] && die "Python missing."
[[ -z "$VIRTUALENV_BIN" ]] && die "virtualenv missing."
[[ -z "$PIP_BIN" ]] && die "pip missing."



# U CANT TOUCH THIS

[[ `id -u` == 0 ]] && die "You are root, not nice!"

trap "exit 1;" TERM INT

function die() {
    echo "Error! $1" > /dev/stderr
    exit 1;
}

HERE_PATH="`dirname $0`"
DEST_PATH="$1"

[[ -z "$DEST_PATH" ]] && die "You need to give me a path for you new virtualenv"
[[ -e "$DEST_PATH" ]] && die "There's something in $1, remove it"

echo "Installing all in $DEST_PATH"
echo "Don't worry, won't touch stuff outside that dir."
echo "Starting in 3 seconds..."
sleep 3
echo "OK GO!"

mkdir -p "$DEST_PATH" || die "Can't write to $DEST_PATH"


# Setup & start virtualenv
$VIRTUALENV_BIN --python="$PYTHON_BIN" --distribute "$DEST_PATH" || die
source "$DEST_PATH/bin/activate"

# Install libxml2
TMPDIR=`mktemp -d --suffix=".libxml2-${LIBXML2_VER}"`
mkdir -p "$TMPDIR" || die "Can't write to $TMPDIR"
pushd $TMPDIR
echo "Building libxml2-${LIBXML2_VER} in $PWD"
wget ftp://ftp.xmlsoft.org/libxml2/libxml2-${LIBXML2_VER}.tar.gz
tar xzf libxml2-${LIBXML2_VER}.tar.gz
cd libxml2-${LIBXML2_VER}
./configure --prefix="$VIRTUAL_ENV" \
            --with-threads \
            --with-history \
            --with-python="$VIRTUAL_ENV/bin/python" || die "configure failed"
make -j2 || die "make failed"
make install
popd

# we do this instead of "pip install -r pip-requirements.txt" cuz the order in
# which the packages are installed is important, and pip seems to ignore it.
for dep in `grep -e "^\w" "$HERE_PATH/pip-requirements.txt"`; do
    $PIP_BIN install -E "$VIRTUAL_ENV" "$dep"
done

echo "Done! Your virtualenv and stuff is ready at $VIRTUAL_ENV"
exit 0
