
from .. import tk
from .. import utils


class NvFileMenu(object):
    def __init__(self, root, menu_bar, view):
        self.view = view
        self.file_menu = tk.Menu(menu_bar, tearoff=False)
        self.root = root

        self.file_menu.add_command(label="New note", underline=0,
                              command=self.cmd_root_new, accelerator="Ctrl+N")
        self.root.bind_all("<Control-n>", self.cmd_root_new)

        self.file_menu.add_command(label="Delete note", underline=0,
                              command=self.cmd_root_delete, accelerator="Ctrl+D")
        self.root.bind_all("<Control-d>", self.cmd_root_delete)

        self.file_menu.add_command(label="Edit note", underline=0,
                              command=self.cmd_external_edit, accelerator="Ctrl+E")
        self.root.bind_all("<Control-e>", self.cmd_external_edit)

        self.file_menu.add_separator()

        self.file_menu.add_command(label="Sync full", underline=5,
                              command=self.cmd_sync_full, accelerator="Ctrl+Shift+S")
        self.root.bind_all("<Control-S>", self.cmd_sync_full)

        self.file_menu.add_command(label="Sync current note",
                              underline=0, command=self.cmd_sync_current_note,
                              accelerator="Ctrl+S")
        self.root.bind_all("<Control-s>", self.cmd_sync_current_note)

        self.file_menu.add_separator()

        self.file_menu.add_command(label="Render Markdown to HTML", underline=7,
                              command=self.cmd_markdown, accelerator="Ctrl+M")
        self.root.bind_all("<Control-m>", self.cmd_markdown)

        self.continuous_rendering = tk.BooleanVar()
        self.continuous_rendering.set(False)
        self.file_menu.add_checkbutton(
            label="Continuous Markdown to HTML rendering",
            onvalue=True, offvalue=False,
            variable=self.continuous_rendering)

        self.file_menu.add_command(label="Render reST to HTML", underline=7,
                              command=self.cmd_rest, accelerator="Ctrl+R")
        self.root.bind_all("<Control-r>", self.cmd_rest)

        self.file_menu.add_separator()

        self.file_menu.add_command(label="Exit", underline=1,
                              command=self.view.handler_close, accelerator="Ctrl+Q")
        self.root.bind_all("<Control-q>", self.view.handler_close)

    def cmd_root_new(self, evt=None):
        # this'll get caught by a controller event handler
        self.view.notify_observers('create:note', utils.KeyValueObject(
            title=self.view.get_search_entry_text()))
        # the note will be created synchronously, so we can focus the text area
        # already
        self.root.text_note.focus()

    def cmd_root_delete(self, evt=None):
        sidx = self.view.notes_list.selected_idx
        self.view.notify_observers('delete:note', utils.KeyValueObject(sel=sidx))

    def cmd_external_edit(self, evt=None):
        selected_index = self.view.notes_list.selected_idx
        self.view.notify_observers(
            'external-edit:note', utils.KeyValueObject(sel=selected_index))

    def cmd_sync_full(self, event=None):
        self.view.notify_observers('command:sync_full', None)

    def cmd_sync_current_note(self, event=None):
        self.view.notify_observers('command:sync_current_note', None)

    def cmd_markdown(self, event=None):
        self.view.notify_observers('command:markdown', None)

    def cmd_rest(self, event=None):
        self.view.notify_observers('command:rest', None)

    def get_continuous_rendering(self):
        return self.continuous_rendering.get()


class NvEditMenu(object):
    def __init__(self, root, menu_bar, view):
        self.view = view
        self.root = root

        self.edit_menu = tk.Menu(menu_bar, tearoff=False)

        self.edit_menu.add_command(label="Undo", accelerator="Ctrl+Z",
                              underline=0, command=lambda: self.view.text_note.edit_undo())
        self.root.bind_all("<Control-z>", lambda e: self.view.text_note.edit_undo())

        self.edit_menu.add_command(label="Redo", accelerator="Ctrl+Y",
                              underline=0, command=lambda: self.view.text_note.edit_undo())
        self.root.bind_all("<Control-y>", lambda e: self.view.text_note.edit_redo())

        self.edit_menu.add_separator()

        self.edit_menu.add_command(label="Cut", accelerator="Ctrl+X",
                              underline=2, command=self.cmd_cut)
        self.edit_menu.add_command(label="Copy", accelerator="Ctrl+C",
                              underline=0, command=self.cmd_copy)
        self.edit_menu.add_command(label="Paste", accelerator="Ctrl+V",
                              underline=0, command=self.cmd_paste)

        # FIXME: ctrl-a is usually bound to start-of-line. What's a
        # better binding for select all then?
        self.edit_menu.add_command(label="Select All", accelerator="Ctrl+A",
                              underline=7, command=self.cmd_select_all)

        self.edit_menu.add_separator()

        self.edit_menu.add_command(label="Find", accelerator="Ctrl+F",
                              underline=0, command=lambda: self.view.search_entry.focus())
        self.root.bind_all("<Control-f>", lambda e: self.view.search_entry.focus())

    def cmd_cut(self):
        self.view.text_note.event_generate('<<Cut>>')

    def cmd_copy(self):
        self.view.text_note.event_generate('<<Copy>>')

    def cmd_paste(self):
        self.view.text_note.event_generate('<<Paste>>')

    def cmd_select_all(self, evt=None):
        self.view.text_note.tag_add("sel", "1.0", "end-1c")
        # we don't want the text bind_class() handler for Ctrl-A to be fired.
        return "break"


class NvToolsMenu(object):
    def __init__(self, menu_bar, view):
        self.view = view
        self.tools_menu = tk.Menu(menu_bar, tearoff=False)
        self.tools_menu.add_command(label="Word Count",
                               underline=0, command=self.word_count)
        # the internet thinks that multiple modifiers should work, but this didn't
        # want to.
        #self.root.bind_all("<Control-Shift-c>", lambda e: self.word_count())

    def word_count(self):
        """
        Display count of total words and selected words in a dialog box.
        """

        selected_text = self.get_selected_text()
        selected_text_length = len(selected_text.split())

        txt = self.get_text()
        text_length = len(txt.split())

        self.view.show_info('Word Count', '%d words in total\n%d words in selection' % (text_length, selected_text_length))


class NvHelpMenu(object):
    def __init__(self, menu_bar, view):
        self.view = view
        self.help_menu = tk.Menu(menu_bar, tearoff=False)
        self.help_menu.add_command(label="About", underline=0,
                              command=self.cmd_help_about)
        self.help_menu.add_command(label="Bindings", underline=0,
                              command=self.cmd_help_bindings,
                              accelerator="Ctrl+?")

    def cmd_help_about(self):
        tkMessageBox.showinfo(
            'Help | About',
            'nvxp %s is copyright 2012 by Charl P. Botha '
            '<http://charlbotha.com/>\n\n'
            'A rather ugly but cross-platform simplenote client.' % (
                self.config.app_version,),
            parent=self.root)

    def cmd_help_bindings(self):
        h = HelpBindings()
        self.root.wait_window(h)

