class LineInfo:
    def __init__(self, line_nr, line_type, line_color):
        self.line_nr = line_nr
        self.line_type = line_type
        self.line_color = line_color

    def get_line_nr(self):
        return self.line_nr

    def get_line_type(self):
        return self.line_type

    def get_line_color(self):
        return self.line_color

    def __str__(self):
        return f"{self.line_nr}: {self.line_type}: {self.line_color}"
