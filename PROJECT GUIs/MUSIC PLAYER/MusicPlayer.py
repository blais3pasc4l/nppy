import os
import sys
import time
import json
import random
import winsound
from tkinter import *
import tkinter.ttk as ttk
from tkinter import font, filedialog, messagebox
import pygame
from ttkbootstrap import Style
from mutagen.mp3 import MP3, HeaderNotFoundError


'''To setup ttkbootstrap:
        1. Install ttkbootstrap using python -m pip install ttkbootstrap
        2. Create themes using python -m ttkcreator
        3. Specify your desired color and save the themes
        4. If you want to use my theme then copy user.py file to
                <python-installed-directory>\Lib\site-packages\ttkbootstrap\themes'''


class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()

        self.PrevID = ''
        self.TagCount = 0
        self.childrens = []
        self.AudioFiles = dict()
        self.extensions = [('Music Files', '*.mp3')]
        self.PrevSearchChar = None  # Store previous search string
        self.RepeatAudio = None  # Track the state of Repeat Button
        self.IsMuted = False  # Track if audio has been muted or not
        self.AudioName = None  # Store currently playing song's name
        self.WindowNotMapped = False  # Track if window is minimized
        self.CurrentPlayingIndex = 0  # Index of current playing audio
        self.IsFindWidgetShown = False  # Track if FindWidget is shown
        self.SearchGlobalIndex = None  # Track the index of Search Value
        self.EOF = False  # Trigger to check if the last songs is about to play
        self.SearchLocalIndex = None   # Track the search index of filtered items
        self.PlayRandom = False  # Track if Random Button has been pressed or not
        self.RemTimer = None  # Stores an alarm to call change_time function in every 500 ms
        self.PreviousVolume = 100  # Store previous value of volume before muting and un-muting
        self.ScaleTimer = None  # Stores an alarm to call update_scale function in every 1000 ms
        self.ShowRemTime = False  # Trigger to check if remaining time has showed in total time button
        self.PlaylistPath = self.ResourcePath('playlists.json')  # File where list of audios are saved
        self.PreviousScaleValue = 0  # Store previous position of AudioSlider to avoid dragging in same position
        self.isButtonInMotion = False  # Trigger to check if audio_slider is in motion. True for the audio_slider is being dragged
        self.isPlaying = None  # Trigger to check if the song is playing. None for has not started playing yet, True for playing and False for pause

        self.master = Tk()
        self.master.withdraw()
        self.master.title('Music Player')
        self.master.iconbitmap(self.ResourcePath('icon.ico'))

        self.PlayImage = PhotoImage(file=self.ResourcePath('Play.png'))
        self.NextImage = PhotoImage(file=self.ResourcePath('Next.png'))
        self.UnmuteImage = PhotoImage(file=self.ResourcePath('Vol4.png'))
        self.PauseImage = PhotoImage(file=self.ResourcePath('Pause.png'))
        self.VolumeImage1 = PhotoImage(file=self.ResourcePath('Vol1.png'))
        self.VolumeImage2 = PhotoImage(file=self.ResourcePath('Vol2.png'))
        self.VolumeImage3 = PhotoImage(file=self.ResourcePath('Vol3.png'))
        self.VolumeImage4 = PhotoImage(file=self.ResourcePath('Vol4.png'))
        self.NoVolumeImage = PhotoImage(file=self.ResourcePath('Vol0.png'))
        self.SearchImage = PhotoImage(file=self.ResourcePath('Search.png'))
        self.StopAudioImage = PhotoImage(file=self.ResourcePath('Stop.png'))
        self.PreviousImage = PhotoImage(file=self.ResourcePath('Previous.png'))
        self.RepeatAllImage = PhotoImage(file=self.ResourcePath('RepeatAll.png'))
        self.SearchExitImage = PhotoImage(file=self.ResourcePath('SearchExit.png'))
        self.RandomActiveImage = PhotoImage(file=self.ResourcePath('RandomActive.png'))
        self.RepeatCurrentImage = PhotoImage(file=self.ResourcePath('RepeatCurrent.png'))
        self.RandomDisabledImage = PhotoImage(file=self.ResourcePath('RandomDisabled.png'))

        self.container = Frame(self.master)
        self.container.pack()

        self.Menu = Menu(self.container)
        self.FileMenu = Menu(self.Menu, tearoff=0)
        self.Menu.add_cascade(label='File', menu=self.FileMenu)
        self.master.config(menu=self.Menu)

        self.EmptySpace = ' ' * 10
        self.FileMenu.add_command(label='Open', accelerator=f'{self.EmptySpace}Ctrl + O' , command=self.OpenFiles)
        self.FileMenu.add_command(label='Open Playlist', accelerator=f'{self.EmptySpace}Ctrl + Shift + O', command=self.GetPlaylist)
        self.FileMenu.add_command(label='Find ...', accelerator=f'{self.EmptySpace}Ctrl + F' , command=self.ShowFindWidget)
        self.FileMenu.add_command(label='Save Playlist', accelerator=f'{self.EmptySpace}Ctrl + S', command=lambda: self.SavePlaylist(Event, True))
        self.FileMenu.add_command(label='Exit', accelerator=f'{self.EmptySpace}Ctrl + Q', command=self.master.destroy)

        self.AudioListFrame = Frame(self.container, width=621, height=239)
        self.AudioListFrame.pack()

        self.Columns = ['Title', 'Duration']

        self.style = Style('newtheme')
        self.Tree = ttk.Treeview(self.AudioListFrame, columns=self.Columns, show='headings', style='secondary.Treeview')
        self.Tree.pack(side=LEFT, fill=BOTH)

        # Attaching scrollbar to TreeView
        self.scrollbar = Scrollbar(self.AudioListFrame, orient="vertical", command=self.Tree.yview)
        self.Tree.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=RIGHT, fill='y')

        self.Tree.heading('Title', text='Title')
        self.Tree.column('Title', width=525)
        self.Tree.heading('Duration', text='Duration')
        self.Tree.column('Duration', width=60, anchor='center')

        self.TotalTimeVar = StringVar()
        self.TotalTimeVar.set('--:--')
        self.EscapedTimeVar = StringVar()
        self.EscapedTimeVar.set('--:--')

        self.TimeFrame = Frame(self.container)
        self.EscapedTimeLabel = Label(self.TimeFrame, textvariable=self.EscapedTimeVar, bd=0, takefocus=False)
        self.EscapedTimeLabel.pack(side=LEFT)
        self.TotalTimeLabel = Label(self.TimeFrame, textvariable=self.TotalTimeVar, bd=0)
        self.TotalTimeLabel.pack(side=RIGHT)
        self.TimeFrame.pack(fill='x')

        self.AudioSliderVar = IntVar()
        self.AudioSlider = ttk.Scale(self.container, from_=0, to=100, style='info.Horizontal.TScale', variable=self.AudioSliderVar)
        self.AudioSlider.pack(fill='x')

        self.VolumeSliderVar = IntVar()
        self.VolumeLabelVar = StringVar()
        self.VolumeLabelVar.set('100%')
        self.VolumeSliderVar.set(100)

        self.BottomFrame = Frame(self.container)
        self.BottomFrame.pack(side=BOTTOM, fill='x')
        self.ButtonsAttributes = {'bd': '0', 'bg': 'white', 'activebackground': 'white', 'takefocus': False}

        self.ButtonsFrame = Frame(self.BottomFrame)
        self.ButtonsFrame.pack(side=LEFT)

        self.PlayButton = Button(self.ButtonsFrame, image=self.PlayImage, **self.ButtonsAttributes, command=self.PlayOrPauseAudio)
        self.PlayButton.pack(side=LEFT)
        self.PreviousButton = Button(self.ButtonsFrame, image=self.PreviousImage, **self.ButtonsAttributes, command=lambda: self.PreviousNextAudio(button_name='Prev'))
        self.PreviousButton.pack(side=LEFT, padx=2, ipady=5)
        self.StopAudioButton = Button(self.ButtonsFrame, image=self.StopAudioImage, **self.ButtonsAttributes, command=self.StopAudio)
        self.StopAudioButton.pack(side=LEFT)
        self.NextButton = Button(self.ButtonsFrame, image=self.NextImage, **self.ButtonsAttributes, command=lambda: self.PreviousNextAudio(button_name='Next', event=Event))
        self.NextButton.pack(side=LEFT, padx=2)
        self.RepeatButton = Button(self.ButtonsFrame, image=self.RepeatAllImage, **self.ButtonsAttributes, command=self.ToggleRepeat)
        self.RepeatButton.pack(side=LEFT)
        self.RandomButton = Button(self.ButtonsFrame, image=self.RandomDisabledImage, **self.ButtonsAttributes, command=self.ToggleRandom)
        self.RandomButton.pack(side=LEFT, padx=2)
        self.SearchButton = Button(self.ButtonsFrame, image=self.SearchImage, **self.ButtonsAttributes, command=self.ShowFindWidget)
        self.SearchButton.pack(side=LEFT)

        self.VolumeFrame = Frame(self.BottomFrame)
        self.VolumeSliderFrame = Frame(self.VolumeFrame)
        self.MuteUnmuteButton = Button(self.VolumeFrame, image=self.VolumeImage4, **self.ButtonsAttributes, command=self.MuteUnmuteVolume)
        self.MuteUnmuteButton.pack(side=LEFT)
        self.VolumeSlider = ttk.Scale(self.VolumeSliderFrame, from_=0, to=100, variable=self.VolumeSliderVar, style='success.Horizontal.TScale', command=self.ChangeVolume)
        self.VolumeSlider.pack(side=LEFT, padx=5)
        self.VolumeLabel = Label(self.VolumeSliderFrame, textvariable=self.VolumeLabelVar, width=4, font=font.Font(weight='bold'))
        self.VolumeLabel.pack(side=LEFT)
        self.VolumeFrame.pack(side=LEFT, padx=2)

        self.SearchStyle = ttk.Style()
        self.SearchEntryVar = StringVar()
        self.SearchEntryVar.trace("w", self.SearchAudio)
        self.SearchFrame = Frame(self.ButtonsFrame, bg='#e5e5e5')
        self.SearchStyle.configure('Search.TEntry')
        self.SearchEntry = ttk.Entry(self.SearchFrame, width=26, style='Search.TEntry', textvariable=self.SearchEntryVar)
        self.SearchEntry.pack(side=LEFT)
        self.ExitSearchButton = Button(self.SearchFrame, image=self.SearchExitImage, bg='#e5e5e5', bd=0, activebackground='#e5e5e5', cursor='hand2', command=self.DestroyFindWidget)
        self.ExitSearchButton.pack(side=RIGHT)

        self.Tree.bind('<Delete>', self.RemoveFromList)
        self.Tree.bind('<space>', self.SpaceBarBindings)
        self.master.bind('<MouseWheel>', self.MouseWheel)
        self.Tree.bind('<Button-1>', self.SingleLeftClick)
        self.AudioSlider.bind('<Button-3>', self.SkipAudio)
        self.master.bind_all('<Control-o>', self.OpenFiles)
        self.master.bind_all("<Button-3>", self.RightClick)
        self.SearchEntry.bind('<Up>', self.UpDownSearchItems)
        self.master.bind_all('<Control-O>', self.GetPlaylist)
        self.SearchEntry.bind('<Down>', self.UpDownSearchItems)
        self.Tree.bind('<Motion>', self.RestrictResizingHeading)
        self.AudioSlider.bind('<B1-Motion>', self.ClickInMotion)
        self.master.bind_all('<Control-f>', self.ShowFindWidget)
        self.AudioSlider.bind('<B3-Motion>', self.ClickInMotion)
        self.master.bind_all('<Escape>', self.DestroyFindWidget)
        self.Tree.bind('<Shift-Delete>', self.RemoveFromPlaylist)
        self.VolumeFrame.bind('<Enter>', self.ShowVolumeSlider)
        self.VolumeFrame.bind('<Leave>', self.HideVolumeSlider)
        self.SearchEntry.bind('<Return>', self.SearchEntryReturnBind)
        self.TotalTimeLabel.bind('<Button-1>', self.ShowRemainingTime)
        self.master.bind_all('<Double-Button-1>', self.DoubleLeftClick)
        self.master.bind("<Control-q>", lambda e: self.master.destroy())
        self.AudioSlider.bind('<ButtonRelease-1>', self.ClickInMotionReleased)
        self.AudioSlider.bind('<ButtonRelease-3>', self.ClickInMotionReleased)
        self.master.bind("<Control-s>", lambda event: self.SavePlaylist(event, True))
        self.master.bind_all('<Home>', lambda event: self.Tree.see(self.childrens[0]))
        self.Tree.bind('<Control-a>', lambda e: self.Tree.selection_set(self.childrens))
        self.master.bind_all('<Control-Left>', lambda event: self.SkipAudio(event, 'backward'))
        self.master.bind_all('<Control-Right>', lambda event: self.SkipAudio(event, 'forward'))
        self.master.bind_all('<Left>', lambda event, change='decrease': self.ChangeVolume(event, change))
        self.master.bind_all('<Right>', lambda event, change='increase': self.ChangeVolume(event, change))
        self.master.bind_all('<End>', lambda event: self.Tree.see(self.childrens[len(self.AudioFiles) - 1]))
        self.AudioSlider.bind('<Button-1>', lambda event: self.SeekSingleClick(event, self.AudioSlider, self.SkipAudio))
        self.VolumeSlider.bind('<Button-1>', lambda event: self.SeekSingleClick(event, self.VolumeSlider, self.ChangeVolume, True))

        self.InitialPosition()
        self.StopWindowFlicking()

        self.master.mainloop()

    def RestrictResizingHeading(self, event):
        '''Restrict user to resize the columns of Treeview '''

        if self.Tree.identify_region(event.x, event.y) == "separator":
            return "break"

    def StopWindowFlicking(self):
        '''When window is minimize and maximized continuously then black
           color gets appear on the window for fraction of seconds which
           looks like the window is flickering'''

        if self.master.winfo_ismapped() == 0:  # When window is minimized
            self.container.pack_forget()
            self.master.config(bg='#e5e5e5')
            self.WindowNotMapped = True

        if self.master.winfo_ismapped() == 1 and self.WindowNotMapped:  # When window is restored
            self.master.after(0, lambda: self.container.pack())
            self.WindowNotMapped = False

        self.master.after(5, self.StopWindowFlicking)

    def InitialPosition(self):
        '''Set window position to the center when program starts first time'''

        self.master.update()
        self.master.resizable(0, 0)

        width = self.master.winfo_width()
        height = self.master.winfo_height()
        screen_width = self.master.winfo_screenwidth() // 2
        screen_height = self.master.winfo_screenheight() // 2

        self.master.geometry(f'{width}x{height}+{screen_width - width // 2}+{screen_height - height // 2}')
        self.master.deiconify()

    def ClickedAtEmptySpace(self, event=None):
        '''Check if user has clicked in empty space'''

        return self.Tree.identify('item', event.x, event.y) == ''

    def SingleLeftClick(self, event):
        '''When user single left click inside Tree widget'''

        if self.Tree.identify_region(event.x, event.y) == 'heading':
            # Restrict single left clicking if the cursor is on Treeview's heading
            return

        if not self.AudioFiles:
            # If there is no audio played yet but user left clicks
            # then make single left click event as double left click

            self.OpenFiles()
            return 'break'

    def DoubleLeftClick(self, event=None):
        '''When user double clicks anywhere in window'''

        x, y = self.master.winfo_pointerxy()
        widget = self.master.winfo_containing(x, y)

        if widget == self.Tree:
            if self.Tree.identify_region(event.x, event.y) == 'heading':
                self.DRY_1()

            elif self.ClickedAtEmptySpace(event):
                # When some files are opened and user double clicks
                # on the empty spaces then open file_dialog to open additional audio files
                self.OpenFiles()

            else:
                selection = self.Tree.selection()

                if selection:
                    index = self.childrens.index(selection[0])

                    if index == self.CurrentPlayingIndex:
                        self.AddRemoveSelection('Add')

                    else:
                        self.isPlaying = None

                    self.PlayOrPauseAudio()

        elif widget in [self.EscapedTimeLabel, self.VolumeLabel] or isinstance(widget, Frame):
            # When user clicks to the empty space or
            # to the EscapedTimeLabel or VolumeLabel
            self.DRY_1()

    def SeekSingleClick(self, event, widget, function, seek=False):
        '''Hijacking Single Left Click to work like Single Right Click
           to change the value of Scale to the position it is clicked

           Setting seek parameter to True activates audio_slider but
           not seek_scale when there is no audio in audio_list'''

        if self.AudioFiles or seek:
            if event.y not in [0, 1, 2, 3, 4, 12, 13, 14, 15]:
                # I have noticed that we can click on some regions outside of ttk.Scale
                # making audio repeating at the same position. Those regions in event.y
                # are [0, 1, 2, 3, 4, 12, 13, 14, 15] where [0, 1, 2, 3, 4] are the top
                # regions of and [12 ,13, 14, 15] are the bottom regions of ttk.Scale.
                # When user clicks to these regions must be ignored.

                widget.event_generate('<Button-3>', x=event.x, y=event.y)
                function(event)

        return 'break'

    def SpaceBarBindings(self, event=None):
        '''When user presses space-bar'''

        if self.master.focus_get() != self.SearchEntry:
            selections = self.Tree.selection()

            if self.childrens and selections and self.childrens.index(selections[0]) != self.CurrentPlayingIndex:
                self.isPlaying = None

            self.PlayOrPauseAudio()

    def ClickInMotion(self, event=None):
        '''When user holds left button and starts to drag left or right'''

        if self.isButtonInMotion is False:
            self.isButtonInMotion = True

    def ClickInMotionReleased(self, event=None):
        '''When user stops dragging left or right the AudioSlider'''

        if self.isButtonInMotion:
            self.isButtonInMotion = False

            if self.PreviousScaleValue != self.AudioSliderVar.get():
                self.PreviousScaleValue = self.AudioSliderVar.get()
                self.SkipAudio(event)

    def MouseWheel(self, event):
        '''Change Volume or Skip Audio when ScrollWheel button'''

        x, y = self.master.winfo_pointerxy()
        widget = self.master.winfo_containing(x, y)

        if widget not in [self.Tree, self.AudioSlider, self.scrollbar]:
            self.ChangeVolume(event)

        elif widget == self.AudioSlider:  # Skip audio
            self.SkipAudio(event)

    def ShowVolumeSlider(self, event=None):
        '''Show the volume slider when user hovers to volume button'''

        self.VolumeSliderFrame.pack(side=LEFT)

    def HideVolumeSlider(self, event=None):
        '''Hide the volume slider when user hovers away from the
           volume button'''

        self.VolumeSliderFrame.pack_forget()

    def OpenFiles(self, event=None, files=None):
        '''Open dialog box to select audio files'''

        ShowErrorMessage = False

        if files is None:
            files = filedialog.askopenfilenames(filetypes=self.extensions, initialdir=os.getcwd(), defaultextension=self.extensions)

        if files:
            for file in files:
                try:
                    pygame.mixer.music.set_volume(0)
                    pygame.mixer.music.load(file)
                    pygame.mixer.music.play()
                    length = MP3(file).info.length

                    basename = os.path.basename(file)
                    _time = time.strftime('%H:%M:%S', time.gmtime(length)).lstrip('00').strip(':')

                    self.Tree.insert('', END, values=(basename, _time), tag=self.TagCount)
                    self.AudioFiles.update({basename: (file, self.TagCount)})
                    self.TagCount += 1

                except (pygame.error, HeaderNotFoundError):
                    if ShowErrorMessage is False:
                        ShowErrorMessage = True
                        messagebox.showinfo('ERR', 'Some audio file(s) are not supported so ignoring them')

                pygame.mixer.music.stop()

            self.childrens = self.Tree.get_children()
            self.LowerCasedAudioFiles = [f.lower() for f in self.AudioFiles.keys()]

            if self.IsMuted is False:
                pygame.mixer.music.set_volume(self.PreviousVolume / 100)

            if self.isPlaying is None and not self.Tree.selection():
                self.Tree.focus_force()
                self.Tree.focus(self.childrens[0])
                self.Tree.selection_set(self.childrens[0])

            if len(self.AudioFiles) == 1:  # Play audio if user opens only 1 audio file
                self.PlayOrPauseAudio()

        return 'break'

    def GetPlaylist(self, event=None):
        '''Get audio path stored in a file'''

        try:
            with open(self.PlaylistPath, 'r') as f:
                contents = json.load(f)

        except (json.decoder.JSONDecodeError, FileNotFoundError):
            contents = {}
            messagebox.showerror('ERR', 'Either playlists file is corrupt or does not exist')

        if contents:
            files = [f for f in contents['playlists'].values() if os.path.exists(f)]  # Removing audios that does not exists
            self.OpenFiles(files=files)

        else:
            winsound.MessageBeep()

    def AddRemoveSelection(self, status):
        '''Add or Remove selection when audio changes'''

        if status == 'Remove':
            if self.AudioName:  # Removing the previous selection if another audio has been played before
                _tag = self.AudioFiles[self.AudioName][1]
                self.Tree.tag_configure(_tag, background='#e5e5e5', foreground='#333333')

        else:
            if self.AudioName is None:
                self.PlayOrPauseAudio()

            else:
                _tag = self.AudioFiles[self.AudioName][1]
                self.Tree.tag_configure(_tag, background='#29465b')
                self.Tree.selection_remove(self.Tree.selection()[0])

    def PlayOrPauseAudio(self, event=None):
        '''Play or pause audio when play or pause button is pressed'''

        try:
            if self.AudioFiles:
                if self.isPlaying is None:  # Audio not playing yet
                    cursel = self.Tree.selection()
                    self.AddRemoveSelection('Remove')

                    if len(cursel) == 1:  # Play Audio if there is only one selection
                        cursel = cursel[0]
                        self.CurrentPlayingIndex = self.childrens.index(cursel)

                        if self.PrevID != cursel:  # Play Audio only if current playing audio is different than selected audio
                            self.PrevID = cursel
                            self.isPlaying = True
                            _image = self.PauseImage

                            self.AudioName = self.Tree.item(cursel)['values'][0]
                            self.CurrentAudioPath = self.AudioFiles[self.AudioName][0]

                            self.TotalTime = MP3(self.CurrentAudioPath).info.length
                            self.AudioSlider.config(to=int(self.TotalTime))
                            self.Tree.tag_configure(self.AudioFiles[self.AudioName][1], foreground='silver')
                            _time = time.strftime('%H:%M:%S', time.gmtime(self.TotalTime)).lstrip('00').lstrip(':')
                            self.TotalTimeVar.set(_time)
                            self.EscapedTimeVar.set('00:00')
                            self.AudioSliderVar.set(0)

                            self.AddRemoveSelection('Add')
                            pygame.mixer.music.load(self.CurrentAudioPath)  # Loading selected file for playing
                            pygame.mixer.music.play()  # Start playing loaded file

                            if self.ScaleTimer:
                                self.master.after_cancel(self.ScaleTimer)

                            self.ScaleTimer = self.master.after(250, self.UpdateScale)

                elif self.isPlaying is True:  # Audio is being played
                    self.isPlaying = False
                    _image = self.PlayImage
                    pygame.mixer.music.pause()
                    self.master.after_cancel(self.ScaleTimer)

                elif self.isPlaying is False:  # Audio is paused
                    self.isPlaying = True
                    _image = self.PauseImage
                    pygame.mixer.music.play(start=self.AudioSliderVar.get())
                    self.ScaleTimer = self.master.after(250, self.UpdateScale)

                self.PlayButton.config(image=_image)

        except (TclError, UnboundLocalError):
            pass

    def StopAudio(self, event=None):
        '''Stop playing audio'''

        if self.isPlaying is not None:  # If audio is playing or is paused
            pygame.mixer.music.stop()

            if self.ScaleTimer:
                self.master.after_cancel(self.ScaleTimer)

            self.PrevID = ''
            self.isPlaying = None
            self.AudioSliderVar.set(0)
            self.CurrentPlayingIndex = 0
            self.TotalTimeVar.set('--:--')
            self.EscapedTimeVar.set('--:--')
            self.Tree.see(self.childrens[0])
            self.AddRemoveSelection('Remove')
            self.Tree.selection_set(self.childrens[0])
            self.PlayButton.config(image=self.PlayImage)

        else:
            winsound.MessageBeep()

    def ToggleRepeat(self, event=None):
        '''When user clicks repeat button'''

        if self.RepeatAudio is None:  # Button has not clicked yet
            self.RepeatAudio = 'LoopAll'
            self.RepeatButton.config(relief='sunken')

        elif self.RepeatAudio == 'LoopAll':
            self.RepeatAudio = 'LoopCurrent'
            self.RepeatButton.config(image=self.RepeatCurrentImage)

        elif self.RepeatAudio == 'LoopCurrent':
            self.RepeatAudio = None
            self.RepeatButton.config(image=self.RepeatAllImage, relief='raised')

    def ToggleRandom(self, event=None):
        '''When user clicks random button'''

        if self.PlayRandom is False:
            self.PlayRandom = True
            self.RandomButton.config(image=self.RandomActiveImage)

        else:
            self.PlayRandom = False
            self.RandomButton.config(image=self.RandomDisabledImage)

    def UpdateScale(self, event=None):
        '''Continuously update escaping time and slider values
           until songs comes to end'''

        self.CurrentPos = pygame.mixer.music.get_pos() / 1000

        if self.AudioSliderVar.get() > int(self.CurrentPos):
            # When user skips audio and the position of AudioSlider
            # becomes more than the previous AudioSlider position
            self.CurrentPos = self.AudioSliderVar.get() + 1

        self.EscapedTimeVar.set(time.strftime('%H:%M:%S', time.gmtime(self.CurrentPos)))
        self.AudioSliderVar.set(int(self.CurrentPos))

        if int(self.CurrentPos) >= int(self.TotalTime):  # Checking if audio has complete playing
            self.master.after_cancel(self.ScaleTimer)

            self.AudioSliderVar.set(0)
            self.TotalTimeVar.set('--:--')
            self.EscapedTimeVar.set('--:--')

            if self.CurrentPlayingIndex == len(self.AudioFiles) - 1:
                if self.RepeatAudio in ['LoopAll', 'LoopCurrent'] or self.PlayRandom:
                    self.EOF = False

                else:
                    self.EOF = True
                    self.StopAudio()

            if self.EOF:
                self.EOF = False
                self.ShowRemTime = False
                self.PlayButton.config(image=self.PlayImage)

                if self.RemTimer:
                    self.master.after_cancel(self.RemTimer)

            elif self.RepeatAudio == 'LoopCurrent':
                self.PrevID = ''
                self.isPlaying = None
                self.Tree.selection_set(self.childrens[self.CurrentPlayingIndex])
                self.PlayOrPauseAudio()

            elif self.RepeatAudio == 'LoopAll' and self.CurrentPlayingIndex == len(self.AudioFiles) - 1:
                if self.PlayRandom is True:
                    self.PreviousNextAudio(button_name='next')

                else:
                    self.PrevID = ''
                    self.isPlaying = None
                    self.Tree.selection_set(self.childrens[0])
                    self.Tree.see(self.childrens[0])
                    self.PlayOrPauseAudio()

            else:
                self.PreviousNextAudio(button_name='next')

        else:
            self.ScaleTimer = self.master.after(1000, self.UpdateScale)

    def PreviousNextAudio(self, event=None, button_name=None):
        '''Play previous and present audio present in list-box'''

        try:
            if self.AudioFiles:
                if self.PlayRandom:
                    self.PrevID = ''
                    self.CurrentPlayingIndex = random.randint(0, len(self.AudioFiles) - 1)

                elif button_name == 'Prev':
                    if self.CurrentPlayingIndex == 0:
                        return

                    self.CurrentPlayingIndex -= 1

                else:
                    if self.CurrentPlayingIndex >= len(self.AudioFiles) - 1:
                        return

                    self.CurrentPlayingIndex += 1

                self.isPlaying = None
                self.AddRemoveSelection('Remove')

                item = self.childrens[self.CurrentPlayingIndex]
                self.Tree.see(item)
                self.Tree.focus(item)
                self.Tree.selection_set(item)
                self.PlayOrPauseAudio()

        except TclError:
            pass

    def SkipAudio(self, event=None, direction=None):
        '''Skip song as the user moves the slider'''

        if self.isPlaying:
            SkipAt = self.AudioSliderVar.get()

            if direction == 'forward' or (not(isinstance(event, str)) and event.delta > 0):
                SkipAt += 5

                if SkipAt >= self.TotalTime:
                    self.PreviousNextAudio()
                    return

            elif direction == 'backward' or (not(isinstance(event, str)) and event.delta < 0):
                SkipAt -= 5

                if SkipAt <= 0:
                    SkipAt = 0

            self.AudioSliderVar.set(SkipAt)

            if self.isPlaying:
                pygame.mixer.music.play(start=SkipAt)
                self.MuteUnmuteVolume(nochange=True)

            self.EscapedTimeVar.set(time.strftime('%H:%M:%S', time.gmtime(SkipAt)))

    def ChangeVolume(self, event=None, change=None):
        '''Increase or decrease volume when user drags volume bar or
           when user presses right arrow or left arrow
                Here volume value is between 0-1'''

        if self.master.focus_get() == self.SearchEntry and not event:
            event.widget.tk_focusNext().focus()

        CurrentVolume = self.VolumeSliderVar.get()

        if change == 'increase' or (not(isinstance(event, str)) and event.delta > 0):
            CurrentVolume += 5

            if CurrentVolume >= 100:
                CurrentVolume = 100

        elif change == 'decrease' or (not(isinstance(event, str)) and event.delta < 0):
            CurrentVolume -= 5

            if CurrentVolume <= 0:
                CurrentVolume = 00

        if CurrentVolume == 0:
            self.IsMuted = False

        else:
            self.IsMuted = True
            self.PreviousVolume = CurrentVolume

        self.MuteUnmuteVolume()

        return 'break'

    def MuteUnmuteVolume(self, event=None, nochange=False):
        '''Mute and Unmute volume

           nochange parameter is to skip indented block of
           following first if statement to un-change volume
           when audio is skipped or changed'''

        if nochange is False:
            if self.IsMuted is False:  # Volume is not muted before
                self.IsMuted = True
                self.PreviousVolume = self.VolumeSliderVar.get()
                self.VolumeLabelVar.set('0%')
                pygame.mixer.music.set_volume(0)
                self.VolumeSliderVar.set(0)

            else:  # Volume is muted before
                self.IsMuted = False
                self.VolumeSlider.config(state='normal')
                self.VolumeSliderVar.set(self.PreviousVolume)
                pygame.mixer.music.set_volume(self.PreviousVolume / 100)
                self.VolumeLabelVar.set(f'{self.PreviousVolume}%')

        SliderGet = self.VolumeSliderVar.get()

        if SliderGet == 0:
            self.MuteUnmuteButton.config(image=self.NoVolumeImage)

        elif SliderGet <= 25:
            self.MuteUnmuteButton.config(image=self.VolumeImage1)

        elif SliderGet <= 50:
            self.MuteUnmuteButton.config(image=self.VolumeImage2)

        elif SliderGet <=75:
            self.MuteUnmuteButton.config(image=self.VolumeImage3)

        else:
            self.MuteUnmuteButton.config(image=self.VolumeImage4)

    def ShowRemainingTime(self, event=None):
        '''Show remaining time of current playing audio'''

        if self.isPlaying is not None:
            if self.ShowRemTime is False:  # If remaining time has not been shown
                self.ShowRemTime = True
                self.ChangeTime()

            else:  # Remaining time has already been show
                self.ShowRemTime = False
                self.master.after_cancel(self.RemTimer)
                self.TotalTimeVar.set(time.strftime('%H:%M:%S', time.gmtime(self.TotalTime)))

    def ChangeTime(self):
        '''Calculate remaining time of currently playing song'''

        gmtime = time.gmtime(self.TotalTime - self.CurrentPos)
        self.TotalTimeVar.set(time.strftime('-%H:%M:%S', gmtime))
        self.RemTimer = self.master.after(500, self.ChangeTime)

    def RightClick(self, event=None):
        '''When user right clicks inside list-box'''

        x, y = event.x , event.y  # Cursor position with respect to Tk window
        _x, _y = self.master.winfo_pointerxy()  # Cursor position with repsect to monitor resolution

        CurrentSelection = self.Tree.selection()
        widget = self.master.winfo_containing(_x, _y)
        RightClickMenu = Menu(self.master, tearoff=False)

        if widget == self.Tree:
            if CurrentSelection:
                if self.ClickedAtEmptySpace(event):
                    RightClickMenu.add_command(label='Open', command=self.OpenFiles)

                else:
                    if len(self.Tree.selection()) == 1:
                        self.Tree.event_generate("<Button-1>", x=x, y=y)

                    RightClickMenu.add_command(label='Remove from list', command=self.RemoveFromList)
                    RightClickMenu.add_command(label='Remove from playlist', command=self.RemoveFromPlaylist)

            else:
                if self.Tree.identify_element(x, y) == 'text':
                    self.Tree.event_generate('<Button-1>', x=x, y=y)
                    self.Tree.event_generate('<Button-3>', x=x, y=y)

                elif self.Tree.identify_region(x, y) == 'heading' or self.ClickedAtEmptySpace(event):
                    RightClickMenu.add_command(label='Open', command=self.OpenFiles)
                    RightClickMenu.add_command(label='Open Playlist', command=self.GetPlaylist)

        elif widget in [self.EscapedTimeLabel, self.VolumeLabel] or isinstance(widget, Frame):
            RightClickMenu.add_command(label='Open', command=self.OpenFiles)
            RightClickMenu.add_command(label='Open Playlist', command=self.GetPlaylist)

        try:
            RightClickMenu.tk_popup(event.x_root, event.y_root)

        finally:
            RightClickMenu.grab_release()

    def RemoveFromList(self, event=None):
        '''Remove selected item from the list-box'''

        try:
            CurrentIndexes = self.Tree.selection()

            for iid in CurrentIndexes:
                if self.childrens.index(iid) == self.CurrentPlayingIndex and self.isPlaying is not None:
                    self.StopAudio()

                song_name = self.Tree.item(iid)['values'][0]
                self.AudioFiles.pop(song_name)
                self.Tree.delete(iid)

            self.LowerCasedAudioFiles = [f.lower() for f in self.AudioFiles.keys()]

            index = self.childrens.index(iid)
            self.childrens = self.Tree.get_children()
            self.Tree.focus(self.childrens[index])
            self.Tree.selection_set(self.childrens[index])

        except (IndexError, TclError):
            pass

    def RemoveFromPlaylist(self, event=None):
        '''Remove selected item from the list-box as well from the playlist file'''

        self.RemoveFromList()
        self.SavePlaylist()

    def SavePlaylist(self, event=None, show_message=False):
        '''Save audio path present in list-box'''

        if self.AudioFiles:
            newAudioFiles = {k: v[0] for k, v in self.AudioFiles.items()}  # Saving Audios path without tagCount

            with open(self.PlaylistPath, 'w') as f:
                contents = {'playlists': newAudioFiles}
                json.dump(contents, f, indent=4)

                if show_message:
                    messagebox.showinfo('Saved!', 'Playlist Saved !!')

        else:
            winsound.MessageBeep()

    def ShowFindWidget(self, event=None):
        '''Show Find widget if not already shown'''

        if self.IsFindWidgetShown is False:
            self.IsFindWidgetShown = True
            self.SearchEntry.focus()
            self.SearchButton.pack_forget()
            self.SearchFrame.pack(side=LEFT)

        else:
            self.SearchEntry.focus()

    def DestroyFindWidget(self, event=None):
        '''Destroy Find widget when pressed ESC or X button'''

        self.master.focus_force()
        self.SearchEntryVar.set('')
        self.IsFindWidgetShown = False
        self.SearchFrame.pack_forget()
        self.SearchButton.pack(side=LEFT)

    def SearchAudio(self, *args):
        '''Searching Audio'''

        try:
            value = self.SearchEntryVar.get().lower()

            if value:
                self.filteredFiles = [f for f in self.LowerCasedAudioFiles if f.startswith(value)]
                self.SearchLocalIndex = 0

                self.SearchGlobalIndex = self.LowerCasedAudioFiles.index(self.filteredFiles[self.SearchLocalIndex])
                item = self.childrens[self.SearchGlobalIndex]
                self.Tree.see(item)

        except (IndexError, AttributeError):
            pass

    def UpDownSearchItems(self, event=None):
        '''When user presses Up or Down arrow in SearchEntry box'''

        try:
            arrow = event.keysym

            if not self.SearchEntryVar.get():
                self.filteredFiles = []

            if arrow == 'Up':
                if self.SearchLocalIndex == 0:
                    self.SearchLocalIndex = len(self.filteredFiles)

                self.SearchLocalIndex -= 1

            elif arrow == 'Down':
                if self.SearchLocalIndex == len(self.filteredFiles) - 1:
                    self.SearchLocalIndex = -1

                if self.SearchLocalIndex != 0:
                    self.SearchLocalIndex += 1

            self.SearchGlobalIndex = self.LowerCasedAudioFiles.index(self.filteredFiles[self.SearchLocalIndex])

            item = self.childrens[self.SearchGlobalIndex]
            self.Tree.see(item)
            self.Tree.focus(item)
            self.Tree.selection_set(item)
            self.Tree.focus_force()

        except (TypeError, AttributeError, IndexError):
            # When no audio is opened though user wants to make a search
            winsound.MessageBeep()

    def SearchEntryReturnBind(self, event=None):
        '''When user hits Enter key when focused to SearchEntry box'''

        if self.SearchGlobalIndex:
            item = self.childrens[self.SearchGlobalIndex]
            self.Tree.focus(item)
            self.Tree.selection_set(item)

            if self.SearchGlobalIndex != self.CurrentPlayingIndex:
                self.isPlaying = None

            self.PlayOrPauseAudio()
            self.DestroyFindWidget()

    def DRY_1(self):
        '''Some conditions that are used for multiple times. So,
           to avoid repetition putting them in this method'''

        if self.isPlaying is not None:
            self.PlayOrPauseAudio()

        elif not self.AudioFiles:
            self.OpenFiles()

    def ResourcePath(self, FileName):
        '''Get absolute path to resource from temporary directory

        In development:
            Gets path of files that are used in this script like icons, images or file of any extension from current directory

        After compiling to .exe with pyinstaller and using --add-data flag:
            Gets path of files that are used in this script like icons, images or file of any extension from temporary directory'''

        try:
            base_path = sys._MEIPASS  # PyInstaller creates a temporary directory and stores path of that directory in _MEIPASS

        except AttributeError:
            base_path = os.path.dirname(__file__)

        return os.path.join(base_path, 'included_files', FileName)


if __name__ == '__main__':
    MusicPlayer()
