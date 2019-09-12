class Logger:
    def __init__(self, file_name="log.txt"):
        self.file_name = file_name
        self.file = open(self.file_name,"a")

    def write(self, *contents):
        for c in contents:
            self.file.write(c)
        self.file.write("\n")

    def read(self):
        return self.file.read()

    def __del__(self):
        self.file.close()
