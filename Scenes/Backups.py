from time import sleep

# resources
from Config import *
from Resources.Colors import *

# services
from Services.Audio import *
from Services.Video import *
from Services.Core import *
from Services.Input import *

class Backups():
    def loadDirectoryData(self, path):
        files, directories = self.core.GetDataInDirectory(path)
        self.currentDirectories = directories
        self.currentFiles = []
        self.currentIndex = 0
    
        for file in files:
            if ".aif" in file.lower():
                self.currentFiles.append(file)

    def getObjectType(self, index):
        if index < len(self.currentDirectories):
            return "Directory"
        elif (index - len(self.currentDirectories)) < len(self.currentFiles):
            return "File"
        else:
            return None

    def getObject(self, index):
        if index < len(self.currentDirectories):
            return self.currentDirectories[index]
        elif (index - len(self.currentDirectories)) < len(self.currentFiles):
            return self.currentFiles[(index - len(self.currentDirectories))]
        else:
            return None

    def __init__(self, core, audio, video, input):
        print 'Backups:: Starting Init'
        self.core = core
        self.audio = audio
        self.video = video
        self.input = input
        self.local = False
        self.menu = 0
        self.cursorPosition = 0
        self.contextPosition = 0
        self.currentFileName = ""
        self.g = 0
        self.currentIndex = 0
        self.volume = self.audio.GetVolume()
        self.op1Present = self.core.IsUSBDeviceConnected(Config.OP1USBVendor, Config.OP1USBProduct)
        
        if self.op1Present:
            # create mount directory if it doesn't exist
            self.core.ForceDirectory(Config.OP1USBMountDir)
            # get usb drive mount path
            self.mountpath = self.core.GetUSBMountPath(Config.OP1USBId)
            print(" > OP-1 device path: %s" % self.mountpath)
            # mount it!
            self.core.MountDevice(self.mountpath, Config.OP1USBMountDir)
            # load contents
            self.loadDirectoryData(Config.MediaDirectory + "/" + Config.BackupDirectory + "/");

    def Dispose(self):
        pass

    def Update(self):
        self.g = self.g + 1
        if (self.g > 255):
            self.g = 0

    def InputUpdate(self, k1, k2, k3, ku, kd, kl, kr, kp):

        if self.op1Present:
            if self.menu == 0:
                # main backups menu
                # up / down change menu option
                # left / right change backup context

                if ku:
                    self.currentIndex -= 1

                elif kd:
                    self.currentIndex += 1

                elif kl:
                    self.contextPosition -= 1;

                    if (len(self.currentDirectories) > 0): 
                        if (self.contextPosition < 0):
                            self.contextPosition = len(self.currentDirectories) - 1

                        Config.BackupContext = self.core.getNormPath(self.currentDirectories[self.contextPosition])
                    else:
                        Config.BackupContext = 'default'

                elif kr:
                    self.contextPosition += 1;
                    
                    if (len(self.currentDirectories) > 0): 
                        if (self.contextPosition >= len(self.currentDirectories)):
                            self.contextPosition = 0

                        Config.BackupContext = self.core.getNormPath(self.currentDirectories[self.contextPosition])
                    else:
                        Config.BackupContext = 'default'

                # cursor wrapping
                if (self.currentIndex < 0):
                    self.currentIndex = 5

                elif (self.currentIndex > 5):
                    self.currentIndex = 0

                if k1:
                    if (self.currentIndex == 0):
                        self.menu = 1
                    elif (self.currentIndex == 1):
                        self.menu = 2
                    elif (self.currentIndex == 2):
                        from Scenes.Synths import *
                        self.core.ChangeScene(Synths)
                    elif (self.currentIndex == 3):
                        from Scenes.Drums import *
                        self.core.ChangeScene(Drums)
                    elif (self.currentIndex == 4):
                        from Scenes.Tapes import *
                        self.core.ChangeScene(Tapes)
                    elif (self.currentIndex == 5):
                        from Scenes.Albums import *
                        self.core.ChangeScene(Albums)

                if k2:
                    pass
                    
                if k3:
                    self.core.UnmountDevice(Config.OP1USBMountDir)
                    from Scenes.MainMenu import *
                    self.core.ChangeScene(MainMenu)

            elif self.menu == 1:
                # create new context entry
                if ku:
                    phraseList = list(Config.BackupContext)
                    char = phraseList[self.cursorPosition]
                    charIndex = Config.ValidFilenameCharacters.index(char)
                    charIndex += 1;

                    if charIndex >= len(Config.ValidFilenameCharacters):
                        charIndex = 0

                    phraseList[self.cursorPosition] = Config.ValidFilenameCharacters[charIndex]
                    Config.BackupContext = "".join(phraseList)

                elif kd:
                    phraseList = list(Config.BackupContext)
                    char = phraseList[self.cursorPosition]
                    charIndex = Config.ValidFilenameCharacters.index(char)
                    charIndex -= 1;

                    if charIndex < 0:
                        charIndex = len(Config.ValidFilenameCharacters) - 1
                    
                    phraseList[self.cursorPosition] = Config.ValidFilenameCharacters[charIndex]
                    Config.BackupContext = "".join(phraseList)

                elif kl:
                    self.cursorPosition -= 1

                elif kr:
                    self.cursorPosition += 1

                # cursor wrapping
                if (self.cursorPosition < 0):
                    self.cursorPosition = Config.MaxFilenameLength

                elif (self.cursorPosition > Config.MaxFilenameLength):
                    self.cursorPosition = 0
                    
                if k1:
                    # create new backup directory
                    self.core.ForceDirectory(Config.MediaDirectory + "/" + Config.BackupDirectory + "/" + Config.BackupContext)
                    
                    # reload backup directories
                    self.loadDirectoryData(Config.MediaDirectory + "/" + Config.BackupDirectory + "/");
                    
                    # select new backup directory
                    for index, directory in enumerate(self.currentDirectories):
                        if self.core.getNormPath(directory) == Config.BackupContext:
                            self.contextPosition = index

                    # back to backup main menu
                    self.menu = 0

                if k2:
                    pass

                if k3:
                    # cancel action
                    self.menu = 0

            elif self.menu == 2:
                if k1:
                    # copy all local
                    self.video.DrawLargeText(
                        Config.PrimaryTextColor, 
                        (10, 10), 
                        "Copying!")

                    self.video.Update()

                    if self.local:
                        print("Backups:: Restoring Local System to OP1")
                        sourceDirectory = Config.MediaDirectory + "/" + Config.BackupDirectory + "/" + Config.BackupContext + "/"
                        destinationDirectory = Config.OP1USBMountDir + "/"
                    else:
                        print("Backups:: Backing up OP1 to Local System")
                        sourceDirectory = Config.OP1USBMountDir + "/"
                        destinationDirectory = Config.MediaDirectory + "/" + Config.BackupDirectory + "/" + Config.BackupContext + "/"

                    # clear out current synths and drums
                    self.core.DeleteFolder(destinationDirectory + "synth")
                    self.core.DeleteFolder(destinationDirectory + "drum")
                        
                    # copy
                    print("All:: Copying all directories from")
                    print(sourceDirectory)
                    print("to")
                    print(destinationDirectory)
                    self.core.CopyFolder(sourceDirectory, destinationDirectory)
                    self.menu = 0

                if k2:
                    if self.local == True:
                        self.local = False
                    else:
                        self.local = True

                if k3:
                    # cancel action
                    self.menu = 0

        elif self.op1Present == False:
            if k1 or k2 or k3:
                from Scenes.MainMenu import *
                self.core.ChangeScene(MainMenu)

    def Draw(self):
        indexColor = (100, self.g, 100)

        if self.op1Present:
            if self.menu == 0:
                # main backups menu
                self.video.DrawSmallText(
                    Config.PrimaryTextColor,
                    (2, 2),
                    'Context > ' + Config.BackupContext)

                self.video.DrawLargeText(
                    indexColor if self.currentIndex == 0 else Config.PrimaryTextColor, 
                    (10, 20), 
                    'New Context')
                    
                self.video.DrawLargeText(
                    indexColor if self.currentIndex == 1 else Config.PrimaryTextColor, 
                    (51, 38), 
                    'All')

                self.video.DrawLargeText(
                    indexColor if self.currentIndex == 2 else Config.PrimaryTextColor, 
                    (40, 56), 
                    'Synths')

                self.video.DrawLargeText(
                    indexColor if self.currentIndex == 3 else Config.PrimaryTextColor, 
                    (40, 74), 
                    'Drums')

                self.video.DrawLargeText(
                    indexColor if self.currentIndex == 4 else Config.PrimaryTextColor, 
                    (47, 92), 
                    'Tapes')

                self.video.DrawLargeText(
                    indexColor if self.currentIndex == 5 else Config.PrimaryTextColor, 
                    (40, 110), 
                    'Albums')

            elif self.menu == 1:
                # create new context entry
                self.video.DrawSmallText(
                    indexColor, 
                    (10, 10), 
                    "Create new Context")

                phraseList = list(Config.BackupContext)
                newPhraseList = []
                
                for index, char in enumerate(phraseList):
                    if (index == self.cursorPosition):
                        newPhraseList.append("[")
                        newPhraseList.append(phraseList[index])
                        newPhraseList.append("]")
                    else:
                        newPhraseList.append(phraseList[index])

                self.video.DrawLargeText(
                    Config.PrimaryTextColor, 
                    (10, 100), 
                    "".join(newPhraseList))

            elif self.menu == 2:
                # backup all menu
                if self.local:
                    self.video.DrawLargeText(
                        Config.PrimaryTextColor, 
                        (35, 2), 
                        "Restore?")
                else:
                    self.video.DrawLargeText(
                        Config.PrimaryTextColor, 
                        (35, 2), 
                        "Backup?")

                self.video.DrawLargeText(
                        Config.PrimaryTextColor, 
                        (35, 38), 
                        "Context")

                self.video.DrawLargeText(
                        Config.PrimaryTextColor, 
                        (35, 56), 
                        Config.BackupContext)

        else:
            self.video.DrawLargeText(
                indexColor, 
                (10, 10), 
                "OP1 Drive")

            self.video.DrawLargeText(
                indexColor, 
                (10, 25), 
                "Not Present!")

            self.video.DrawSmallText(
                Config.PrimaryTextColor, 
                (10, 40), 
                "Return to the menu,")

            self.video.DrawSmallText(
                Config.PrimaryTextColor, 
                (10, 48), 
                "plug in the OP1")

            self.video.DrawSmallText(
                Config.PrimaryTextColor, 
                (10, 56), 
                "and try again.")
