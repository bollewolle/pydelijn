class AtomicStop:
    def __init__(self, stop_id, line_nr, variante, terminus):
        self.stop_id = stop_id
        self.line_nr = line_nr
        self.variante = variante
        self.terminus = terminus

    def get_stop_id(self):
        return self.stop_id

    def get_line_nr(self):
        return self.line_nr

    def get_destination(self):
        return self.terminus

    def __str__(self):
        return f"{self.stop_id} {self.line_nr} {self.variante} {self.terminus}"


class StopInfo:
    def __init__(self, stop_name):
        self.stop_name = stop_name
        self.lines = []
        self.line_infos = {}

    def add_stop(self, stop_id, line_nr, variante, terminus):
        self.lines.append(AtomicStop(stop_id, line_nr, variante, terminus))

    def add_line_info(self, line_info):
        self.line_infos[line_info.get_line_nr()] = line_info

    def get_line_info(self, line_nr):
        return self.line_infos[line_nr]

    def get_lines(self):
        return self.lines

    def __str__(self):
        return f"{self.stop_name}: {[str(k) for k in self.lines]}: {[str(v) for v in self.line_infos.values()]}"
