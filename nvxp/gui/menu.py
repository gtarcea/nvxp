
from .. import tk
from .. import utils


class NvMenu(tk.Menu, object):
    """The base Menu class"""

    def __init__(self, view, menu_bar, **kw):
        super(NvMenu, self).__init__(self, menu_bar, **kw)
        self.view = view


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


class NvEditMenu(tk.Menu):
    pass


class NvToolsMenus(tk.Menu):
    pass


class NvHelpMenu(tk.Menu):
    pass


class NvMainMenu(tk.Menu):
    pass
