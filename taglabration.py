import pyaudio
import numpy as np
import taglameter

def calibrate():

    """ 
    Main function for the recalibration procedure. After the recalibration is 
    finished the paramters are saved in an npz file specified in 
    loadCalibrationParameters(). A previous calibration is required.

    Inputs
        port : pyAudio port to stream the sound
    """

    import shutil

    port = pyaudio.PyAudio() 

    print "\n\nWARNING! You are recalibrating the system! ",
    answ = raw_input("Is that what you really want to do?! ")
    
    if not(answ.lower() in ['y', 'yes', 'si', 'oui', 'ja', 'jaaaa']):
        print "Ok, no worries! Leaving calibration function..."
        return()

    [calFile, freq, loud, prevA0, eps, par] = loadCalibrationParameters()
    A0 = np.zeros(prevA0.shape)

    for fIx, f in enumerate(freq):
        for lIx, l in enumerate(loud):
            print "\n\nf = {:.0f}Hz, target loudness = {:.1f}dB".format(f, l)
            print "  | To increase intensity, press: up, right, w, s, x"
            print "  | To decrease intensity, press: down, left, q, a, z"
            print "  | To accept calibration, press: ENTER"
            A0[fIx,lIx] = calibrateTone(f, l, prevA0[fIx,lIx], port, par, eps)

    shutil.move(calFile, calFile[0:-4]+ 'Prev' + calFile[-4:])
    np.savez(calFile, A0 = A0, FREQ = freq, LOUD = loud, FS = par['fs'])

    print "\n\nCalibration finished! <3 File saved to {}\n\n".format(calFile)

    return()



def calibrateTone(f, l, a0, port, par, epsilon):

    """ 
    Calibrates the waveform amplitude of a [frequency, loudness] pair.

    Inputs
        f       : pure tone frequency (Hz)
        l       : target loudness (dB)
        a0      : initalisation value for the waveform amplitude (0 < a0 < 1)
        port    : pyAudio port to stream the sound
        par     : dictionary with the parameters, check loadParameters()
        epsilon : dictionary mapping pressed keys to adjustment sizes 
    
    Outputs 
        a0      : adjusted waveform amplitude (0 <= a0 <= 1)
    """

    fs  = float(par['fs'])
    dur = par['dur']
    key = None

    while not (key in ['\n', ' ']):

        streamer = taglameter.PyAudioStreamer(f, a0, par)
        stream   = port.open(format          = pyaudio.paFloat32,
                             channels        = 1,
                             rate            = par['fs'],
                             output          = True, 
                             stream_callback = streamer.callback)
        
        stream.start_stream()
        
        key = taglameter.listenKeyPress(par['dur'], 
                             terminateOnPress = True, verbose = False)   

        stream.stop_stream()
        stream.close()

        if key in epsilon.keys():
            a0 = a0 + epsilon[key]
            if a0 > 0.999:
                a0 = 0.999
                print "WARNING: You are trying to increase a0 but a0 < 1"
            elif a0 < 0.001:
                a0 = 0.001
                print "WARNING: You are trying to decrease a0 but a0 > 0"
            print "New factor: {:.3} ".format(a0),
            print "(epsilon = {:.3})".format(epsilon[key])

    return a0



def loadCalibrationParameters():

    """ 
    Returns the calibration parameters. Change this function to adjust them.
    
    Outputs 
        calf    : path to the calibration npz file 
        freq    : array holding the considered frequency values in Hz
        loud    : array holding the considered loundess values in dB
        freq    : flag that marks if the sound waveform is deplected
        prevA0  : list of arrays with the previous calibration of the system
        epsilon : dictionary mapping pressed keys to adjustment sizes 
        prevA0  : flag that marks if the sound waveform is deplected
        par     : dictionary with the basic parameters of the sounds
    """

    par  = {'dur'  : 100,   # maximum duration of the sound (seconds)
            'fs'   : 48000, # sample rate Hz
            'tau'  : 0}     # ramps time windows

    calf = './calibration.npz'   # path to calibration file

    epsilon = {'\x1b[A': 0.1,    # keyboard map for the calibration
               '\x1b[C': 0.05,   # procedure
               'w':      0.01,
               's':      0.005,
               'x':      0.001,
               'z':     -0.001,
               'a':     -0.005,
               'q':     -0.01,
               '\x1b[D':-0.05, 
               '\x1b[B':-0.1}

    if os.path.isfile(calf):
        calFile = np.load(calf)
        loud    = calFile['LOUD']
        freq    = calFile['FREQ']
        prevA0  = calFile['A0']
    else:
        loud   = np.arange(-10, 91, 5)
        freq   = 1000 * np.array([1,1.5,2,3] + range(4, 21, 2) + [0.25,0.5])
        prevA0 = 0.9 * np.ones([len(freq), len(loud)])

    return(calf, freq, loud, prevA0, epsilon, par)



if __name__ == "__main__":
    
    calibrate()

