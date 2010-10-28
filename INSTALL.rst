INSTALL
=======

There's a bundled ``install.sh`` file which will setup a virtualenv for you and
install mscrap there, that's the easiest choice. You should use it like this::

    ./install.sh /path/where/to/setup/your/virtualenv

**Don't worry**, nothing will be installed outside that directory, so you can
simply remove that and everything will be clean again.

Otherwise, you could check what the ``install.sh`` file does and do it by hand,
it quite easy.

You need to have installed:

- python2 (>2.6)
- pip
- virtualenv
- make and those things one needs to compile stuff (needed for libxml2)

