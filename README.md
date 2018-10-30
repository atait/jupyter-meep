## My notes on installation
The ones [here](http://localhost:8000/Installation/) are not complete for Mac OSX. Some of the brew targets have been renamed

```bash
Wrong: brew install homebrew/science/hdf5 homebrew/science/openblas guile fftw h5utils
Right: brew install hdf5 openblas guile fftw h5utils
```

Then you have to get libctl and harminv. Download zips of them from github. Next is says to run
```bash
./configure && make && make install
```

*however*, you must first run this command

```bash
source autogen.sh
```

Now meep is a little different. You have to do
```bash
./autogen.sh --enable-maintainer-mode --enable-shared --prefix=/usr/local
make && make install
```
I don't know why. Ask [this guy](https://darkalexwang.github.io/2016/10/06/python-meep-install-mac/).

### MPB
Ok it seems there are actually bugs in the code where maxwell_eps.c is trying to get `NQUAD` from sphere-quad.h, but that h-file is empty. Strangely it is in the gitignore