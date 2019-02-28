# atait, some things to make MEEP nicer
Mostly, this is about using MEEP in jupyter notebooks.

## Liveplot in notebooks
This is important because you get real time feedback on how the simulation is going. Lumerical can't do that.

## Importing PHIDL Devices and gds files

## Converting simulations to gifs
`to_gif`. You must have imagemagik installed. Usage:
```
shutil.rmtree('outputs', ignore_errors=True)
sim.use_output_directory('outputs')
sim.run(
        mp.at_beginning(livefield),    # Optional, if you want to see live plots
        mp.at_every(5, livefield),     # Optional, if you want to see live plots
        mp.at_every(1, mp.output_png(mp.Ez, "-Zc dkbluered")),         # Need this line to export the pngs
        mp.to_appended('ez', mp.at_every(0.6, mp.output_efield_z)),    # Need this line to export the pngs
        until=until)
to_gif('outputs', 'ez')
```

## Notes on installing MEEP and MPB
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

Alright! The autogen options also solved the problem with MPB.

For python version, MPB goes within MEEP. You must reconfigure and re-install MEEP after installing MPB