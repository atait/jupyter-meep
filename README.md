# Jupyter MEEP
Notebook-based graphics and I/O for MEEP, with examples of specific devices.

Disclaimer: This is not a formally maintained repo, more like a lab notebook. Most of them are illustrations/tutorials of workflows I found useful. Notebooks on the main branch are not guaranteed to work, even if it did the day before. Elements that are reusable such as plotting tools have been extracted into the library modules, which are kind of stable (not guaranteed).

## Features
### Liveplot in notebooks
This is important because you get real time feedback on how the simulation is going. I don't think Lumerical can do that. To use it, wrap `liveplot` with a function that defines the field polarization. For example,
```
def livefield(sim):
    liveplot(sim, mp.Ez)
```
Then in your simulator, do that plot every few timesteps
```
sim.run(
        mp.at_beginning(livefield),
        mp.at_every(5, livefield),
        )
```

### Converting simulations to gifs
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

Then go ahead and embed the gif anywhere

![alt](mmi-example.gif)


### Importing PHIDL Devices and gds files
`device_to_meep` and `gds_to_meep`. You must have phidl installed. See the notebook.


### Save and load formulas
This is done with `lightlab`. You sometimes don't want to resimulate the whole thing if you just want to mess with the plots. If the jupyter kernel reboots, then you will lose all of your simulation data needed to come back to the plot.

The formula in the notebook goes like
```
isResimulating = True
isSaving = True
filename = 'shovel-length.pkl'
if isResimulating:
    spectra = do_thing(param_vals)  # do some kind of simulation involving parameter sweeps or something.
    if isSaving:
        io.savePickleGzip(dataTuple=(param_vals, spectra), filename=filename)
else:
    param_vals, spectra = io.loadPickleGzip(filename=filename)
```
And then in your new cell,
```
spectra.simplePlot()
```

### Sweep multiprocessing
MEEP has some HPC (MPI, GPU) capabilities for large simulations. These are great but do not really provide a benefit for embarrassingly parallel parameter sweeps. The concept: create one process per MEEP simulation, scatter parameters, let the OS schedule processes on the multi-core machine, gather results. Jupyter-MEEP provides a simple interface for orchestrating this strategy (EDIT: _will_ provide. This is planned but not done. Development efforts are sketched out in a notebook).


## Notes on installing MEEP and MPB on OSX
The ones [here](http://localhost:8000/Installation/) are not complete for Mac OSX. Some of the brew targets have been renamed

```bash
Wrong: brew install homebrew/science/hdf5 homebrew/science/openblas guile fftw h5utils
Right: brew install hdf5 openblas guile fftw h5utils
```

Then you have to get libctl and harminv. Download zips of them from github. Next is says to run
```bash
./configure && make && make install
```

*however, if autogen.sh is present in the directory*, you must first run this command

```bash
source autogen.sh
```

Now meep is a little different. You have to do
```bash
./configure --enable-maintainer-mode --enable-shared --prefix=/usr/local
make && make install
```
I don't know why. Ask [this person](https://darkalexwang.github.io/2016/10/06/python-meep-install-mac/).

### MPB
Ok it seems there are actually bugs in the code where maxwell_eps.c is trying to get `NQUAD` from sphere-quad.h, but that h-file is empty. Strangely it is in the gitignore

Alright! The autogen options also solved the problem with MPB.
```bash
./configure --enable-maintainer-mode --enable-shared --prefix=/usr/local
make && make install
```

For python version, MPB goes within MEEP. You must reconfigure and re-install MEEP after installing MPB

### "Installing" jupyter-meep
This is not a python package. Each notebook must add the `./jupyter-meep-libs` directory to system path in order to import the modules.
