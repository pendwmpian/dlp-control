from pattern_on_the_fly import PatternOnTheFly
import numpy as np

dmd = PatternOnTheFly()

# Enable Trigger 1 (1000 ms delay)
dmd.EnableTrigIn1(Delay=1000)

dmd.DefinePattern(0, 2000000, 0, np.ones((1080, 1920)))

dmd.SendImageSequence(nRepeat=2)

dmd.StartRunning()
# Patterns will be displayed 1000 ms after the first hardware trigger is received following StartRunning().
# If nRepeat > 1, the pattern sequence starts upon each trigger, repeating up to nRepeat times.

# Disable Trigger 1 mode
dmd.DisableTrigIn1()