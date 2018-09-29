class Sink(object):
    def open(self, client):
        pass

    def close(self):
        pass

    def setup(self, fmt):
        pass

    def render(self, data):
        pass

    def pump(self):
        pass
