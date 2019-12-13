from threading import Timer, enumerate

import wx
from pubsub.pub import addTopicDefnProvider, TOPIC_TREE_FROM_CLASS

import Topic_Def
from Engine import LoggerEngine
from Interface import LoggerInterface

addTopicDefnProvider(Topic_Def, TOPIC_TREE_FROM_CLASS)


def main():
    ex = wx.App()
    engine = LoggerEngine()
    gui = LoggerInterface(parent=None)
    print('Engine initilized: {:s}'.format(str(engine.__class__)))
    print('GUI initialized: {:s}'.format(str(gui.__class__)))
    ex.MainLoop()


if __name__ == '__main__':
    main()
    for thread in enumerate():
        if type(thread) == Timer:
            thread.cancel()
