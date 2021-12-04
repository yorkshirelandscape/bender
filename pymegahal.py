#!/usr/bin/env python

"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
For a copy of the license see http://www.gnu.org

=====================================================================
Based on megahal.py
author : www.peileppe.com
"""

from optparse import OptionParser
import sys
from megahal import *

DEFAULT_TRANSCRIPT = 'pymegahal-transcript.txt'

def interact_record(megahal):
    """Have a friendly chat session.. ^D to exit"""
    output_transcript=open(DEFAULT_TRANSCRIPT,"a") 
    print ('Transcription has began')
    while True:
        try:
            phrase = input('> ')
        except EOFError:
            close_transcript(output_transcript)
            break
        if phrase:
            output_transcript.write("User: "+phrase+"\n")
            answer=megahal.get_reply(phrase)
            print(answer)
            #str1='megahal:'+answer+'\n'
            #output_transcript.write(str1)

def close_transcript(output_transcript):
    """ exiting closing transcript  """
    print ('Closing transcript')
    output_transcript.write(" --------- "+"\n")
    output_transcript.close()

def main(argv=None):
    optparse = OptionParser(version=__version__, description=__doc__)
    optparse.add_option('-b', '--brain', dest='brainfile', metavar='<file>', default=DEFAULT_BRAINFILE,
                        help='location of brain (default: %default)')
    optparse.add_option('-o', '--order', metavar='<int>', default=DEFAULT_ORDER, type='int',
                        help='order of markov chain (default: %default)')
    optparse.add_option('-t', '--timeout', metavar='<float>', default=DEFAULT_TIMEOUT, type='float',
                        help='how long to look for replies (default: %default)')
    optparse.add_option('-T', '--train', metavar='<file>', help='train brain with file')
    opts, args = optparse.parse_args(argv)

    megahal = MegaHAL(brainfile=opts.brainfile, order=opts.order, timeout=opts.timeout)
    if opts.train:
        megahal.train(opts.train)
    interact_record(megahal)

    return 0

if __name__ == '__main__':
    sys.exit(main())
