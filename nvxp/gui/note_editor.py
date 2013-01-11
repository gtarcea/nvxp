
from .. import tk
import tkFont


class OriginalCommand:

    def __init__(self, redir, name):
        self.redir = redir
        self.name = name
        self.tk = redir.tk
        self.orig = redir.orig
        self.tk_call = self.tk.call
        self.orig_and_name = (self.orig, self.name)

    def __repr__(self):
        return "OriginalCommand(%r, %r)" % (self.redir, self.name)

    def __call__(self, *args):
        return self.tk_call(self.orig_and_name + args)


class WidgetRedirector:

    """Support for redirecting arbitrary widget subcommands."""

    def __init__(self, widget):
        self.dict = {}
        self.widget = widget
        self.tk = mytk = widget.tk
        w = widget._w
        self.orig = w + "_orig"
        mytk.call("rename", w, self.orig)
        mytk.createcommand(w, self.dispatch)

    def __repr__(self):
        return "WidgetRedirector(%s<%s>)" % (self.widget.__class__.__name__,
                                             self.widget._w)

    def close(self):
        for name in self.dict.keys():
            self.unregister(name)
        widget = self.widget
        del self.widget
        orig = self.orig
        del self.orig
        mytk = widget.tk
        w = widget._w
        mytk.deletecommand(w)
        mytk.call("rename", orig, w)

    def register(self, name, function):
        if name in self.dict:
            previous = dict[name]
        else:
            previous = OriginalCommand(self, name)
        self.dict[name] = function
        setattr(self.widget, name, function)
        return previous

    def unregister(self, name):
        if name in self.dict:
            function = self.dict[name]
            del self.dict[name]
            if hasattr(self.widget, name):
                delattr(self.widget, name)
            return function
        else:
            return None

    def dispatch(self, cmd, *args):
        m = self.dict.get(cmd)
        try:
            if m:
                return m(*args)
            else:
                return self.tk.call((self.orig, cmd) + args)
        except tk.TclError:
            return ""


class NoteEditor(tk.Text):
    """We would like to know when the Text widget's contents change.  We can't
    just override the insert method, we have to make use of some Tk magic.
    This magic is encapsulated in the idlelib.WidgetRedirector class which
    we use here.
    """

    def __init__(self, master=None, cnf={}, **kw):
        tk.Text.__init__(self, master, cnf, **kw)

        # now attach the redirector
        self.redir = WidgetRedirector(self)
        self.orig_insert = self.redir.register("insert", self.new_insert)
        self.orig_delete = self.redir.register("delete", self.new_delete)
        self.fonts = [kw['font']]

    def new_insert(self, *args):
        self.orig_insert(*args)
        self.event_generate('<<Change>>')

    def new_delete(self, *args):
        self.orig_delete(*args)
        self.event_generate('<<Change>>')


def create_scrolled_text(frame, config):
    TEXT_WIDTH = 80
    yscrollbar = tk.Scrollbar(frame)
    yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    #f = tkFont.nametofont('TkFixedFont')
    f = tkFont.Font(family=config.font_family,
                    size=config.font_size)
    # tkFont.families(root) returns list of available font family names
    # this determines the width of the complete interface (yes)
    note_editor = NoteEditor(frame, height=25, width=TEXT_WIDTH,
                                wrap=tk.WORD,
                                font=f, tabs=(4 * f.measure(0), 'left'), tabstyle='wordprocessor',
                                yscrollcommand=yscrollbar.set,
                                undo=True,
                                background=config.background_color)
    # change default font at runtime with:
    note_editor.config(font=f)

    # need expand=1 so that when user resizes window, note_editor widget gets
    # the extra space
    note_editor.pack(fill=tk.BOTH, expand=1)

    #xscrollbar.config(command=note_editor.xview)
    yscrollbar.config(command=note_editor.yview)

    return note_editor
